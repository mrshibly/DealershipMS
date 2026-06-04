/**
 * Dashboard placeholder page — Sprint 6 will populate this.
 * Shows layout skeleton with sprint status cards.
 */
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, Package, Users, FileText, BarChart2, Settings } from 'lucide-react';

const SPRINT_STATUS = [
  { sprint: 'S0', name: 'Foundation',            status: 'current',  icon: Settings },
  { sprint: 'S1', name: 'Products & Inventory',  status: 'upcoming', icon: Package },
  { sprint: 'S2', name: 'People & Routes',        status: 'upcoming', icon: Users },
  { sprint: 'S3', name: 'Invoices & Collections', status: 'upcoming', icon: FileText },
  { sprint: 'S4', name: 'Accounts & Finance',     status: 'upcoming', icon: BarChart2 },
  { sprint: 'S5', name: 'Reports',                status: 'upcoming', icon: BarChart2 },
  { sprint: 'S6', name: 'Dashboard Charts',       status: 'upcoming', icon: LayoutDashboard },
];

export default function Dashboard() {
  const { t } = useTranslation();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text">{t('dashboard.title')}</h1>
        <p className="text-text-muted text-sm mt-1">
          Sprint 0 — Foundation complete. Dashboard analytics coming in Sprint 6.
        </p>
      </div>

      {/* Metric placeholders */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        {[
          { key: 'today_sales',       color: 'text-primary' },
          { key: 'today_collections', color: 'text-success' },
          { key: 'today_expenses',    color: 'text-warning' },
          { key: 'outstanding_dues',  color: 'text-danger' },
          { key: 'low_stock',         color: 'text-warning' },
          { key: 'daily_balance',     color: 'text-primary' },
        ].map(({ key, color }) => (
          <div key={key} className="card">
            <p className="text-xs text-text-muted mb-1">{t(`dashboard.${key}`)}</p>
            <p className={`text-xl font-bold ${color}`}>—</p>
          </div>
        ))}
      </div>

      {/* Sprint progress */}
      <div className="card">
        <h2 className="font-semibold text-text mb-4">Build Progress</h2>
        <div className="space-y-3">
          {SPRINT_STATUS.map((s) => (
            <div key={s.sprint} className="flex items-center gap-3">
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  s.status === 'done'
                    ? 'bg-success-light'
                    : s.status === 'current'
                    ? 'bg-primary-light'
                    : 'bg-background'
                }`}
              >
                <s.icon
                  className={`w-4 h-4 ${
                    s.status === 'done'
                      ? 'text-success'
                      : s.status === 'current'
                      ? 'text-primary'
                      : 'text-text-muted'
                  }`}
                />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-text">
                    {s.sprint} — {s.name}
                  </span>
                  <span
                    className={`badge ${
                      s.status === 'done'
                        ? 'badge-success'
                        : s.status === 'current'
                        ? 'badge-info'
                        : 'text-text-muted text-xs'
                    }`}
                  >
                    {s.status === 'done' ? 'Done' : s.status === 'current' ? 'In Progress' : 'Upcoming'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
