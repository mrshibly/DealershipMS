import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import { PageHeader } from '../../components/ui/index.jsx';

export default function ExpenseList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [headId, setHeadId] = useState('');
  
  const monthStart = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];
  const [dateFrom, setDateFrom] = useState(monthStart);
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);

  const { data: headsData } = useQuery({
    queryKey: ['expense-heads'],
    queryFn: () => api.get('/expenses/heads').then(res => res.data.data),
  });

  const { data, isLoading } = useQuery({
    queryKey: ['expenses', page, headId, dateFrom, dateTo],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (headId) params.append('head_id', headId);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      
      const res = await api.get(`/expenses?${params.toString()}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/expenses/${id}`),
    onSuccess: () => {
      qc.invalidateQueries(['expenses']);
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: t('common.delete_success'), type: 'success' } }));
    },
    onError: (err) => {
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: err.response?.data?.detail || t('common.error'), type: 'danger' } }));
    }
  });

  const expenses = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const columns = [
    { key: 'date', label: t('common.date'), render: (v) => formatDate(v) },
    { key: 'head_name', label: t('expenses.head_name') },
    { key: 'account_name', label: t('expenses.paid_from') },
    { key: 'amount', label: t('common.amount'), render: (v) => <span className="font-medium text-danger">{formatCurrency(v)}</span> },
    { key: 'description', label: t('expenses.description'), render: (v) => v || '—' },
    { key: 'reference', label: t('expenses.reference'), render: (v) => v || '—' },
    {
      key: 'id',
      label: t('common.actions'),
      render: (id) => (
        <div className="flex gap-1">
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
        title={t('nav.expenses')}
        subtitle={`${total} ${t('nav.expenses')}`}
        action={
          <button onClick={() => navigate('/expenses/new')} className="btn-primary">
            <Plus className="w-4 h-4" /> {t('expenses.record')}
          </button>
        }
      />
      
      <div className="card mb-4 flex flex-wrap gap-4 items-end">
          <div>
            <label className="label">{t('expenses.head_name')}</label>
            <select className="input" value={headId} onChange={e => { setHeadId(e.target.value); setPage(1); }}>
              <option value="">{t('common.all')}</option>
              {(headsData || []).map(h => (
                  <option key={h.id} value={h.id}>{h.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">{t('common.from')}</label>
            <input type="date" className="input" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setPage(1); }} />
          </div>
          <div>
            <label className="label">{t('common.to')}</label>
            <input type="date" className="input" value={dateTo} onChange={e => { setDateTo(e.target.value); setPage(1); }} />
          </div>
      </div>
      
      <div className="card p-0">
        <Table columns={columns} data={expenses} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}
