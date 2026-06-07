import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Download } from 'lucide-react';
import { PageHeader } from '../../components/ui/index.jsx';
import api from '../../utils/api';
import Table from '../../components/ui/Table';
import { formatCurrency } from '../../utils/formatters';

export default function SalesProfitReport() {
  const { t } = useTranslation();
  
  const monthStart = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];
  const [dateFrom, setDateFrom] = useState(monthStart);
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);
  const [reportType, setReportType] = useState('sales'); // 'sales', 'product-sales', 'profit', 'vat'

  const { data, isLoading } = useQuery({
    queryKey: ['report', reportType, dateFrom, dateTo],
    queryFn: async () => {
      const res = await api.get(`/reports/${reportType}?date_from=${dateFrom}&date_to=${dateTo}`);
      return res.data.data;
    },
  });

  const handleExport = async () => {
    try {
      const res = await api.get(`/reports/${reportType}?date_from=${dateFrom}&date_to=${dateTo}&export=true`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportType}-${dateFrom}-to-${dateTo}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to export excel');
    }
  };

  const getColumns = () => {
    if (reportType === 'sales') {
      return [
        { key: 'date', label: t('common.date') },
        { key: 'invoice_no', label: t('reports.invoice_no') },
        { key: 'dsr_name', label: t('reports.dsr') },
        { key: 'dealer_name', label: t('reports.dealer') },
        { key: 'grand_total', label: t('reports.amount'), render: v => formatCurrency(v) },
        { key: 'due', label: t('reports.due'), render: v => <span className={v > 0 ? 'text-danger' : 'text-success'}>{formatCurrency(v)}</span> },
      ];
    }
    if (reportType === 'product-sales') {
      return [
        { key: 'sku', label: t('reports.sku') },
        { key: 'product_name', label: t('reports.product') },
        { key: 'quantity_sold', label: t('reports.quantity_sold') },
        { key: 'total_revenue', label: t('reports.total_revenue'), render: v => formatCurrency(v) },
      ];
    }
    if (reportType === 'profit') {
      return [
        { key: 'sku', label: t('reports.sku') },
        { key: 'product_name', label: t('reports.product') },
        { key: 'quantity_sold', label: t('reports.quantity_sold') },
        { key: 'total_revenue', label: t('reports.total_revenue'), render: v => formatCurrency(v) },
        { key: 'estimated_cogs', label: t('reports.estimated_cogs'), render: v => formatCurrency(v) },
        { key: 'gross_profit', label: t('reports.gross_profit'), render: v => <span className="font-medium text-success">{formatCurrency(v)}</span> },
        { key: 'margin_pct', label: t('reports.margin_pct'), render: v => `${v}%` },
      ];
    }
    if (reportType === 'vat') {
      return [
        { key: 'date', label: t('common.date') },
        { key: 'invoice_no', label: t('reports.invoice_no') },
        { key: 'subtotal', label: t('reports.subtotal'), render: v => formatCurrency(v) },
        { key: 'vat_amount', label: t('reports.vat_amount'), render: v => formatCurrency(v) },
        { key: 'total_with_vat', label: t('reports.total'), render: v => formatCurrency(v) },
      ];
    }
    return [];
  };

  return (
    <div>
      <PageHeader
        title={t('reports.sales_profit')}
        onBack={() => window.history.back()}
        action={
          <button onClick={handleExport} className="btn-secondary">
            <Download className="w-4 h-4" /> {t('reports.export_excel')}
          </button>
        }
      />

      <div className="card mb-6 flex flex-wrap gap-4 items-end">
        <div>
          <label className="label">{t('reports.report_type')}</label>
          <select className="input" value={reportType} onChange={e => setReportType(e.target.value)}>
            <option value="sales">{t('reports.sales_register')}</option>
            <option value="product-sales">{t('reports.product_sales')}</option>
            <option value="profit">{t('reports.gross_profit')}</option>
            <option value="vat">{t('reports.vat_register')}</option>
          </select>
        </div>
        <div>
          <label className="label">{t('common.from')}</label>
          <input type="date" className="input" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
        </div>
        <div>
          <label className="label">{t('common.to')}</label>
          <input type="date" className="input" value={dateTo} onChange={e => setDateTo(e.target.value)} />
        </div>
      </div>

      <div className="card p-0">
        <Table columns={getColumns()} data={data || []} loading={isLoading} />
      </div>
    </div>
  );
}
