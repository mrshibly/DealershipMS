import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Download } from 'lucide-react';
import { PageHeader } from '../../components/ui/index.jsx';
import api from '../../utils/api';
import Table from '../../components/ui/Table';
import { formatCurrency } from '../../utils/formatters';

export default function DaybookReport() {
  const { t } = useTranslation();
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);

  const { data, isLoading } = useQuery({
    queryKey: ['report-daybook', reportDate],
    queryFn: async () => {
      const res = await api.get(`/reports/daybook?report_date=${reportDate}`);
      return res.data.data;
    },
  });

  const handleExport = () => {
    window.open(`${import.meta.env.VITE_API_URL}/api/v1/reports/daybook?report_date=${reportDate}&export=true`, '_blank');
  };

  const summary = data?.summary || {};
  const transactions = data?.transactions || [];

  const columns = [
    { key: 'type', label: t('reports.type') },
    { key: 'reference', label: t('reports.reference'), render: (v) => v || '—' },
    { key: 'account', label: t('reports.account') },
    { key: 'narration', label: t('reports.narration'), render: (v) => v || '—' },
    { key: 'inflow', label: t('reports.inflow'), render: (v) => <span className="text-success font-medium">{v > 0 ? formatCurrency(v) : '-'}</span> },
    { key: 'outflow', label: t('reports.outflow'), render: (v) => <span className="text-danger font-medium">{v > 0 ? formatCurrency(v) : '-'}</span> },
  ];

  return (
    <div>
      <PageHeader
        title={t('reports.daybook')}
        onBack={() => window.history.back()}
        action={
          <button onClick={handleExport} className="btn-secondary">
            <Download className="w-4 h-4" /> {t('reports.export_excel')}
          </button>
        }
      />

      <div className="card mb-6 flex flex-wrap gap-4 items-end">
        <div>
          <label className="label">{t('reports.select_date')}</label>
          <input type="date" className="input" value={reportDate} onChange={e => setReportDate(e.target.value)} />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card bg-background/50 border border-border">
          <p className="text-sm text-text-muted">{t('reports.total_inflow')}</p>
          <p className="text-2xl font-bold text-success mt-1">{formatCurrency(summary.total_inflow || 0)}</p>
        </div>
        <div className="card bg-background/50 border border-border">
          <p className="text-sm text-text-muted">{t('reports.total_outflow')}</p>
          <p className="text-2xl font-bold text-danger mt-1">{formatCurrency(summary.total_outflow || 0)}</p>
        </div>
        <div className="card bg-background/50 border border-border">
          <p className="text-sm text-text-muted">{t('reports.net_cash_flow')}</p>
          <p className={`text-2xl font-bold mt-1 ${summary.net_cash_flow >= 0 ? 'text-success' : 'text-danger'}`}>
            {formatCurrency(summary.net_cash_flow || 0)}
          </p>
        </div>
        <div className="card bg-background/50 border border-border">
          <p className="text-sm text-text-muted">{t('reports.total_sales_booked')}</p>
          <p className="text-2xl font-bold text-primary mt-1">{formatCurrency(summary.total_sales_booked || 0)}</p>
        </div>
      </div>

      <div className="card p-0">
        <Table columns={columns} data={transactions} loading={isLoading} />
      </div>
    </div>
  );
}
