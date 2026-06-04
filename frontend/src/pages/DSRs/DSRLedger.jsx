import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, TrendingUp, DollarSign, Clock, Award } from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency, formatDate } from '../../utils/formatters';

function StatCard({ icon: Icon, label, value, color = 'primary', sub }) {
  const colorMap = {
    primary: 'text-primary bg-primary/10',
    success: 'text-success bg-success/10',
    warning: 'text-warning bg-warning/10',
    danger: 'text-danger bg-danger/10',
  };
  return (
    <div className="card flex items-start gap-4">
      <div className={`p-3 rounded-xl ${colorMap[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-text-muted uppercase tracking-wider font-medium">{label}</p>
        <p className="text-xl font-bold text-text mt-0.5">{value}</p>
        {sub && <p className="text-xs text-text-muted mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default function DSRLedger() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const today = new Date().toISOString().split('T')[0];
  const monthStart = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
    .toISOString().split('T')[0];

  const [dateFrom, setDateFrom] = useState(monthStart);
  const [dateTo, setDateTo] = useState(today);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['dsr-ledger', id, dateFrom, dateTo],
    queryFn: () => {
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      return api.get(`/dsrs/${id}/ledger?${params.toString()}`).then(r => r.data.data);
    },
  });

  const statusColors = {
    DRAFT: 'badge-info',
    CONFIRMED: 'badge-primary',
    PARTIAL: 'badge-warning',
    PAID: 'badge-success',
    VOID: 'bg-danger/10 text-danger',
  };

  if (isLoading) return <div className="p-8 text-center text-text-muted">{t('common.loading')}...</div>;
  if (!data) return <div className="p-8 text-center text-danger">DSR not found</div>;

  const { dsr, summary, invoices } = data;

  return (
    <div className="max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/dsrs')} className="btn-icon">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-text">{dsr.name}</h1>
          <p className="text-text-muted text-sm">{dsr.phone} · {t('dsr.ledger_subtitle')}</p>
        </div>
      </div>

      {/* Date Filter */}
      <div className="card mb-6 flex flex-wrap gap-4 items-end">
        <div>
          <label className="label">{t('common.from')}</label>
          <input type="date" className="input" value={dateFrom}
            onChange={e => setDateFrom(e.target.value)} />
        </div>
        <div>
          <label className="label">{t('common.to')}</label>
          <input type="date" className="input" value={dateTo}
            onChange={e => setDateTo(e.target.value)} />
        </div>
        <button className="btn-primary" onClick={() => refetch()}>
          {t('common.filter')}
        </button>
        <button className="btn-secondary" onClick={() => {
          setDateFrom('');
          setDateTo('');
        }}>
          {t('common.clear')}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={TrendingUp}
          label={t('dsr.total_sales')}
          value={formatCurrency(summary.total_sales)}
          sub={`${summary.total_invoices} ${t('nav.invoices')}`}
          color="primary"
        />
        <StatCard
          icon={DollarSign}
          label={t('dsr.total_collected')}
          value={formatCurrency(summary.total_collected)}
          color="success"
        />
        <StatCard
          icon={Clock}
          label={t('dsr.outstanding')}
          value={formatCurrency(summary.total_outstanding)}
          color="warning"
        />
        <StatCard
          icon={Award}
          label={t('dsr.commission_earned')}
          value={formatCurrency(summary.commission_earned)}
          sub={`${summary.commission_rate}% rate`}
          color="primary"
        />
      </div>

      {/* Invoice Ledger Table */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-border bg-background/50">
          <h2 className="font-semibold text-text">{t('dsr.invoice_ledger')}</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-background text-text-muted">
              <tr>
                <th className="px-5 py-3">{t('invoices.date')}</th>
                <th className="px-5 py-3">{t('invoices.invoice_no')}</th>
                <th className="px-5 py-3 text-right">{t('invoices.grand_total')}</th>
                <th className="px-5 py-3 text-right">{t('invoices.paid_amount')}</th>
                <th className="px-5 py-3 text-right">{t('invoices.outstanding')}</th>
                <th className="px-5 py-3 text-right">{t('dsr.running_balance')}</th>
                <th className="px-5 py-3">{t('invoices.status')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-text-muted">
                    {t('common.no_data')}
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-background/50 transition-colors">
                    <td className="px-5 py-3 text-text-muted">{formatDate(inv.date)}</td>
                    <td className="px-5 py-3">
                      <Link
                        to={`/invoices/${inv.id}`}
                        className="font-medium text-primary hover:underline"
                      >
                        {inv.invoice_no}
                      </Link>
                    </td>
                    <td className="px-5 py-3 text-right font-medium">{formatCurrency(inv.grand_total)}</td>
                    <td className="px-5 py-3 text-right text-success">{formatCurrency(inv.paid_amount)}</td>
                    <td className="px-5 py-3 text-right text-danger">{formatCurrency(inv.outstanding)}</td>
                    <td className="px-5 py-3 text-right font-bold text-warning">
                      {formatCurrency(inv.running_balance)}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`badge ${statusColors[inv.status] || 'badge-info'}`}>
                        {t(`invoices.status_${inv.status.toLowerCase()}`)}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {invoices.length > 0 && (
              <tfoot className="bg-background/70 border-t-2 border-border font-semibold">
                <tr>
                  <td colSpan={2} className="px-5 py-3 text-text-muted">{t('common.total')}</td>
                  <td className="px-5 py-3 text-right">{formatCurrency(summary.total_sales)}</td>
                  <td className="px-5 py-3 text-right text-success">{formatCurrency(summary.total_collected)}</td>
                  <td className="px-5 py-3 text-right text-danger">{formatCurrency(summary.total_outstanding)}</td>
                  <td colSpan={2}></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>
    </div>
  );
}
