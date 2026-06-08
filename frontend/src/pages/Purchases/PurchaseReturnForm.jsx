/**
 * PurchaseReturnForm — create a purchase return (draft).
 * Items are validated against current stock levels before saving.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2, Save, ArrowLeft, AlertCircle } from 'lucide-react';
import api from '../../utils/api';
import { formatBDT } from '../../utils/formatters';
import { PageHeader } from '../../components/ui/index.jsx';

const emptyItem = () => ({ product_id: '', qty_carton: 0, qty_pcs: 0, return_price: 0 });

export default function PurchaseReturnForm() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const today = new Date().toISOString().split('T')[0];
  const [form, setForm] = useState({
    supplier_id: '',
    purchase_id: '',
    return_date: today,
    discount: 0,
    notes: '',
  });
  const [items, setItems] = useState([emptyItem()]);
  const [error, setError] = useState('');

  // ------- Data fetching -------
  const { data: suppliers } = useQuery({
    queryKey: ['suppliers-all'],
    queryFn: async () => {
      const r = await api.get('/suppliers?per_page=200');
      return r.data.data;
    },
  });

  const { data: products } = useQuery({
    queryKey: ['products-all'],
    queryFn: async () => {
      const r = await api.get('/products?per_page=500&is_active=true');
      return r.data.data;
    },
  });

  // Load purchases belonging to the selected supplier (for optional reference)
  const { data: supplierPurchases } = useQuery({
    queryKey: ['supplier-purchases', form.supplier_id],
    queryFn: async () => {
      if (!form.supplier_id) return [];
      const r = await api.get(
        `/purchases?supplier_id=${form.supplier_id}&status=RECEIVED&per_page=50`
      );
      return r.data.data || [];
    },
    enabled: !!form.supplier_id,
  });

  const productMap = Object.fromEntries((products || []).map((p) => [p.id, p]));

  // ------- Live totals -------
  const subtotal = items.reduce((sum, item) => {
    const product = productMap[item.product_id];
    if (!product) return sum;
    const pcs =
      Number(item.qty_carton) * product.pcs_per_carton + Number(item.qty_pcs);
    return sum + pcs * Number(item.return_price || 0);
  }, 0);
  const total = Math.max(0, subtotal - Number(form.discount || 0));

  // ------- Handlers -------
  const updateItem = (i, field, value) => {
    setItems((prev) =>
      prev.map((item, idx) => {
        if (idx !== i) return item;
        const updated = { ...item, [field]: value };
        // Auto-fill return_price from buy_price when product changes
        if (field === 'product_id' && productMap[value]) {
          updated.return_price = productMap[value].buy_price;
        }
        return updated;
      })
    );
  };

  const addItem = () => setItems((prev) => [...prev, emptyItem()]);
  const removeItem = (i) => setItems((prev) => prev.filter((_, idx) => idx !== i));

  // ------- Mutation -------
  const mutation = useMutation({
    mutationFn: (payload) => api.post('/purchase-returns', payload),
    onSuccess: () => {
      qc.invalidateQueries(['purchase-returns']);
      window.dispatchEvent(
        new CustomEvent('dms:toast', {
          detail: { message: 'Purchase return saved as DRAFT', type: 'success' },
        })
      );
      navigate('/purchases/returns');
    },
    onError: (e) => {
      setError(
        e.response?.data?.error || e.response?.data?.detail || 'An error occurred'
      );
    },
  });

  const onSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!form.supplier_id) {
      setError('Please select a supplier');
      return;
    }

    const validItems = items.filter(
      (i) =>
        i.product_id &&
        (Number(i.qty_carton) > 0 || Number(i.qty_pcs) > 0) &&
        Number(i.return_price) > 0
    );

    if (!validItems.length) {
      setError('Add at least one product with quantity > 0 and a valid return price');
      return;
    }

    mutation.mutate({
      supplier_id: form.supplier_id,
      purchase_id: form.purchase_id || null,
      return_date: form.return_date,
      discount: Number(form.discount || 0),
      notes: form.notes,
      items: validItems.map((i) => ({
        product_id: i.product_id,
        qty_carton: Number(i.qty_carton || 0),
        qty_pcs: Number(i.qty_pcs || 0),
        return_price: String(i.return_price || 0),
      })),
    });
  };

  return (
    <div>
      <PageHeader
        title="New Purchase Return"
        action={
          <button onClick={() => navigate(-1)} className="btn-secondary">
            <ArrowLeft className="w-4 h-4" />
            {t('common.cancel')}
          </button>
        }
      />

      <form onSubmit={onSubmit}>
        {/* ── Header row ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="card lg:col-span-2 space-y-4">
            <h2 className="font-semibold text-text">Return Information</h2>

            <div className="grid grid-cols-2 gap-3">
              {/* Supplier */}
              <div className="col-span-2">
                <label className="label">{t('nav.suppliers')} *</label>
                <select
                  className="input"
                  value={form.supplier_id}
                  onChange={(e) =>
                    setForm({ ...form, supplier_id: e.target.value, purchase_id: '' })
                  }
                  required
                >
                  <option value="">Select supplier</option>
                  {(suppliers || []).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Reference Purchase (optional) */}
              <div className="col-span-2">
                <label className="label">
                  Reference Purchase Invoice{' '}
                  <span className="text-text-muted text-xs">(optional)</span>
                </label>
                <select
                  className="input"
                  value={form.purchase_id}
                  onChange={(e) => setForm({ ...form, purchase_id: e.target.value })}
                  disabled={!form.supplier_id}
                >
                  <option value="">No reference purchase</option>
                  {(supplierPurchases || []).map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.invoice_no || `PO-${p.id.slice(0, 8)}`} —{' '}
                      {new Date(p.purchase_date).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>

              {/* Return date */}
              <div>
                <label className="label">Return Date *</label>
                <input
                  type="date"
                  className="input"
                  value={form.return_date}
                  onChange={(e) => setForm({ ...form, return_date: e.target.value })}
                  required
                />
              </div>

              {/* Discount */}
              <div>
                <label className="label">{t('purchase.discount')} (৳)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="input"
                  value={form.discount}
                  onChange={(e) => setForm({ ...form, discount: e.target.value })}
                />
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="label">{t('purchase.notes')}</label>
              <textarea
                rows={2}
                className="input resize-none"
                value={form.notes}
                placeholder="Reason for return, batch details, etc."
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </div>
          </div>

          {/* Summary sidebar */}
          <div className="card">
            <h2 className="font-semibold text-text mb-4">{t('purchase.summary')}</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-muted">{t('purchase.subtotal')}</span>
                <span className="font-medium">{formatBDT(subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">{t('purchase.discount')}</span>
                <span className="font-medium text-warning">−{formatBDT(form.discount || 0)}</span>
              </div>
              <div className="flex justify-between border-t border-border pt-2 mt-2">
                <span className="font-semibold text-text">Total Receivable</span>
                <span className="font-bold text-primary text-base">{formatBDT(total)}</span>
              </div>
            </div>

            <div className="mt-6 p-3 bg-warning-light border border-warning rounded-lg">
              <p className="text-xs text-warning font-medium">
                ⚠️ Confirming this return will <strong>reduce stock</strong> for all listed
                products. Ensure quantities are correct before confirming.
              </p>
            </div>
          </div>
        </div>

        {/* ── Line items table ── */}
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-text">{t('purchase.items')} to Return</h2>
            <button type="button" onClick={addItem} className="btn-secondary text-xs">
              <Plus className="w-3.5 h-3.5" />
              {t('purchase.add_item')}
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 pr-3 font-medium text-text-muted">
                    {t('product.name')}
                  </th>
                  <th className="text-left py-2 pr-3 font-medium text-text-muted">
                    {t('product.ctn')}
                  </th>
                  <th className="text-left py-2 pr-3 font-medium text-text-muted">
                    {t('product.pcs')}
                  </th>
                  <th className="text-left py-2 pr-3 font-medium text-text-muted">
                    Return Price (৳)
                  </th>
                  <th className="text-left py-2 font-medium text-text-muted">Line Total</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {items.map((item, i) => {
                  const product = productMap[item.product_id];
                  const pcs =
                    Number(item.qty_carton) * (product?.pcs_per_carton || 1) +
                    Number(item.qty_pcs);
                  const lineTotal = pcs * Number(item.return_price || 0);
                  return (
                    <tr key={i} className="border-b border-border">
                      <td className="py-2 pr-3 min-w-[180px]">
                        <select
                          className="input text-xs"
                          value={item.product_id}
                          onChange={(e) => updateItem(i, 'product_id', e.target.value)}
                          required
                        >
                          <option value="">{t('purchase.select_product')}</option>
                          {(products || []).map((p) => (
                            <option key={p.id} value={p.id}>
                              {i18n.language === 'bn' && p.name_bn ? p.name_bn : p.name_en} (
                              {p.sku})
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="py-2 pr-3">
                        <input
                          type="number"
                          min="0"
                          className="input w-20 text-xs"
                          value={item.qty_carton}
                          onChange={(e) => updateItem(i, 'qty_carton', e.target.value)}
                        />
                      </td>
                      <td className="py-2 pr-3">
                        <input
                          type="number"
                          min="0"
                          className="input w-20 text-xs"
                          value={item.qty_pcs}
                          onChange={(e) => updateItem(i, 'qty_pcs', e.target.value)}
                        />
                      </td>
                      <td className="py-2 pr-3">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          className="input w-28 text-xs"
                          value={item.return_price}
                          onChange={(e) => updateItem(i, 'return_price', e.target.value)}
                        />
                      </td>
                      <td className="py-2 font-medium text-text">{formatBDT(lineTotal)}</td>
                      <td className="py-2">
                        {items.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeItem(i)}
                            className="p-1 hover:text-danger text-text-muted"
                          >
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

        {/* Error banner */}
        {error && (
          <div className="mb-4 p-3 bg-danger-light border border-danger rounded-lg text-sm text-danger flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            {t('common.cancel')}
          </button>
          <button
            id="purchase-return-save-btn"
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary"
          >
            <Save className="w-4 h-4" />
            {mutation.isPending ? t('common.loading') : 'Save as Draft'}
          </button>
        </div>
      </form>
    </div>
  );
}
