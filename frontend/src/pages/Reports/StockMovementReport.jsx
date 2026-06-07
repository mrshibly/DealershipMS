import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Download } from 'lucide-react';
import { PageHeader } from '../../components/ui/index.jsx';
import api from '../../utils/api';
import Table from '../../components/ui/Table';
import { formatDate } from '../../utils/formatters';

export default function StockMovementReport() {
  const { t, i18n } = useTranslation();
  const [productId, setProductId] = useState('');

  const { data: productsData } = useQuery({
    queryKey: ['products-for-report'],
    queryFn: () => api.get('/products').then(res => res.data.data),
  });
  const products = productsData || [];

  const { data, isLoading } = useQuery({
    queryKey: ['report-stock-movement', productId],
    queryFn: async () => {
      const res = await api.get(`/reports/stock-movement/${productId}`);
      return res.data.data;
    },
    enabled: !!productId,
  });

  const handleExport = async () => {
    if (!productId) return;
    try {
      const res = await api.get(`/reports/stock-movement/${productId}?export=true`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `stock-movement-${productId}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to export excel');
    }
  };

  const columns = [
    { key: 'date', label: t('common.date'), render: v => formatDate(v) },
    { key: 'type', label: t('reports.type') },
    { key: 'reference_id', label: t('reports.reference') },
    { key: 'qty_change', label: t('reports.qty_change'), render: v => (
        <span className={`font-bold ${v > 0 ? 'text-success' : 'text-danger'}`}>{v > 0 ? `+${v}` : v}</span>
    )},
    { key: 'running_balance', label: t('reports.running_balance'), render: v => <span className="font-bold">{v}</span> },
    { key: 'notes', label: t('reports.notes') },
  ];

  return (
    <div>
      <PageHeader
        title={t('reports.stock_movement')}
        onBack={() => window.history.back()}
        action={
          <button onClick={handleExport} className="btn-secondary" disabled={!productId}>
            <Download className="w-4 h-4" /> {t('reports.export_excel')}
          </button>
        }
      />

      <div className="card mb-6 flex flex-wrap gap-4 items-end">
        <div className="w-full md:w-1/3">
          <label className="label">{t('reports.select_product')}</label>
          <select className="input" value={productId} onChange={e => setProductId(e.target.value)}>
            <option value="">{t('common.select')}...</option>
            {products.map(p => (
                <option key={p.id} value={p.id}>[{p.sku}] {i18n.language === 'bn' && p.name_bn ? p.name_bn : p.name_en}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="card p-0">
        {!productId ? (
            <div className="p-8 text-center text-text-muted">{t('reports.select_product_prompt')}</div>
        ) : (
            <Table columns={columns} data={data || []} loading={isLoading} />
        )}
      </div>
    </div>
  );
}
