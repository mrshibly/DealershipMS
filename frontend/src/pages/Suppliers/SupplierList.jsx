/**
 * Supplier List page.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Plus, Edit, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import { formatBDT } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import { Badge, PageHeader, SearchInput } from '../../components/ui/index.jsx';

export default function SupplierList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['suppliers', page, search],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (search) params.set('search', search);
      const res = await api.get(`/suppliers?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/suppliers/${id}`),
    onSuccess: () => {
      qc.invalidateQueries(['suppliers']);
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: t('common.delete_success'), type: 'success' } }));
    },
    onError: (err) => {
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: err.response?.data?.detail || t('common.error'), type: 'danger' } }));
    }
  });

  const suppliers = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const columns = [
    { key: 'name', label: t('supplier.name') },
    { key: 'contact_person', label: t('supplier.contact'), render: (v) => v || '—' },
    { key: 'phone', label: t('common.phone'), render: (v) => v || '—' },
    { key: 'district', label: t('supplier.district'), render: (v) => v || '—' },
    {
      key: 'opening_balance',
      label: t('supplier.balance'),
      render: (v) => formatBDT(v),
    },
    {
      key: 'is_active',
      label: t('common.status'),
      render: (v) => <Badge variant={v ? 'success' : 'muted'}>{v ? t('common.active') : t('common.inactive')}</Badge>,
    },
    {
      key: 'id',
      label: t('common.actions'),
      render: (id) => (
        <div className="flex gap-1">
          <button onClick={() => navigate(`/suppliers/${id}/edit`)} className="p-1.5 rounded hover:bg-primary-light text-text-muted hover:text-primary">
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => { if (window.confirm(t('common.delete_confirm'))) deleteMutation.mutate(id); }}
            className="p-1.5 rounded hover:bg-danger-light text-text-muted hover:text-danger"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.suppliers')}
        subtitle={`${total} ${t('supplier.total')}`}
        action={
          <button onClick={() => navigate('/suppliers/new')} className="btn-primary">
            <Plus className="w-4 h-4" /> {t('supplier.add')}
          </button>
        }
      />
      <div className="flex gap-3 mb-4">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder={t('supplier.search')} />
      </div>
      <div className="card p-0">
        <Table columns={columns} data={suppliers} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}
