import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Plus, Edit, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import { Badge, PageHeader, SearchInput } from '../../components/ui/index.jsx';

export default function DealerList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['dealers', page, search],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (search) params.set('search', search);
      const res = await api.get(`/dealers?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/dealers/${id}`),
    onSuccess: () => qc.invalidateQueries(['dealers']),
  });

  const dealers = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const columns = [
    { key: 'name', label: t('dealer.name') },
    { key: 'owner_name', label: t('dealer.owner'), render: (v) => v || '—' },
    { key: 'phone', label: t('dealer.phone') },
    { key: 'route_name', label: t('dealer.route'), render: (v) => v || '—' },
    {
      key: 'district',
      label: `${t('dealer.district')} / ${t('dealer.upazila')}`,
      render: (_, row) => {
        const parts = [row.district, row.upazila].filter(Boolean);
        return parts.length > 0 ? parts.join(' / ') : '—';
      },
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
          <button onClick={() => navigate(`/dealers/${id}/edit`)} className="p-1.5 rounded hover:bg-primary-light text-text-muted hover:text-primary">
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => { if (confirm(t('dealer.confirm_delete'))) deleteMutation.mutate(id); }}
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
        title={t('nav.dealers')}
        subtitle={`${total} ${t('nav.dealers')}`}
        action={
          <button onClick={() => navigate('/dealers/new')} className="btn-primary">
            <Plus className="w-4 h-4" /> {t('dealer.add')}
          </button>
        }
      />
      <div className="flex gap-3 mb-4">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder={t('dealer.search')} />
      </div>
      <div className="card p-0">
        <Table columns={columns} data={dealers} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}
