import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Plus, CheckCircle, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import { formatBDT, formatDate } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import { Badge, PageHeader } from '../../components/ui/index.jsx';

const STATUS_VARIANTS = { DRAFT: 'muted', CONFIRMED: 'success', VOID: 'danger' };

export default function PurchaseReturnList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  // Fetch returns
  const { data, isLoading } = useQuery({
    queryKey: ['purchase-returns', page, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (statusFilter) params.set('status', statusFilter);
      const res = await api.get(`/purchase-returns?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const confirmMutation = useMutation({
    mutationFn: (id) => api.post(`/purchase-returns/${id}/confirm`),
    onSuccess: () => {
      qc.invalidateQueries(['purchase-returns']);
      qc.invalidateQueries(['products-all']);
      qc.invalidateQueries(['inventory']);
      window.dispatchEvent(
        new CustomEvent('dms:toast', {
          detail: { message: 'Return confirmed. Stock levels updated.', type: 'success' },
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

  const voidMutation = useMutation({
    mutationFn: (id) => api.post(`/purchase-returns/${id}/void`),
    onSuccess: () => {
      qc.invalidateQueries(['purchase-returns']);
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

  const returns = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const columns = [
    {
      key: 'return_date',
      label: t('common.date'),
      render: (v) => formatDate(v),
    },
    { key: 'return_no', label: 'Return No.' },
    { key: 'supplier_name', label: t('nav.suppliers') },
    { key: 'purchase_no', label: t('purchase.invoice_no'), render: (v) => v || '—' },
    {
      key: 'total_receivable',
      label: t('purchase.total'),
      render: (v) => <span className="font-semibold">{formatBDT(v)}</span>,
    },
    {
      key: 'status',
      label: t('common.status'),
      render: (v) => <Badge variant={STATUS_VARIANTS[v] || 'info'}>{v}</Badge>,
    },
    {
      key: 'id',
      label: t('common.actions'),
      render: (id, row) => (
        <div className="flex gap-1">
          {row.status === 'DRAFT' && (
            <>
              <button
                onClick={() => {
                  if (window.confirm('Confirm return? This will decrease product stock.')) {
                    confirmMutation.mutate(id);
                  }
                }}
                title="Confirm & Deduct Stock"
                className="p-1.5 rounded hover:bg-success-light text-text-muted hover:text-success"
              >
                <CheckCircle className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  if (window.confirm(t('common.delete_confirm'))) {
                    voidMutation.mutate(id);
                  }
                }}
                title="Void Return"
                className="p-1.5 rounded hover:bg-danger-light text-text-muted hover:text-danger"
              >
                <XCircle className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.purchase_returns')}
        subtitle={`${total} returns`}
        action={
          <button onClick={() => navigate('/purchases/returns/new')} className="btn-primary">
            <Plus className="w-4 h-4" /> Add Return
          </button>
        }
      />

      <div className="flex gap-3 mb-4">
        <select
          className="input max-w-[160px]"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">{t('purchase.all_status')}</option>
          <option value="DRAFT">DRAFT</option>
          <option value="CONFIRMED">CONFIRMED</option>
          <option value="VOID">VOID</option>
        </select>
      </div>

      <div className="card p-0">
        <Table columns={columns} data={returns} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}
