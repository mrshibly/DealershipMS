import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Plus, Edit, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import { Badge, PageHeader, SearchInput } from '../../components/ui/index.jsx';

export default function RouteList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['routes', page, search],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (search) params.set('search', search);
      const res = await api.get(`/routes?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/routes/${id}`),
    onSuccess: () => qc.invalidateQueries(['routes']),
  });

  const routesList = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const columns = [
    { key: 'name', label: t('route.name') },
    { key: 'area', label: t('route.area'), render: (v) => v || '—' },
    { key: 'description', label: t('route.description'), render: (v) => v || '—' },
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
          <button onClick={() => navigate(`/routes/${id}/edit`)} className="p-1.5 rounded hover:bg-primary-light text-text-muted hover:text-primary">
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => { if (confirm(t('route.confirm_delete'))) deleteMutation.mutate(id); }}
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
        title={t('nav.routes')}
        subtitle={`${total} ${t('nav.routes')}`}
        action={
          <button onClick={() => navigate('/routes/new')} className="btn-primary">
            <Plus className="w-4 h-4" /> {t('route.add')}
          </button>
        }
      />
      <div className="flex gap-3 mb-4">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder={t('route.search')} />
      </div>
      <div className="card p-0">
        <Table columns={columns} data={routesList} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}
