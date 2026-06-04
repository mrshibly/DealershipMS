/**
 * Product Create / Edit form.
 * Route: /products/new  |  /products/:id/edit
 */
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Save, ArrowLeft } from 'lucide-react';
import api from '../../utils/api';
import { PageHeader, SearchInput } from '../../components/ui/index.jsx';
import Spinner from '../../components/ui/index.jsx';

const schema = z.object({
  name_en: z.string().min(1, 'English name is required'),
  name_bn: z.string().optional(),
  sku: z.string().optional(),
  category_id: z.string().optional(),
  unit: z.enum(['piece', 'kg', 'litre', 'set', 'box', 'pack']),
  pcs_per_carton: z.coerce.number().int().min(1),
  buy_price: z.coerce.number().min(0),
  sell_price: z.coerce.number().min(0),
  mrp: z.coerce.number().min(0).optional(),
  vat_applicable: z.boolean(),
  vat_rate: z.coerce.number().min(0).max(100),
  low_stock_threshold: z.coerce.number().int().min(0),
  description: z.string().optional(),
});

export default function ProductForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const qc = useQueryClient();

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => { const r = await api.get('/categories'); return r.data.data; },
  });

  const { data: existing, isLoading: loadingExisting } = useQuery({
    queryKey: ['product', id],
    queryFn: async () => { const r = await api.get(`/products/${id}`); return r.data.data; },
    enabled: isEdit,
  });

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      unit: 'piece', pcs_per_carton: 1, vat_applicable: true,
      vat_rate: 15, low_stock_threshold: 0,
    },
  });

  useEffect(() => {
    if (existing) reset({
      ...existing,
      category_id: existing.category_id || '',
      mrp: existing.mrp || '',
    });
  }, [existing, reset]);

  const mutation = useMutation({
    mutationFn: (data) =>
      isEdit ? api.put(`/products/${id}`, data) : api.post('/products', data),
    onSuccess: () => {
      qc.invalidateQueries(['products']);
      navigate('/products');
    },
  });

  const onSubmit = (data) => {
    const payload = { ...data };
    if (!payload.category_id) delete payload.category_id;
    if (!payload.sku) delete payload.sku;
    if (!payload.mrp) delete payload.mrp;
    mutation.mutate(payload);
  };

  if (isEdit && loadingExisting) return <div className="flex justify-center py-20"><Spinner /></div>;

  const vatApplicable = watch('vat_applicable');

  const Field = ({ name, label, children }) => (
    <div className="mb-4">
      <label htmlFor={name} className="label">{label}</label>
      {children}
      {errors[name] && <p className="error-msg">{errors[name]?.message}</p>}
    </div>
  );

  return (
    <div>
      <PageHeader
        title={isEdit ? t('product.edit_product') : t('product.add_product')}
        action={
          <button onClick={() => navigate(-1)} className="btn-secondary">
            <ArrowLeft className="w-4 h-4" /> {t('common.cancel')}
          </button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Basic Info */}
          <div className="card">
            <h2 className="font-semibold text-text mb-4">{t('product.basic_info')}</h2>

            <Field name="name_en" label={t('product.name_en')}>
              <input id="name_en" className={`input ${errors.name_en ? 'input-error' : ''}`} {...register('name_en')} />
            </Field>

            <Field name="name_bn" label={t('product.name_bn')}>
              <input id="name_bn" className="input font-bn" {...register('name_bn')} />
            </Field>

            <Field name="sku" label={`SKU (${t('product.auto_generated')})`}>
              <input id="sku" className="input" placeholder="Auto-generated if blank" {...register('sku')} />
            </Field>

            <Field name="category_id" label={t('product.category')}>
              <select id="category_id" className="input" {...register('category_id')}>
                <option value="">{t('product.no_category')}</option>
                {categories?.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field name="unit" label={t('product.unit')}>
                <select id="unit" className="input" {...register('unit')}>
                  {['piece','kg','litre','set','box','pack'].map(u => (
                    <option key={u} value={u}>{u}</option>
                  ))}
                </select>
              </Field>
              <Field name="pcs_per_carton" label={t('product.pcs_per_carton')}>
                <input id="pcs_per_carton" type="number" min="1" className="input" {...register('pcs_per_carton')} />
              </Field>
            </div>
          </div>

          {/* Pricing */}
          <div className="card">
            <h2 className="font-semibold text-text mb-4">{t('product.pricing')}</h2>

            <div className="grid grid-cols-2 gap-3">
              <Field name="buy_price" label={`${t('product.buy_price')} (৳)`}>
                <input id="buy_price" type="number" step="0.01" min="0" className={`input ${errors.buy_price ? 'input-error' : ''}`} {...register('buy_price')} />
              </Field>
              <Field name="sell_price" label={`${t('product.sell_price')} (৳)`}>
                <input id="sell_price" type="number" step="0.01" min="0" className={`input ${errors.sell_price ? 'input-error' : ''}`} {...register('sell_price')} />
              </Field>
            </div>

            <Field name="mrp" label={`MRP (৳) — ${t('product.optional')}`}>
              <input id="mrp" type="number" step="0.01" min="0" className="input" {...register('mrp')} />
            </Field>

            {/* VAT */}
            <div className="mb-4 p-3 bg-background rounded-lg border border-border">
              <div className="flex items-center gap-2 mb-2">
                <input id="vat_applicable" type="checkbox" className="w-4 h-4 accent-primary" {...register('vat_applicable')} />
                <label htmlFor="vat_applicable" className="text-sm font-medium text-text">{t('product.vat_applicable')}</label>
              </div>
              {vatApplicable && (
                <Field name="vat_rate" label={`${t('product.vat_rate')} (%)`}>
                  <input id="vat_rate" type="number" step="0.01" min="0" max="100" className="input" {...register('vat_rate')} />
                </Field>
              )}
            </div>

            <Field name="low_stock_threshold" label={`${t('product.low_stock_threshold')} (${t('product.pcs')})`}>
              <input id="low_stock_threshold" type="number" min="0" className="input" {...register('low_stock_threshold')} />
            </Field>

            <Field name="description" label={t('product.description')}>
              <textarea id="description" rows={3} className="input resize-none" {...register('description')} />
            </Field>
          </div>
        </div>

        {/* Error */}
        {mutation.isError && (
          <div className="mt-4 p-3 bg-danger-light border border-danger rounded-lg text-sm text-danger">
            {mutation.error?.response?.data?.detail || 'An error occurred'}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            {t('common.cancel')}
          </button>
          <button
            id="product-save-btn"
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary"
          >
            <Save className="w-4 h-4" />
            {mutation.isPending ? t('common.loading') : t('common.save')}
          </button>
        </div>
      </form>
    </div>
  );
}
