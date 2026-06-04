/**
 * Purchase Create form — multi-line items with live totals.
 */
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2, Save, ArrowLeft } from 'lucide-react';
import api from '../../utils/api';
import { formatBDT } from '../../utils/formatters';
import { PageHeader } from '../../components/ui/index.jsx';

const emptyItem = () => ({ product_id: '', qty_carton: 0, qty_pcs: 0, buy_price: 0 });

export default function PurchaseForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const today = new Date().toISOString().split('T')[0];
  const [form, setForm] = useState({ supplier_id: '', purchase_date: today, invoice_no: '', discount: 0, notes: '' });
  const [items, setItems] = useState([emptyItem()]);
  const [error, setError] = useState('');

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers-all'],
    queryFn: async () => { const r = await api.get('/suppliers?per_page=200'); return r.data.data; },
  });

  const { data: products } = useQuery({
    queryKey: ['products-all'],
    queryFn: async () => { const r = await api.get('/products?per_page=500&is_active=true'); return r.data.data; },
  });

  const productMap = Object.fromEntries((products || []).map((p) => [p.id, p]));

  // Compute totals
  const subtotal = items.reduce((sum, item) => {
    const product = productMap[item.product_id];
    if (!product) return sum;
    const pcs = (Number(item.qty_carton) * product.pcs_per_carton) + Number(item.qty_pcs);
    return sum + pcs * Number(item.buy_price || product.buy_price);
  }, 0);
  const total = Math.max(0, subtotal - Number(form.discount || 0));

  const updateItem = (i, field, value) => {
    setItems((prev) => prev.map((item, idx) => idx === i ? { ...item, [field]: value } : item));
    // Auto-fill buy_price when product changes
    if (field === 'product_id' && productMap[value]) {
      setItems((prev) => prev.map((item, idx) =>
        idx === i ? { ...item, product_id: value, buy_price: productMap[value].buy_price } : item
      ));
    }
  };

  const mutation = useMutation({
    mutationFn: (payload) => api.post('/purchases', payload),
    onSuccess: () => { qc.invalidateQueries(['purchases']); navigate('/purchases'); },
    onError: (e) => setError(e.response?.data?.detail || 'An error occurred'),
  });

  const onSubmit = (e) => {
    e.preventDefault();
    setError('');
    const validItems = items.filter((i) => i.product_id && (Number(i.qty_carton) > 0 || Number(i.qty_pcs) > 0));
    if (!validItems.length) { setError('Add at least one product with quantity > 0'); return; }
    mutation.mutate({
      ...form,
      supplier_id: form.supplier_id || null,
      discount: Number(form.discount || 0),
      items: validItems.map((i) => ({
        product_id: i.product_id,
        qty_carton: Number(i.qty_carton || 0),
        qty_pcs: Number(i.qty_pcs || 0),
        buy_price: String(i.buy_price || 0),
      })),
    });
  };

  return (
    <div>
      <PageHeader
        title={t('purchase.add')}
        action={<button onClick={() => navigate(-1)} className="btn-secondary"><ArrowLeft className="w-4 h-4" />{t('common.cancel')}</button>}
      />
      <form onSubmit={onSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="card lg:col-span-2">
            <h2 className="font-semibold text-text mb-4">{t('purchase.header_info')}</h2>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <label className="label">{t('nav.suppliers')}</label>
                <select className="input" value={form.supplier_id} onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}>
                  <option value="">{t('purchase.no_supplier')}</option>
                  {(suppliers || []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="label">{t('purchase.date')}</label>
                <input type="date" className="input" value={form.purchase_date} onChange={(e) => setForm({ ...form, purchase_date: e.target.value })} required />
              </div>
              <div>
                <label className="label">{t('purchase.invoice_no')}</label>
                <input className="input" placeholder="Supplier invoice #" value={form.invoice_no} onChange={(e) => setForm({ ...form, invoice_no: e.target.value })} />
              </div>
              <div>
                <label className="label">{t('purchase.discount')} (৳)</label>
                <input type="number" step="0.01" min="0" className="input" value={form.discount} onChange={(e) => setForm({ ...form, discount: e.target.value })} />
              </div>
            </div>
            <div>
              <label className="label">{t('purchase.notes')}</label>
              <textarea rows={2} className="input resize-none" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
          </div>

          {/* Totals sidebar */}
          <div className="card">
            <h2 className="font-semibold text-text mb-4">{t('purchase.summary')}</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-text-muted">{t('purchase.subtotal')}</span><span className="font-medium">{formatBDT(subtotal)}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">{t('purchase.discount')}</span><span className="font-medium text-warning">−{formatBDT(form.discount || 0)}</span></div>
              <div className="flex justify-between border-t border-border pt-2 mt-2">
                <span className="font-semibold text-text">{t('purchase.total')}</span>
                <span className="font-bold text-primary text-base">{formatBDT(total)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Line items */}
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-text">{t('purchase.items')}</h2>
            <button type="button" onClick={() => setItems([...items, emptyItem()])} className="btn-secondary text-xs">
              <Plus className="w-3.5 h-3.5" /> {t('purchase.add_item')}
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 pr-3 font-medium text-text-muted">{t('product.name')}</th>
                  <th className="text-left py-2 pr-3 font-medium text-text-muted">{t('product.ctn')}</th>
                  <th className="text-left py-2 pr-3 font-medium text-text-muted">{t('product.pcs')}</th>
                  <th className="text-left py-2 pr-3 font-medium text-text-muted">{t('purchase.buy_price')} (৳)</th>
                  <th className="text-left py-2 font-medium text-text-muted">{t('purchase.line_total')}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, i) => {
                  const product = productMap[item.product_id];
                  const pcs = (Number(item.qty_carton) * (product?.pcs_per_carton || 1)) + Number(item.qty_pcs);
                  const lineTotal = pcs * Number(item.buy_price || 0);
                  return (
                    <tr key={i} className="border-b border-border">
                      <td className="py-2 pr-3">
                        <select
                          className="input text-xs"
                          value={item.product_id}
                          onChange={(e) => updateItem(i, 'product_id', e.target.value)}
                          required
                        >
                          <option value="">{t('purchase.select_product')}</option>
                          {(products || []).map((p) => (
                            <option key={p.id} value={p.id}>{p.name_en} ({p.sku})</option>
                          ))}
                        </select>
                      </td>
                      <td className="py-2 pr-3">
                        <input type="number" min="0" className="input w-20 text-xs" value={item.qty_carton} onChange={(e) => updateItem(i, 'qty_carton', e.target.value)} />
                      </td>
                      <td className="py-2 pr-3">
                        <input type="number" min="0" className="input w-20 text-xs" value={item.qty_pcs} onChange={(e) => updateItem(i, 'qty_pcs', e.target.value)} />
                      </td>
                      <td className="py-2 pr-3">
                        <input type="number" min="0" step="0.01" className="input w-28 text-xs" value={item.buy_price} onChange={(e) => updateItem(i, 'buy_price', e.target.value)} />
                      </td>
                      <td className="py-2 font-medium text-text">{formatBDT(lineTotal)}</td>
                      <td className="py-2">
                        {items.length > 1 && (
                          <button type="button" onClick={() => setItems(items.filter((_, idx) => idx !== i))} className="p-1 hover:text-danger text-text-muted">
                            <Trash2 className="w-3.5 h-3.5" />
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

        {error && <div className="mb-4 p-3 bg-danger-light border border-danger rounded-lg text-sm text-danger">{error}</div>}

        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">{t('common.cancel')}</button>
          <button id="purchase-save-btn" type="submit" disabled={mutation.isPending} className="btn-primary">
            <Save className="w-4 h-4" />
            {mutation.isPending ? t('common.loading') : t('purchase.save_draft')}
          </button>
        </div>
      </form>
    </div>
  );
}
