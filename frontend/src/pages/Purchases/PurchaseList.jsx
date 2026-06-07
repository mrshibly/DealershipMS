/**
 * Purchase List page.
 */
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

const STATUS_VARIANTS = { DRAFT: 'muted', RECEIVED: 'success', CANCELLED: 'danger' };

export default function PurchaseList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['purchases', page, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (statusFilter) params.set('status', statusFilter);
      const res = await api.get(`/purchases?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const receiveMutation = useMutation({
    mutationFn: (id) => api.post(`/purchases/${id}/receive?paid=0`),
    onSuccess: () => qc.invalidateQueries(['purchases']),
  });

  const cancelMutation = useMutation({
    mutationFn: (id) => api.post(`/purchases/${id}/cancel`),
    onSuccess: () => qc.invalidateQueries(['purchases']),
  });

  const purchases = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const columns = [
    {
      key: 'purchase_date',
      label: t('purchase.date'),
      render: (v) => formatDate(v),
    },
    { key: 'invoice_no', label: t('purchase.invoice_no'), render: (v) => v || '—' },
    { key: 'supplier_name', label: t('nav.suppliers'), render: (v) => v || t('purchase.no_supplier') },
    {
      key: 'total',
      label: t('purchase.total'),
      render: (v) => <span className="font-semibold">{formatBDT(v)}</span>,
    },
    {
      key: 'paid',
      label: t('purchase.paid'),
      render: (v) => formatBDT(v),
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
                onClick={() => { if (window.confirm(t('purchase.confirm_receive'))) receiveMutation.mutate(id); }}
                title={t('purchase.receive')}
                className="p-1.5 rounded hover:bg-success-light text-text-muted hover:text-success"
              >
                <CheckCircle className="w-4 h-4" />
              </button>
              <button
                onClick={() => { if (window.confirm(t('purchase.confirm_cancel'))) cancelMutation.mutate(id); }}
                title={t('purchase.cancel')}
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
        title={t('nav.purchases')}
        subtitle={`${total} ${t('purchase.total')}`}
        action={
          <button onClick={() => navigate('/purchases/new')} className="btn-primary">
            <Plus className="w-4 h-4" /> {t('purchase.add')}
          </button>
        }
      />
      <div className="flex gap-3 mb-4">
        <select
          className="input max-w-[160px]"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">{t('purchase.all_status')}</option>
          <option value="DRAFT">DRAFT</option>
          <option value="RECEIVED">RECEIVED</option>
          <option value="CANCELLED">CANCELLED</option>
        </select>
      </div>
      <div className="card p-0">
        <Table columns={columns} data={purchases} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}
