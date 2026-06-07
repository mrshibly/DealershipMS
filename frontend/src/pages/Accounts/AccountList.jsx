import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Plus, Edit, Trash2, Wallet } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import { formatCurrency } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import { Badge, PageHeader } from '../../components/ui/index.jsx';

export default function AccountList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: response, isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      const res = await api.get('/accounts');
      return res.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/accounts/${id}`),
    onSuccess: () => {
      qc.invalidateQueries(['accounts']);
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: t('common.delete_success'), type: 'success' } }));
    },
    onError: (err) => {
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: err.response?.data?.detail || t('common.error'), type: 'danger' } }));
    }
  });

  const accounts = response?.data || [];
  
  const totalBalance = accounts.reduce((sum, acc) => sum + (acc.current_balance || 0), 0);

  const columns = [
    { key: 'name', label: t('accounts.name'), render: (v, acc) => (
        <div className="flex items-center gap-2">
            <Wallet className="w-4 h-4 text-text-muted" />
            <span className="font-medium text-text">{v}</span>
        </div>
    ) },
    { key: 'type', label: t('accounts.type'), render: (v) => t(`accounts.type_${v.toLowerCase()}`) },
    { key: 'account_no', label: t('accounts.account_no'), render: (v) => v || '—' },
    {
      key: 'current_balance',
      label: t('accounts.current_balance'),
      render: (v) => (
          <span className={`font-semibold ${v < 0 ? 'text-danger' : 'text-success'}`}>
              {formatCurrency(v)}
          </span>
      ),
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
          <button onClick={() => navigate(`/accounts/${id}/edit`)} className="p-1.5 rounded hover:bg-primary-light text-text-muted hover:text-primary">
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
        title={t('nav.accounts')}
        subtitle={t('accounts.subtitle')}
        action={
          <div className="flex gap-3 items-center">
             <div className="text-right mr-4">
                 <p className="text-xs text-text-muted">{t('accounts.total_liquidity')}</p>
                 <p className="font-bold text-lg text-primary">{formatCurrency(totalBalance)}</p>
             </div>
             <button onClick={() => navigate('/accounts/contra')} className="btn-secondary">
                 {t('accounts.contra_transfer')}
             </button>
            <button onClick={() => navigate('/accounts/new')} className="btn-primary">
                <Plus className="w-4 h-4" /> {t('accounts.add')}
            </button>
          </div>
        }
      />
      
      <div className="card p-0 mt-6">
        <Table columns={columns} data={accounts} loading={isLoading} />
      </div>
    </div>
  );
}
