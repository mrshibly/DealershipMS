import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, CheckCircle, XCircle, Download, DollarSign, AlertTriangle, Edit3 } from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import Modal from '../../components/ui/Modal';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const collectionSchema = z.object({
  amount: z.coerce.number().min(0.01, 'Must be greater than 0'),
  payment_method: z.string().min(1, 'Required'),
  reference_no: z.string().optional(),
  notes: z.string().optional(),
  account_id: z.string().optional(),
});

export default function InvoiceDetail() {
  const { id } = useParams();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [isCollectModalOpen, setIsCollectModalOpen] = useState(false);
  const [isVoidModalOpen, setIsVoidModalOpen] = useState(false);

  const { data: invoice, isLoading } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => api.get(`/invoices/${id}`).then(res => res.data.data),
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => api.get('/accounts?per_page=100').then(res => res.data.data),
  });

  const confirmMutation = useMutation({
    mutationFn: () => api.post(`/invoices/${id}/confirm`),
    onSuccess: () => {
      queryClient.invalidateQueries(['invoice', id]);
    },
    onError: (err) => {
      alert(err.response?.data?.detail || t('common.error'));
    }
  });

  const voidMutation = useMutation({
    mutationFn: () => api.post(`/invoices/${id}/void`),
    onSuccess: () => {
      queryClient.invalidateQueries(['invoice', id]);
      setIsVoidModalOpen(false);
    },
    onError: (err) => {
      alert(err.response?.data?.detail || t('common.error'));
      setIsVoidModalOpen(false);
    }
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(collectionSchema),
    defaultValues: {
      amount: 0,
      payment_method: 'CASH',
      account_id: '',
    }
  });

  const collectMutation = useMutation({
    mutationFn: (data) => api.post(`/invoices/${id}/collect`, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['invoice', id]);
      queryClient.invalidateQueries(['accounts']);
      setIsCollectModalOpen(false);
      reset();
    },
    onError: (err) => {
      alert(err.response?.data?.detail || t('common.error'));
    }
  });

  if (isLoading) return <div className="p-8 text-center text-text-muted">{t('common.loading')}...</div>;
  if (!invoice) return <div className="p-8 text-center text-danger">Invoice not found</div>;

  const outstanding = invoice.grand_total - invoice.paid_amount;
  const canConfirm = invoice.status === 'DRAFT';
  const canCollect = ['CONFIRMED', 'PARTIAL'].includes(invoice.status) && outstanding > 0;
  const canVoid = invoice.status === 'DRAFT' || invoice.status === 'CONFIRMED';

  const statusColors = {
    DRAFT: 'badge-info',
    CONFIRMED: 'badge-primary',
    PARTIAL: 'badge-warning',
    PAID: 'badge-success',
    VOID: 'bg-danger/10 text-danger',
  };

  return (
    <div className="max-w-5xl mx-auto pb-12">
      {/* Header Actions */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/invoices')} className="btn-icon">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-text flex items-center gap-3">
              {invoice.invoice_no}
              <span className={`badge ${statusColors[invoice.status]}`}>
                {t(`invoices.status_${invoice.status.toLowerCase()}`)}
              </span>
            </h1>
            <p className="text-text-muted text-sm mt-1">{formatDate(invoice.date)}</p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button
            className="btn-secondary"
            onClick={async () => {
              try {
                const res = await api.get(`/invoices/${id}/pdf`, { responseType: 'blob' });
                const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
                const a = document.createElement('a');
                a.href = url;
                a.download = `invoice-${invoice.invoice_no}.pdf`;
                a.click();
                window.URL.revokeObjectURL(url);
              } catch (e) {
                alert('Failed to download PDF');
              }
            }}
          >
            <Download className="w-4 h-4 mr-2" />
            {t('invoices.download_pdf')}
          </button>
          
          {canVoid && (
            <button className="btn-danger" onClick={() => setIsVoidModalOpen(true)}>
              <XCircle className="w-4 h-4 mr-2" />
              {t('invoices.void')}
            </button>
          )}

          {canConfirm && (
            <>
              <Link to={`/invoices/${id}/edit`} className="btn-secondary">
                <Edit3 className="w-4 h-4 mr-2" />
                {t('common.edit', 'Adjust')}
              </Link>
              <button 
                className="btn-primary" 
                onClick={() => confirmMutation.mutate()}
                disabled={confirmMutation.isPending}
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                {confirmMutation.isPending ? t('common.loading') : t('invoices.confirm')}
              </button>
            </>
          )}

          {canCollect && (
            <button 
              className="btn-success" 
              onClick={() => {
                reset({ amount: outstanding, payment_method: 'CASH' });
                setIsCollectModalOpen(true);
              }}
            >
              <DollarSign className="w-4 h-4 mr-2" />
              {t('invoices.collect')}
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wider">{t('invoices.bill_to')}</h3>
          <p className="font-bold text-lg text-primary">{invoice.dealer?.name || '-'}</p>
          <p className="text-sm text-text-muted">{invoice.dealer?.phone || '-'}</p>
          <p className="text-sm text-text-muted">{invoice.dealer?.address || '-'}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wider">{t('invoices.details')}</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-muted">{t('invoices.dsr')}:</span>
              <span className="font-medium">{invoice.dsr?.name || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">{t('invoices.shop')}:</span>
              <span className="font-medium">{invoice.shop?.name || '-'}</span>
            </div>
          </div>
        </div>
        <div className="card bg-primary/5 border-primary/20">
          <h3 className="text-sm font-semibold text-primary mb-4 uppercase tracking-wider">{t('invoices.summary')}</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-muted">{t('invoices.grand_total')}:</span>
              <span className="font-bold">{formatCurrency(invoice.grand_total)}</span>
            </div>
            <div className="flex justify-between text-success">
              <span>{t('invoices.paid_amount')}:</span>
              <span className="font-bold">{formatCurrency(invoice.paid_amount)}</span>
            </div>
            <div className="flex justify-between text-danger pt-2 border-t border-primary/10 mt-2">
              <span className="font-bold">{t('invoices.outstanding')}:</span>
              <span className="font-bold text-lg">{formatCurrency(outstanding)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="card p-0 overflow-hidden mb-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-background text-text-muted">
              <tr>
                <th className="px-6 py-4">{t('product.name')}</th>
                <th className="px-6 py-4 text-center">{t('product.pcs')}</th>
                <th className="px-6 py-4 text-right">{t('product.sell_price')}</th>
                <th className="px-6 py-4 text-right">{t('product.vat_rate')}</th>
                <th className="px-6 py-4 text-right">{t('invoices.line_total')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {invoice.items.map((item) => (
                <tr key={item.id}>
                  <td className="px-6 py-4">
                    <p className="font-medium text-text">
                      {i18n.language === 'bn' && item.product?.name_bn ? item.product?.name_bn : item.product?.name_en || item.product?.name}
                    </p>
                    {item.is_free_item && <span className="badge badge-success mt-1">{t('invoices.free_item')}</span>}
                  </td>
                  <td className="px-6 py-4 text-center font-medium">{item.total_pieces}</td>
                  <td className="px-6 py-4 text-right">{formatCurrency(item.unit_price)}</td>
                  <td className="px-6 py-4 text-right">{formatCurrency(item.vat_amount)} <span className="text-xs text-text-muted">({item.vat_rate}%)</span></td>
                  <td className="px-6 py-4 text-right font-medium">{formatCurrency(item.line_total)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-background/50 border-t border-border">
              <tr>
                <td colSpan="4" className="px-6 py-3 text-right text-text-muted">{t('invoices.subtotal')}</td>
                <td className="px-6 py-3 text-right font-medium">{formatCurrency(invoice.subtotal)}</td>
              </tr>
              {invoice.discount > 0 && (
                <tr>
                  <td colSpan="4" className="px-6 py-3 text-right text-text-muted">{t('invoices.discount')}</td>
                  <td className="px-6 py-3 text-right font-medium text-danger">-{formatCurrency(invoice.discount)}</td>
                </tr>
              )}
              <tr>
                <td colSpan="4" className="px-6 py-3 text-right text-text-muted">{t('invoices.vat')}</td>
                <td className="px-6 py-3 text-right font-medium">{formatCurrency(invoice.vat_amount)}</td>
              </tr>
              <tr className="border-t border-border">
                <td colSpan="4" className="px-6 py-4 text-right font-bold text-text">{t('invoices.grand_total')}</td>
                <td className="px-6 py-4 text-right font-bold text-primary text-lg">{formatCurrency(invoice.grand_total)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Collection History */}
      {invoice.collections?.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <div className="p-4 border-b border-border bg-background/50">
            <h2 className="font-semibold text-text">{t('invoices.payment_history')}</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-background text-text-muted">
                <tr>
                  <th className="px-6 py-3">{t('invoices.date')}</th>
                  <th className="px-6 py-3">{t('invoices.method')}</th>
                  <th className="px-6 py-3">{t('invoices.reference')}</th>
                  <th className="px-6 py-3 text-right">{t('invoices.amount')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {invoice.collections.map((col) => (
                  <tr key={col.id}>
                    <td className="px-6 py-3">{formatDate(col.collected_at)}</td>
                    <td className="px-6 py-3"><span className="badge badge-info">{col.payment_method}</span></td>
                    <td className="px-6 py-3 text-text-muted">{col.reference_no || '-'}</td>
                    <td className="px-6 py-3 text-right font-medium text-success">{formatCurrency(col.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Collect Modal */}
      <Modal isOpen={isCollectModalOpen} onClose={() => setIsCollectModalOpen(false)} title={t('invoices.collect_payment')}>
        <form onSubmit={handleSubmit((d) => collectMutation.mutate(d))} className="space-y-4">
          <div>
            <label className="label">{t('invoices.amount')}</label>
            <input type="number" step="0.01" max={outstanding} className="input text-lg font-bold text-success" {...register('amount')} />
            {errors.amount && <p className="text-danger text-xs mt-1">{errors.amount.message}</p>}
            <p className="text-xs text-text-muted mt-1">{t('invoices.outstanding')}: {formatCurrency(outstanding)}</p>
          </div>
          <div>
            <label className="label">{t('invoices.method')}</label>
            <select className="input" {...register('payment_method')}>
              <option value="CASH">Cash</option>
              <option value="BKASH">bKash</option>
              <option value="NAGAD">Nagad</option>
              <option value="ROCKET">Rocket</option>
              <option value="BANK_TRANSFER">Bank Transfer</option>
              <option value="CHEQUE">Cheque</option>
            </select>
          </div>
          <div>
            <label className="label">{t('accounts.account', 'Deposit Account')}</label>
            <select className="input" {...register('account_id')}>
              <option value="">{t('common.select', 'Select Account')}</option>
              {accounts?.map(acc => (
                <option key={acc.id} value={acc.id}>
                  {acc.name} ({acc.account_type} - {formatCurrency(acc.balance)})
                </option>
              ))}
            </select>
            {errors.account_id && <p className="text-danger text-xs mt-1">{errors.account_id.message}</p>}
          </div>
          <div>
            <label className="label">{t('invoices.reference')} ({t('common.optional')})</label>
            <input type="text" className="input" {...register('reference_no')} placeholder="TrxID / Cheque No" />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <button type="button" className="btn-secondary" onClick={() => setIsCollectModalOpen(false)}>
              {t('common.cancel')}
            </button>
            <button type="submit" className="btn-success" disabled={collectMutation.isPending}>
              {collectMutation.isPending ? t('common.loading') : t('invoices.collect')}
            </button>
          </div>
        </form>
      </Modal>

      {/* Void Modal */}
      <Modal isOpen={isVoidModalOpen} onClose={() => setIsVoidModalOpen(false)} title={t('invoices.void_title')}>
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 bg-warning/10 text-warning-dark rounded-lg">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="text-sm">
              {t('invoices.void_warning')}
              {invoice.status === 'CONFIRMED' && " This will reverse the stock deduction."}
            </p>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <button type="button" className="btn-secondary" onClick={() => setIsVoidModalOpen(false)}>
              {t('common.cancel')}
            </button>
            <button type="button" className="btn-danger" onClick={() => voidMutation.mutate()} disabled={voidMutation.isPending}>
              {voidMutation.isPending ? t('common.loading') : t('invoices.void_confirm')}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
