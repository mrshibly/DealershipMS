import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { 
  TrendingUp, ShoppingCart, Package, DollarSign, AlertCircle, UserMinus, Wallet, Landmark, Calendar, RefreshCw
} from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency } from '../../utils/formatters';

export default function Dashboard() {
  const { t, i18n } = useTranslation();
  
  // Date filter state
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(1); // Default to start of current month
    return d.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState(() => {
    return new Date().toISOString().split('T')[0]; // Default to today
  });

  const [appliedFilters, setAppliedFilters] = useState({ dateFrom, dateTo });

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard-snapshot', appliedFilters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (appliedFilters.dateFrom) params.set('date_from', appliedFilters.dateFrom);
      if (appliedFilters.dateTo) params.set('date_to', appliedFilters.dateTo);
      const res = await api.get(`/dashboard/snapshot?${params}`);
      return res.data.data;
    }
  });

  const handleFilter = (e) => {
    e.preventDefault();
    setAppliedFilters({ dateFrom, dateTo });
  };

  const handleClear = () => {
    const defaultFrom = new Date();
    defaultFrom.setDate(1);
    const defaultFromStr = defaultFrom.toISOString().split('T')[0];
    const defaultToStr = new Date().toISOString().split('T')[0];
    setDateFrom(defaultFromStr);
    setDateTo(defaultToStr);
    setAppliedFilters({ dateFrom: defaultFromStr, dateTo: defaultToStr });
  };

  const kpis = dashboardData?.kpis || {};
  const topSelling = dashboardData?.top_selling || [];
  const stockAlerts = dashboardData?.stock_alerts || [];
  const salesVsTarget = dashboardData?.sales_vs_target || [];

  const StatCard = ({ title, value, icon, gradientClass, textColor = "text-text" }) => (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-border/60 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300">
      <div className="flex justify-between items-start">
        <div className="space-y-3">
          <p className="text-text-muted text-xs font-semibold uppercase tracking-wider">{title}</p>
          <h3 className={`text-2xl font-bold tracking-tight ${textColor}`}>
            {isLoading ? '...' : formatCurrency(value || 0)}
          </h3>
        </div>
        <div className={`p-3.5 rounded-2xl ${gradientClass} shadow-inner`}>
          {icon}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-8 pb-12">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-text tracking-tight">{t('dashboard.title')}</h1>
          <p className="text-text-muted text-sm mt-1">{t('dashboard.subtitle')}</p>
        </div>
        
        {/* Date Filter Bar */}
        <form onSubmit={handleFilter} className="flex flex-wrap items-center gap-3 bg-white p-3.5 rounded-2xl border border-border shadow-sm">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-text-muted uppercase">{t('invoices.date')}</span>
            <input 
              type="date" 
              className="input !py-1.5 !px-3 !w-36 text-sm" 
              value={dateFrom} 
              onChange={(e) => setDateFrom(e.target.value)} 
            />
            <span className="text-text-muted">{t('common.to') || 'to'}</span>
            <input 
              type="date" 
              className="input !py-1.5 !px-3 !w-36 text-sm" 
              value={dateTo} 
              onChange={(e) => setDateTo(e.target.value)} 
            />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary !py-1.5 !px-4 text-sm flex items-center gap-1.5">
              <Calendar className="w-4 h-4" />
              {t('common.filter') || 'Filter'}
            </button>
            <button type="button" onClick={handleClear} className="btn-secondary !py-1.5 !px-4 text-sm flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" />
              {t('common.clear') || 'Clear'}
            </button>
          </div>
        </form>
      </div>

      {/* 8 Stat Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title={t('dashboard.net_sales')} 
          value={kpis.net_sales} 
          icon={<TrendingUp className="w-6 h-6 text-emerald-600" />}
          gradientClass="bg-emerald-50"
          textColor="text-emerald-600"
        />
        <StatCard 
          title={t('dashboard.net_purchase')} 
          value={kpis.net_purchase} 
          icon={<ShoppingCart className="w-6 h-6 text-amber-600" />}
          gradientClass="bg-amber-50"
          textColor="text-amber-600"
        />
        <StatCard 
          title={t('dashboard.current_stock')} 
          value={kpis.current_stock} 
          icon={<Package className="w-6 h-6 text-blue-600" />}
          gradientClass="bg-blue-50"
          textColor="text-blue-600"
        />
        <StatCard 
          title={t('dashboard.profit_loss')} 
          value={kpis.profit_loss} 
          icon={<DollarSign className="w-6 h-6 text-indigo-600" />}
          gradientClass="bg-indigo-50"
          textColor={kpis.profit_loss >= 0 ? "text-indigo-600" : "text-danger"}
        />
        <StatCard 
          title={t('dashboard.dsr_sales_due')} 
          value={kpis.dsr_sales_due} 
          icon={<AlertCircle className="w-6 h-6 text-rose-600" />}
          gradientClass="bg-rose-50"
          textColor="text-rose-600"
        />
        <StatCard 
          title={t('dashboard.supplier_due')} 
          value={kpis.supplier_due} 
          icon={<UserMinus className="w-6 h-6 text-orange-600" />}
          gradientClass="bg-orange-50"
          textColor="text-orange-600"
        />
        <StatCard 
          title={t('dashboard.cash_balance')} 
          value={kpis.cash_balance} 
          icon={<Wallet className="w-6 h-6 text-teal-600" />}
          gradientClass="bg-teal-50"
          textColor="text-teal-600"
        />
        <StatCard 
          title={t('dashboard.bank_balance')} 
          value={kpis.bank_balance} 
          icon={<Landmark className="w-6 h-6 text-cyan-600" />}
          gradientClass="bg-cyan-50"
          textColor="text-cyan-600"
        />
      </div>

      {/* Chart Section */}
      <div className="card p-6 bg-white border border-border/60 rounded-2xl shadow-sm">
        <h3 className="text-lg font-bold text-text mb-6">{t('dashboard.sales_vs_target_title')}</h3>
        <div className="h-[360px] w-full">
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-text-muted">
              {t('common.loading')}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={salesVsTarget} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} tickFormatter={(value) => `৳${value.toLocaleString()}`} />
                <RechartsTooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.05), 0 4px 6px -4px rgb(0 0 0 / 0.05)' }}
                  formatter={(value, name) => [formatCurrency(value), name === 'actual_sales' ? t('dashboard.actual_sales') : t('dashboard.target')]}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                <Bar dataKey="actual_sales" name={t('dashboard.actual_sales')} fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={40} />
                <Bar dataKey="target" name={t('dashboard.target')} fill="#0d9488" radius={[4, 4, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Tables Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Top Selling Products */}
        <div className="card p-0 overflow-hidden bg-white border border-border/60 rounded-2xl shadow-sm">
          <div className="p-5 border-b border-border bg-background/30">
            <h3 className="font-bold text-text text-base">{t('dashboard.top_selling_title')}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-background/50 text-text-muted uppercase text-xs tracking-wider">
                <tr>
                  <th className="px-6 py-4">{t('product.name')}</th>
                  <th className="px-6 py-4">{t('product.sku')}</th>
                  <th className="px-6 py-4">{t('product.brand')}</th>
                  <th className="px-6 py-4">{t('product.category')}</th>
                  <th className="px-6 py-4 text-right">{t('dashboard.net_sales')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {isLoading ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center text-text-muted">{t('common.loading')}</td>
                  </tr>
                ) : topSelling.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center text-text-muted">{t('common.no_data')}</td>
                  </tr>
                ) : (
                  topSelling.map((prod, index) => (
                    <tr key={index} className="hover:bg-background/20 transition-colors">
                      <td className="px-6 py-4">
                        <span className="font-medium text-text">
                          {i18n.language === 'bn' && prod.product_name_bn ? prod.product_name_bn : prod.product_name}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-text-muted">{prod.sku}</td>
                      <td className="px-6 py-4 text-text-muted">{prod.brand || '—'}</td>
                      <td className="px-6 py-4 text-text-muted">{prod.category || '—'}</td>
                      <td className="px-6 py-4 text-right font-semibold text-primary">{formatCurrency(prod.total_sales)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Stock Alert List */}
        <div className="card p-0 overflow-hidden bg-white border border-border/60 rounded-2xl shadow-sm">
          <div className="p-5 border-b border-border bg-background/30">
            <h3 className="font-bold text-text text-base">{t('dashboard.stock_alerts_title')}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-background/50 text-text-muted uppercase text-xs tracking-wider">
                <tr>
                  <th className="px-6 py-4">{t('product.name')}</th>
                  <th className="px-6 py-4">{t('product.sku')}</th>
                  <th className="px-6 py-4">{t('product.brand')}</th>
                  <th className="px-6 py-4">{t('product.category')}</th>
                  <th className="px-6 py-4 text-right">{t('product.stock')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {isLoading ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center text-text-muted">{t('common.loading')}</td>
                  </tr>
                ) : stockAlerts.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center text-text-muted">{t('common.no_data')}</td>
                  </tr>
                ) : (
                  stockAlerts.map((prod, index) => (
                    <tr key={index} className="hover:bg-background/20 transition-colors">
                      <td className="px-6 py-4">
                        <span className="font-medium text-text">
                          {i18n.language === 'bn' && prod.product_name_bn ? prod.product_name_bn : prod.product_name}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-text-muted">{prod.sku}</td>
                      <td className="px-6 py-4 text-text-muted">{prod.brand || '—'}</td>
                      <td className="px-6 py-4 text-text-muted">{prod.category || '—'}</td>
                      <td className="px-6 py-4 text-right">
                        <span className="badge badge-danger font-semibold">{prod.qty} pcs</span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
