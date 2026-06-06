import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { 
  Banknote, Package, TrendingUp, AlertCircle 
} from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency } from '../../utils/formatters';

export default function Dashboard() {
  const { t } = useTranslation();
  const [analyticsPeriod, setAnalyticsPeriod] = useState('monthly');

  const { data: snapshotData, isLoading: isLoadingSnapshot } = useQuery({
    queryKey: ['dashboard-snapshot'],
    queryFn: () => api.get('/dashboard/snapshot').then(res => res.data.data),
  });

  const { data: analyticsData, isLoading: isLoadingAnalytics } = useQuery({
    queryKey: ['dashboard-analytics', analyticsPeriod],
    queryFn: () => api.get(`/dashboard/analytics?period=${analyticsPeriod}`).then(res => res.data.data),
  });

  const StatCard = ({ title, value, icon, colorClass }) => (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-text-muted text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold mt-2 text-text">
            {isLoadingSnapshot ? '...' : formatCurrency(value || 0)}
          </p>
        </div>
        <div className={`p-3 rounded-xl ${colorClass}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text">{t('dashboard.title')}</h1>
          <p className="text-text-muted text-sm mt-1">{t('dashboard.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title={t('dashboard.today_sales')} 
          value={snapshotData?.today_sales} 
          icon={<TrendingUp className="w-6 h-6 text-primary" />}
          colorClass="bg-primary/10"
        />
        <StatCard 
          title={t('dashboard.today_collections')} 
          value={snapshotData?.today_collections} 
          icon={<Banknote className="w-6 h-6 text-success" />}
          colorClass="bg-success/10"
        />
        <StatCard 
          title={t('dashboard.total_due')} 
          value={snapshotData?.total_due} 
          icon={<AlertCircle className="w-6 h-6 text-danger" />}
          colorClass="bg-danger/10"
        />
        <StatCard 
          title={t('dashboard.total_stock_value')} 
          value={snapshotData?.total_stock_value} 
          icon={<Package className="w-6 h-6 text-warning" />}
          colorClass="bg-warning/10"
        />
      </div>

      <div className="card mt-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-bold text-text">{t('dashboard.sales_vs_expenses')}</h3>
          <select 
            className="input !w-auto" 
            value={analyticsPeriod} 
            onChange={(e) => setAnalyticsPeriod(e.target.value)}
          >
            <option value="monthly">{t('dashboard.last_30_days')}</option>
            <option value="yearly">{t('dashboard.last_12_months')}</option>
          </select>
        </div>
        
        <div className="h-[400px] w-full">
          {isLoadingAnalytics ? (
            <div className="flex items-center justify-center h-full text-text-muted">
              {t('common.loading')}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analyticsData || []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4361ee" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#4361ee" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef476f" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef476f" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} tickFormatter={(value) => `৳${value}`} />
                <RechartsTooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  formatter={(value, name) => [formatCurrency(value), name === 'sales' ? t('dashboard.sales') : t('dashboard.expenses')]}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                <Area type="monotone" dataKey="sales" name="sales" stroke="#4361ee" strokeWidth={3} fillOpacity={1} fill="url(#colorSales)" />
                <Area type="monotone" dataKey="expenses" name="expenses" stroke="#ef476f" strokeWidth={3} fillOpacity={1} fill="url(#colorExpenses)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
