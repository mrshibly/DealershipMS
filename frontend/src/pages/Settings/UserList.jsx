import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit, Trash2 } from 'lucide-react';
import api from '../../utils/api';
import Table from '../../components/ui/Table';

export default function UserList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users').then((res) => res.data.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: t('common.delete_success'), type: 'success' } }));
    },
    onError: (err) => {
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: err.response?.data?.detail || t('common.error'), type: 'danger' } }));
    }
  });

  const columns = [
    { key: 'name', label: t('common.name'), render: (v) => <span className="font-semibold">{v}</span> },
    { key: 'email', label: t('settings.email') },
    { key: 'role_name', label: t('settings.role_name'), render: (v) => v || <span className="text-text-muted italic">None</span> },
    { key: 'is_active', label: t('common.status'), render: (v) => (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${v ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
        {v ? t('common.active') : t('common.inactive')}
      </span>
    )},
    { key: 'actions', label: t('common.actions'), render: (_, row) => (
      <div className="flex gap-2">
        <button 
          onClick={() => navigate(`/settings/users/${row.id}`)}
          className="text-primary hover:bg-primary/10 p-2 rounded-lg transition-colors"
        >
          <Edit className="w-4 h-4" />
        </button>
        <button 
          onClick={() => {
            if (window.confirm(t('common.delete_confirm'))) {
              deleteMutation.mutate(row.id);
            }
          }}
          className="text-danger hover:bg-danger/10 p-2 rounded-lg transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="card p-0">
      <div className="p-6 flex justify-between items-center border-b border-border">
        <h2 className="text-xl font-bold">{t('settings.users')}</h2>
        <button onClick={() => navigate('/settings/users/new')} className="btn-primary">
          <Plus className="w-4 h-4" /> {t('settings.add_user')}
        </button>
      </div>
      <Table columns={columns} data={users || []} loading={isLoading} />
    </div>
  );
}
