import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit } from 'lucide-react';
import api from '../../utils/api';
import Table from '../../components/ui/Table';

export default function RoleList() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const { data: roles, isLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => api.get('/roles').then((res) => res.data.data),
  });

  const columns = [
    { key: 'name', label: t('settings.role_name'), render: (v) => <span className="font-semibold">{v}</span> },
    { key: 'is_active', label: t('common.status'), render: (v) => (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${v ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
        {v ? t('common.active') : t('common.inactive')}
      </span>
    )},
    { key: 'actions', label: t('common.action'), render: (_, row) => (
      <button 
        onClick={() => navigate(`/settings/roles/${row.id}`)}
        className="text-primary hover:bg-primary/10 p-2 rounded-lg transition-colors"
      >
        <Edit className="w-4 h-4" />
      </button>
    )}
  ];

  return (
    <div className="card p-0">
      <div className="p-6 flex justify-between items-center border-b border-border">
        <h2 className="text-xl font-bold">{t('settings.roles_permissions')}</h2>
        <button onClick={() => navigate('/settings/roles/new')} className="btn-primary">
          <Plus className="w-4 h-4" /> {t('settings.add_role')}
        </button>
      </div>
      <Table columns={columns} data={roles || []} loading={isLoading} />
    </div>
  );
}
