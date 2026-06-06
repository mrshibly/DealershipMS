import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { FileText, TrendingUp, BarChart2, Package, Calendar } from 'lucide-react';
import { PageHeader } from '../../components/ui/index.jsx';

export default function ReportDashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const reports = [
    {
      id: 'daybook',
      title: t('reports.daybook'),
      description: t('reports.daybook_desc'),
      icon: <Calendar className="w-6 h-6 text-primary" />,
      path: '/reports/daybook',
    },
    {
      id: 'sales_profit',
      title: t('reports.sales_profit'),
      description: t('reports.sales_profit_desc'),
      icon: <TrendingUp className="w-6 h-6 text-success" />,
      path: '/reports/sales-profit',
    },
    {
      id: 'stock_movement',
      title: t('reports.stock_movement'),
      description: t('reports.stock_movement_desc'),
      icon: <Package className="w-6 h-6 text-warning" />,
      path: '/reports/stock-movement',
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.reports')}
        subtitle={t('reports.subtitle')}
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
        {reports.map(report => (
          <div 
            key={report.id} 
            className="card hover:shadow-lg transition-shadow cursor-pointer border-t-4 border-t-transparent hover:border-t-primary"
            onClick={() => navigate(report.path)}
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-background rounded-xl">
                {report.icon}
              </div>
              <div>
                <h3 className="font-semibold text-text text-lg">{report.title}</h3>
                <p className="text-text-muted text-sm mt-1">{report.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
