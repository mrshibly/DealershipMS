import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2, Save, Check } from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency } from '../../utils/formatters';

const schema = z.object({
  dealer_id: z.string().min(1, 'Required'),
  dsr_id: z.string().optional(),
  date: z.string().min(1, 'Required'),
  discount: z.coerce.number().min(0).default(0),
  notes: z.string().optional(),
  items: z.array(
    z.object({
      product_id: z.string().min(1, 'Required'),
      qty_carton: z.coerce.number().min(0).default(0),
      qty_pcs: z.coerce.number().min(0).default(0),
      is_free_item: z.boolean().default(false),
      // Read-only for display calcs
      price: z.coerce.number().default(0),
      vat_rate: z.coerce.number().default(0),
      pcs_per_carton: z.coerce.number().default(1),
    })
  ).min(1, 'At least one item is required'),
});

export default function InvoiceForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  // Fetch lookups
  const { data: dealers } = useQuery({ queryKey: ['dealers'], queryFn: () => api.get('/dealers?per_page=100').then(res => res.data.data) });
  const { data: dsrs } = useQuery({ queryKey: ['dsrs'], queryFn: () => api.get('/dsrs?per_page=100').then(res => res.data.data) });
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: () => api.get('/products?per_page=500').then(res => res.data.data) });

  const { register, control, handleSubmit, watch, setValue, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      date: new Date().toISOString().split('T')[0],
      items: [{ product_id: '', qty_carton: 0, qty_pcs: 0, is_free_item: false, price: 0, vat_rate: 0, pcs_per_carton: 1 }],
      discount: 0,
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'items' });

  const watchItems = watch('items');
  const watchDiscount = watch('discount') || 0;

  // Live calculations
  let subtotal = 0;
  let vatTotal = 0;

  watchItems.forEach((item) => {
    if (!item.product_id) return;
    const totalPcs = (Number(item.qty_carton) * Number(item.pcs_per_carton)) + Number(item.qty_pcs);
    const lineSub = item.is_free_item ? 0 : totalPcs * Number(item.price);
    const lineVat = item.is_free_item ? 0 : lineSub * (Number(item.vat_rate) / 100);
    subtotal += lineSub;
    vatTotal += lineVat;
  });

  const grandTotal = subtotal - Number(watchDiscount) + vatTotal;

  const handleProductChange = (index, productId) => {
    const product = products?.find(p => p.id === productId);
    if (product) {
      setValue(`items.${index}.price`, product.price);
      setValue(`items.${index}.vat_rate`, product.vat_applicable ? product.vat_rate : 0);
      setValue(`items.${index}.pcs_per_carton`, product.pcs_per_carton);
    } else {
      setValue(`items.${index}.price`, 0);
      setValue(`items.${index}.vat_rate`, 0);
      setValue(`items.${index}.pcs_per_carton`, 1);
    }
  };

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/invoices', data),
    onSuccess: (res) => {
      navigate(`/invoices/${res.data.data.id}`);
    },
    onError: (err) => {
      setError(err.response?.data?.detail || t('common.error'));
    },
  });

  const onSubmit = (data) => {
    // Check if quantities are > 0
    const hasZeroQty = data.items.some(i => i.qty_carton === 0 && i.qty_pcs === 0);
    if (hasZeroQty) {
      setError('All items must have quantity > 0');
      return;
    }
    
    // Clean up readonly fields before sending
    const payload = {
      dealer_id: data.dealer_id,
      dsr_id: data.dsr_id || null,
      date: data.date,
      discount: data.discount,
      notes: data.notes,
      items: data.items.map(i => ({
        product_id: i.product_id,
        qty_carton: i.qty_carton,
        qty_pcs: i.qty_pcs,
        is_free_item: i.is_free_item,
      })),
    };
    createMutation.mutate(payload);
  };

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text">{t('invoices.create')}</h1>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-danger/10 text-danger rounded-lg text-sm font-medium">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="card grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="label">{t('invoices.dealer')}</label>
            <select className="input" {...register('dealer_id')}>
              <option value="">{t('common.select')}</option>
              {dealers?.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            {errors.dealer_id && <p className="text-danger text-xs mt-1">{errors.dealer_id.message}</p>}
          </div>

          <div>
            <label className="label">{t('invoices.dsr')} ({t('common.optional')})</label>
            <select className="input" {...register('dsr_id')}>
              <option value="">{t('common.select')}</option>
              {dsrs?.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">{t('invoices.date')}</label>
            <input type="date" className="input" {...register('date')} />
            {errors.date && <p className="text-danger text-xs mt-1">{errors.date.message}</p>}
          </div>
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="p-4 border-b border-border bg-background/50 flex justify-between items-center">
            <h2 className="font-semibold text-text">{t('invoices.items')}</h2>
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => append({ product_id: '', qty_carton: 0, qty_pcs: 0, is_free_item: false, price: 0, vat_rate: 0, pcs_per_carton: 1 })}
            >
              <Plus className="w-4 h-4 mr-1" />
              {t('common.add')}
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-background text-text-muted">
                <tr>
                  <th className="px-4 py-3">{t('products.product')}</th>
                  <th className="px-4 py-3 w-24">{t('products.carton')}</th>
                  <th className="px-4 py-3 w-24">{t('products.pcs')}</th>
                  <th className="px-4 py-3 w-20 text-center">{t('invoices.free')}</th>
                  <th className="px-4 py-3 text-right">{t('products.price')}</th>
                  <th className="px-4 py-3 text-right">{t('products.vat')}</th>
                  <th className="px-4 py-3 text-right">{t('invoices.line_total')}</th>
                  <th className="px-4 py-3 w-12"></th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field, index) => {
                  const item = watchItems[index];
                  const totalPcs = (Number(item.qty_carton) * Number(item.pcs_per_carton)) + Number(item.qty_pcs);
                  const lineSub = item.is_free_item ? 0 : totalPcs * Number(item.price);
                  const lineVat = item.is_free_item ? 0 : lineSub * (Number(item.vat_rate) / 100);
                  const lineTotal = lineSub + lineVat;

                  return (
                    <tr key={field.id} className="border-b border-border last:border-0">
                      <td className="px-4 py-3">
                        <select
                          className="input"
                          {...register(`items.${index}.product_id`)}
                          onChange={(e) => {
                            register(`items.${index}.product_id`).onChange(e);
                            handleProductChange(index, e.target.value);
                          }}
                        >
                          <option value="">{t('common.select')}</option>
                          {products?.map(p => (
                            <option key={p.id} value={p.id}>{p.name} ({p.pcs_per_carton} pcs/ctn)</option>
                          ))}
                        </select>
                        {errors.items?.[index]?.product_id && <p className="text-danger text-xs mt-1">{errors.items[index].product_id.message}</p>}
                      </td>
                      <td className="px-4 py-3">
                        <input type="number" min="0" className="input text-center" {...register(`items.${index}.qty_carton`)} />
                      </td>
                      <td className="px-4 py-3">
                        <input type="number" min="0" className="input text-center" {...register(`items.${index}.qty_pcs`)} />
                      </td>
                      <td className="px-4 py-3 text-center">
                        <input type="checkbox" className="w-4 h-4 text-primary rounded border-border" {...register(`items.${index}.is_free_item`)} />
                      </td>
                      <td className="px-4 py-3 text-right text-text-muted">
                        {formatCurrency(item.price)}
                      </td>
                      <td className="px-4 py-3 text-right text-text-muted">
                        {item.vat_rate}%
                      </td>
                      <td className="px-4 py-3 text-right font-medium">
                        {formatCurrency(lineTotal)}
                      </td>
                      <td className="px-4 py-3">
                        {fields.length > 1 && (
                          <button type="button" className="text-danger hover:bg-danger/10 p-1 rounded" onClick={() => remove(index)}>
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="flex flex-col md:flex-row justify-between gap-8">
            <div className="flex-1">
              <label className="label">{t('invoices.notes')}</label>
              <textarea className="input" rows="3" {...register('notes')} placeholder={t('common.optional')}></textarea>
            </div>
            
            <div className="w-full md:w-80 space-y-3 bg-background/50 p-4 rounded-lg border border-border">
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">{t('invoices.subtotal')}</span>
                <span className="font-medium">{formatCurrency(subtotal)}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-text-muted">{t('invoices.discount')}</span>
                <input type="number" step="0.01" min="0" className="input w-24 text-right h-8" {...register('discount')} />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">{t('invoices.vat')}</span>
                <span className="font-medium">{formatCurrency(vatTotal)}</span>
              </div>
              <div className="border-t border-border pt-3 mt-3 flex justify-between">
                <span className="font-bold text-text">{t('invoices.grand_total')}</span>
                <span className="font-bold text-primary text-lg">{formatCurrency(grandTotal)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-4">
          <button type="button" className="btn-secondary" onClick={() => navigate(-1)} disabled={createMutation.isPending}>
            {t('common.cancel')}
          </button>
          <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? t('common.loading') : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {t('invoices.save_draft')}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
