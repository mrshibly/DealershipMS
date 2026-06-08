import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Plus, X, Trash2, Calendar, DollarSign, FileText } from 'lucide-react';
import api from '../../utils/api';
import { formatBDT, formatDate } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import { PageHeader } from '../../components/ui/index.jsx';

export default function SupplierPaymentList() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [supplierId, setSupplierId] = useState('');
  const [showModal, setShowModal] = useState(false);

  // Form state
  const [form, setForm] = useState({
    supplier_id: '',
    account_id: '',
    amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    description: '',
  });
  const [error, setError] = useState('');

  // Fetch data
  const { data: suppliers } = useQuery({
    queryKey: ['suppliers-all'],
    queryFn: async () => {
      const res = await api.get('/suppliers?per_page=200');
      return res.data.data;
    },
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts-active'],
    queryFn: async () => {
      const res = await api.get('/accounts?is_active=true');
      return res.data.data;  // SuccessResponse wrapper → data field is the array
    },
  });

  const { data: paymentsData, isLoading } = useQuery({
    queryKey: ['supplier-payments', page, supplierId],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (supplierId) params.append('supplier_id', supplierId);
      const res = await api.get(`/supplier-payments?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (payload) => api.post('/supplier-payments', payload),
    onSuccess: () => {
      qc.invalidateQueries(['supplier-payments']);
      qc.invalidateQueries(['accounts-active']);
      setShowModal(false);
      setForm({
        supplier_id: '',
        account_id: '',
        amount: '',
        payment_date: new Date().toISOString().split('T')[0],
        description: '',
      });
      window.dispatchEvent(
        new CustomEvent('dms:toast', {
          detail: { message: t('common.save_success'), type: 'success' },
        })
      );
    },
    onError: (err) => {
      setError(err.response?.data?.error || err.response?.data?.detail || t('common.error'));
    },
  });

  const voidMutation = useMutation({
    mutationFn: (id) => api.post(`/supplier-payments/${id}/void`),
    onSuccess: () => {
      qc.invalidateQueries(['supplier-payments']);
      qc.invalidateQueries(['accounts-active']);
      window.dispatchEvent(
        new CustomEvent('dms:toast', {
          detail: { message: t('common.delete_success'), type: 'success' },
        })
      );
    },
    onError: (err) => {
      window.dispatchEvent(
        new CustomEvent('dms:toast', {
          detail: {
            message: err.response?.data?.error || err.response?.data?.detail || t('common.error'),
            type: 'danger',
          },
        })
      );
    },
  });

  const payments = paymentsData?.data || [];
  const total = paymentsData?.total || 0;
  const pages = paymentsData?.pages || 0;

  const handleCreate = (e) => {
    e.preventDefault();
    setError('');
    if (!form.supplier_id) return setError('Supplier is required');
    if (!form.account_id) return setError('Account is required');
    if (!form.amount || Number(form.amount) <= 0) return setError('Amount must be greater than 0');

    createMutation.mutate({
      ...form,
      amount: String(form.amount),
    });
  };

  const columns = [
    {
      key: 'payment_date',
      label: t('common.date'),
      render: (v) => formatDate(v),
    },
    {
      key: 'supplier_name',
      label: t('nav.suppliers'),
    },
    {
      key: 'amount',
      label: t('common.amount'),
      render: (v) => <span className="font-semibold text-danger">{formatBDT(v)}</span>,
    },
    {
      key: 'account_name',
      label: t('expenses.paid_from'),
    },
    {
      key: 'description',
      label: t('purchase.notes'),
      render: (v) => v || '—',
    },
    {
      key: 'id',
      label: t('common.actions'),
      render: (id, row) => (
        <div className="flex gap-1">
          {!row.is_deleted && (
            <button
              onClick={() => {
                if (window.confirm(t('common.delete_confirm'))) {
                  voidMutation.mutate(id);
                }
              }}
              title="Void Payment"
              className="p-1.5 rounded hover:bg-danger-light text-text-muted hover:text-danger"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.supplier_payments')}
        subtitle={`${total} Payments`}
        action={
          <button onClick={() => setShowModal(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> Record Payment
          </button>
        }
      />

      <div className="card mb-4 flex gap-4 items-end">
        <div>
          <label className="label">{t('nav.suppliers')}</label>
          <select
            className="input max-w-[200px]"
            value={supplierId}
            onChange={(e) => {
              setSupplierId(e.target.value);
              setPage(1);
            }}
          >
            <option value="">{t('common.all')}</option>
            {(suppliers || []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="card p-0">
        <Table columns={columns} data={payments} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="card w-full max-w-md p-6 relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-text-muted hover:text-text"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-bold text-text mb-4">Record Supplier Payment</h3>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="label">Select Supplier *</label>
                <select
                  className="input"
                  value={form.supplier_id}
                  onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}
                  required
                >
                  <option value="">Select Supplier</option>
                  {(suppliers || []).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} (Due: ৳{s.balance || '0.00'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Payment Account *</label>
                <select
                  className="input"
                  value={form.account_id}
                  onChange={(e) => setForm({ ...form, account_id: e.target.value })}
                  required
                >
                  <option value="">Select Cash/Bank Account</option>
                  {(accounts || []).map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name} (Bal: ৳{Number(acc.current_balance || 0).toFixed(2)})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Amount (৳) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    className="input"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label">Payment Date *</label>
                  <input
                    type="date"
                    className="input"
                    value={form.payment_date}
                    onChange={(e) => setForm({ ...form, payment_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Description / Remarks</label>
                <textarea
                  className="input resize-none"
                  rows={2}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Payment details, cheque number, etc."
                />
              </div>

              {error && (
                <div className="p-3 bg-danger-light border border-danger rounded text-sm text-danger">
                  {error}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn-secondary text-sm"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="btn-primary text-sm"
                >
                  {createMutation.isPending ? t('common.loading') : 'Save Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
