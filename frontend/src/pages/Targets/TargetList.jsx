import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Plus, Target as TargetIcon } from 'lucide-react';
import api from '../../utils/api';
import Table from '../../components/ui/Table';
import { PageHeader } from '../../components/ui/index.jsx';

export default function TargetList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7) + '-01');

  const { data: targets, isLoading } = useQuery({
    queryKey: ['targets', month],
    queryFn: () => api.get(`/targets?month=${month}`).then((res) => res.data.data),
  });

  const columns = [
    { key: 'dsr_name', label: t('settings.role_name'), render: (v) => <span className="font-semibold">{v}</span> }, // reusing a generic name label or adding new one
    { key: 'target_amount', label: t('reports.sales'), render: (v) => `${Number(v).toFixed(2)} ৳` },
    { key: 'achieved_amount', label: t('common.amount'), render: (v) => `${Number(v).toFixed(2)} ৳` },
    { key: 'progress', label: t('common.status'), render: (_, row) => {
        const pct = row.target_amount > 0 ? (row.achieved_amount / row.target_amount) * 100 : 0;
        const color = pct >= 100 ? 'bg-success' : pct >= 50 ? 'bg-warning' : 'bg-danger';
        return (
            <div className="flex items-center gap-2">
                <div className="w-full bg-background rounded-full h-2 max-w-[100px]">
                    <div className={`${color} h-2 rounded-full`} style={{ width: `${Math.min(pct, 100)}%` }}></div>
                </div>
                <span className="text-xs font-medium">{pct.toFixed(1)}%</span>
            </div>
        );
    }}
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.targets')}
        action={
          <button onClick={() => navigate('/targets/new')} className="btn-primary">
            <Plus className="w-4 h-4" /> {t('common.add_new')}
          </button>
        }
      />
      <div className="card p-0 mt-6">
        <div className="p-4 border-b border-border flex justify-between items-center">
            <div className="flex items-center gap-2 text-text-muted">
                <TargetIcon className="w-5 h-5" />
                <span className="font-medium">{t('targets.title', 'Monthly Targets')}</span>
            </div>
            <input 
                type="month" 
                value={month.slice(0, 7)}
                onChange={(e) => setMonth(e.target.value + '-01')}
                className="input max-w-[200px]"
            />
        </div>
        <Table columns={columns} data={targets || []} loading={isLoading} />
      </div>
    </div>
  );
}
