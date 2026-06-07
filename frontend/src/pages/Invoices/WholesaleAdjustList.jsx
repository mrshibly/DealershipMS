import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Edit3, Check, Eye, Trash2 } from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';

export default function WholesaleAdjustList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  // Fetch only DRAFT invoices
  const { data, isLoading } = useQuery({
    queryKey: ['invoices-draft', page],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 15, status: 'DRAFT' });
      const res = await api.get(`/invoices?${params.toString()}`);
      return res.data;
    },
  });

  // Confirm Invoice Mutation
  const confirmMutation = useMutation({
    mutationFn: async (id) => {
      await api.post(`/invoices/${id}/confirm`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices-draft'] });
      alert(t('invoices.confirm_success', 'Invoice confirmed successfully'));
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'Failed to confirm invoice');
    },
  });

  // Void Invoice Mutation
  const voidMutation = useMutation({
    mutationFn: async (id) => {
      await api.post(`/invoices/${id}/void`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices-draft'] });
      alert(t('invoices.void_success', 'Invoice voided successfully'));
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'Failed to void invoice');
    },
  });

  const columns = [
    {
      key: 'invoice_no',
      label: t('invoices.invoice_no', 'Invoice No'),
      render: (val, row) => (
        <Link to={`/invoices/${row.id}`} className="text-primary font-medium hover:underline">
          {val}
        </Link>
      ),
    },
    {
      key: 'date',
      label: t('invoices.date', 'Date'),
      render: (val) => formatDate(val),
    },
    {
      key: 'dealer_name',
      label: t('invoices.dealer', 'Dealer'),
      render: (val) => val || '-',
    },
    {
      key: 'dsr_name',
      label: t('invoices.dsr', 'DSR'),
      render: (val) => val || '-',
    },
    {
      key: 'route_name',
      label: t('routes.route', 'Route'),
      render: (val) => val || '-',
    },
    {
      key: 'grand_total',
      label: t('invoices.grand_total', 'Grand Total'),
      render: (val) => formatCurrency(val),
      className: 'text-right',
    },
    {
      key: 'id',
      label: t('common.actions', 'Actions'),
      render: (_, row) => (
        <div className="flex justify-end gap-2">
          <Link
            to={`/invoices/${row.id}`}
            className="btn-icon"
            title={t('common.view', 'View')}
          >
            <Eye className="w-4 h-4 text-text-muted hover:text-primary transition-colors" />
          </Link>
          <Link
            to={`/invoices/${row.id}/edit`}
            className="btn-icon"
            title={t('common.edit', 'Adjust')}
          >
            <Edit3 className="w-4 h-4 text-text-muted hover:text-warning transition-colors" />
          </Link>
          <button
            onClick={() => {
              if (window.confirm(t('invoices.confirm_warning', 'Are you sure you want to confirm this invoice? This will deduct product stock.'))) {
                confirmMutation.mutate(row.id);
              }
            }}
            className="btn-icon"
            title={t('invoices.confirm', 'Confirm')}
          >
            <Check className="w-4 h-4 text-text-muted hover:text-success transition-colors" />
          </button>
          <button
            onClick={() => {
              if (window.confirm(t('invoices.void_warning', 'Are you sure you want to void this invoice?'))) {
                voidMutation.mutate(row.id);
              }
            }}
            className="btn-icon"
            title={t('invoices.void', 'Void')}
          >
            <Trash2 className="w-4 h-4 text-text-muted hover:text-danger transition-colors" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text">{t('nav.wholesale_adjust_list', 'Wholesale Adjust List')}</h1>
          <p className="text-text-muted text-sm mt-1">
            {t('invoices.adjust_list_subtitle', 'Review, edit, or confirm draft invoices before posting them to the ledger')}
          </p>
        </div>
      </div>

      <div className="card p-0 overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200">
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
