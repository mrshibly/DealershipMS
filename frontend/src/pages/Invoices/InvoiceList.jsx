import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Plus, Eye, CheckCircle, XCircle } from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';

export default function InvoiceList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', page, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 15 });
      if (statusFilter) params.append('status', statusFilter);
      const res = await api.get(`/invoices?${params.toString()}`);
      return res.data;
    },
  });

  const columns = [
    {
      key: 'invoice_no',
      label: t('invoices.invoice_no'),
      render: (val, row) => (
        <Link to={`/invoices/${row.id}`} className="text-primary font-medium hover:underline">
          {val}
        </Link>
      ),
    },
    {
      key: 'date',
      label: t('invoices.date'),
      render: (val) => formatDate(val),
    },
    {
      key: 'grand_total',
      label: t('invoices.grand_total'),
      render: (val) => formatCurrency(val),
      className: 'text-right',
    },
    {
      key: 'paid_amount',
      label: t('invoices.paid_amount'),
      render: (val) => formatCurrency(val),
      className: 'text-right',
    },
    {
      key: 'status',
      label: t('invoices.status'),
      render: (val) => {
        const colors = {
          DRAFT: 'badge-info',
          CONFIRMED: 'badge-primary',
          PARTIAL: 'badge-warning',
          PAID: 'badge-success',
          VOID: 'bg-danger/10 text-danger',
        };
        return <span className={`badge ${colors[val] || 'badge-info'}`}>{t(`invoices.status_${val.toLowerCase()}`)}</span>;
      },
    },
    {
      key: 'id',
      label: t('common.actions'),
      render: (_, row) => (
        <div className="flex justify-end gap-2">
          <Link to={`/invoices/${row.id}`} className="btn-icon">
            <Eye className="w-4 h-4 text-text-muted" />
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text">{t('nav.invoices')}</h1>
          <p className="text-text-muted text-sm mt-1">{t('invoices.list_subtitle')}</p>
        </div>
        <Link to="/invoices/new" className="btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          {t('invoices.create')}
        </Link>
      </div>

      <div className="card mb-6">
        <div className="flex gap-4">
          <div className="w-64">
            <label className="label">{t('invoices.filter_status')}</label>
            <select
              className="input"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">{t('common.all')}</option>
              <option value="DRAFT">{t('invoices.status_draft')}</option>
              <option value="CONFIRMED">{t('invoices.status_confirmed')}</option>
              <option value="PARTIAL">{t('invoices.status_partial')}</option>
              <option value="PAID">{t('invoices.status_paid')}</option>
              <option value="VOID">{t('invoices.status_void')}</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <Table columns={columns} data={data?.data || []} loading={isLoading} />
        {data?.pages > 1 && (
          <div className="p-4 border-t border-border">
            <Pagination
              page={page}
              pages={data.pages}
              total={data.total}
              onPageChange={setPage}
            />
          </div>
        )}
      </div>
    </div>
  );
}
