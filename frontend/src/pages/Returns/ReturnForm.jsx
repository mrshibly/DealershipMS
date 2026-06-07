import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useForm, useFieldArray } from 'react-hook-form';
import api from '../../utils/api';
import { Save, ArrowLeft, Search } from 'lucide-react';

export default function ReturnForm() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [invoiceSearch, setInvoiceSearch] = useState('');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Fetch invoices
  const { data: invoices } = useQuery({
    queryKey: ['invoices-return-lookup', invoiceSearch],
    queryFn: () => api.get(`/invoices?per_page=100&status=CONFIRMED`).then(res => res.data.data.data),
  });

  const selectedInvoice = invoices?.find(i => i.id === selectedInvoiceId);

  // Setup form
  const { register, control, handleSubmit, reset } = useForm({
    defaultValues: {
      return_date: new Date().toISOString().split('T')[0],
      items: [],
    }
  });

  const { fields, replace } = useFieldArray({ control, name: 'items' });

  // When selected invoice changes, populate all items as rows in the form
  useEffect(() => {
    if (selectedInvoice && selectedInvoice.items) {
      const formItems = selectedInvoice.items.map(item => ({
        product_id: item.product_id,
        product_name: i18n.language === 'bn' && item.product?.name_bn ? item.product.name_bn : item.product?.name_en || 'Product',
        billed_qty: item.total_pieces,
        qty_returned: 0,
        reason: '',
        should_return: false,
      }));
      replace(formItems);
    } else {
      replace([]);
    }
  }, [selectedInvoice, replace, i18n.language]);

  const onSubmit = async (data) => {
    setError('');
    const itemsToReturn = data.items.filter(item => item.should_return && item.qty_returned > 0);

    if (itemsToReturn.length === 0) {
      setError(t('returns.no_items_selected', 'Please select at least one item to return and specify quantity.'));
      return;
    }

    // Validate quantities
    const invalidItem = itemsToReturn.find(item => item.qty_returned > item.billed_qty);
    if (invalidItem) {
      setError(t('returns.qty_exceeded', `Return quantity for ${invalidItem.product_name} cannot exceed billed quantity of ${invalidItem.billed_qty}.`));
      return;
    }

    setIsSaving(true);
    try {
      // Create returns sequentially or in parallel
      const promises = itemsToReturn.map(item => 
        api.post('/returns', {
          invoice_id: selectedInvoiceId,
          product_id: item.product_id,
          qty_returned: parseInt(item.qty_returned, 10),
          reason: item.reason || data.general_reason || 'Bulk Return',
          return_date: data.return_date,
        })
      );
      await Promise.all(promises);

      queryClient.invalidateQueries(['returns']);
      alert(t('returns.success_msg', 'Return(s) processed successfully and stock adjusted.'));
      navigate('/returns');
    } catch (err) {
      setError(err.response?.data?.detail || t('returns.error_msg', 'Failed to process bulk return. Please check quantities and try again.'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto pb-12">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/returns')} className="btn-icon">
          <ArrowLeft className="w-5 h-5 text-text-muted" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-text">{t('returns.bulk_return', 'Bulk Return Log')}</h1>
          <p className="text-text-muted text-sm mt-1">{t('returns.subtitle', 'Log returned products and restore inventory stock')}</p>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-danger/10 text-danger rounded-lg text-sm font-medium">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Invoice Selection Card */}
        <div className="card shadow-sm">
          <label className="label">{t('invoices.select_invoice', 'Select Confirmed Invoice')}</label>
          <div className="relative mt-1">
            <select
              className="input font-medium"
              value={selectedInvoiceId}
              onChange={(e) => setSelectedInvoiceId(e.target.value)}
            >
              <option value="">{t('common.select', 'Select Invoice...')}</option>
              {invoices?.map(inv => (
                <option key={inv.id} value={inv.id}>
                  {inv.invoice_no} — {inv.dealer_name || 'Dealer'} ({formatDate(inv.date)})
                </option>
              ))}
            </select>
          </div>

          {selectedInvoice && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 p-4 bg-background/50 rounded-lg text-sm border border-border">
              <div>
                <span className="text-text-muted">{t('invoices.dealer', 'Dealer')}:</span>
                <span className="font-semibold text-text ml-2">{selectedInvoice.dealer_name || '-'}</span>
              </div>
              <div>
                <span className="text-text-muted">{t('invoices.dsr', 'DSR')}:</span>
                <span className="font-semibold text-text ml-2">{selectedInvoice.dsr_name || '-'}</span>
              </div>
            </div>
          )}
        </div>

        {/* Return Details Card */}
        {selectedInvoice && fields.length > 0 && (
          <div className="card p-0 overflow-hidden shadow-sm">
            <div className="p-4 border-b border-border bg-background/50">
              <h2 className="font-semibold text-text">{t('returns.items_to_return', 'Billed Items')}</h2>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-background text-text-muted">
                  <tr>
                    <th className="px-4 py-3 w-12 text-center"></th>
                    <th className="px-4 py-3">{t('product.name', 'Product Name')}</th>
                    <th className="px-4 py-3 w-32 text-center">{t('returns.billed_qty', 'Billed Qty (Pcs)')}</th>
                    <th className="px-4 py-3 w-40 text-center">{t('returns.return_qty', 'Qty to Return (Pcs)')}</th>
                    <th className="px-4 py-3">{t('returns.reason', 'Specific Reason / Notes')}</th>
                  </tr>
                </thead>
                <tbody>
                  {fields.map((field, index) => {
                    return (
                      <tr key={field.id} className="border-b border-border last:border-0 hover:bg-background/20 transition-colors">
                        <td className="px-4 py-3 text-center">
                          <input
                            type="checkbox"
                            className="w-4 h-4 text-primary rounded border-border cursor-pointer"
                            {...register(`items.${index}.should_return`)}
                          />
                        </td>
                        <td className="px-4 py-3 font-medium text-text">
                          {field.product_name}
                        </td>
                        <td className="px-4 py-3 text-center font-mono text-text-muted">
                          {field.billed_qty}
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            min="0"
                            max={field.billed_qty}
                            className="input text-center font-mono"
                            {...register(`items.${index}.qty_returned`)}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            className="input"
                            placeholder={t('returns.reason_placeholder', 'Damaged, expired, etc.')}
                            {...register(`items.${index}.reason`)}
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Global Settings */}
        {selectedInvoice && (
          <div className="card shadow-sm grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="label">{t('returns.date', 'Return Date')}</label>
              <input type="date" className="input mt-1" {...register('return_date')} />
            </div>
            <div>
              <label className="label">{t('returns.general_reason', 'General Reason (Optional)')}</label>
              <input
                type="text"
                className="input mt-1"
                {...register('general_reason')}
                placeholder={t('returns.general_placeholder', 'Default note for all items')}
              />
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <button type="button" className="btn-secondary" onClick={() => navigate('/returns')} disabled={isSaving}>
            {t('common.cancel')}
          </button>
          {selectedInvoice && (
            <button type="submit" className="btn-primary" disabled={isSaving}>
              <Save className="w-4 h-4 mr-2" />
              {isSaving ? t('common.saving') : t('common.save')}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
