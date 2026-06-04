/**
 * Stock View page — carton + piece breakdown for all products.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { AlertTriangle } from 'lucide-react';
import api from '../../utils/api';
import { formatBDT } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import { Badge, PageHeader } from '../../components/ui/index.jsx';

export default function StockView() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [lowStockOnly, setLowStockOnly] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['inventory-stock', page, lowStockOnly],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 50, low_stock_only: lowStockOnly });
      const res = await api.get(`/inventory/stock?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const stock = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const totalBuyValue = stock.reduce((s, r) => s + Number(r.buy_value || 0), 0);
  const totalSellValue = stock.reduce((s, r) => s + Number(r.sell_value || 0), 0);
  const lowStockCount = stock.filter((r) => r.is_low_stock).length;

  const columns = [
    {
      key: 'product_name_en',
      label: t('product.name'),
      render: (v, row) => (
        <div>
          <p className="font-medium text-text">{v}</p>
          {row.product_name_bn && <p className="text-xs text-text-muted font-bn">{row.product_name_bn}</p>}
        </div>
      ),
    },
    { key: 'sku', label: 'SKU' },
    { key: 'category_name', label: t('product.category'), render: (v) => v || '—' },
    {
      key: 'qty_cartons',
      label: t('inventory.cartons'),
      render: (v, row) => (
        <span className={row.is_low_stock ? 'text-danger font-semibold' : ''}>
          {v} {t('product.ctn')}
        </span>
      ),
    },
    {
      key: 'remaining_pcs',
      label: t('inventory.loose_pcs'),
      render: (v) => `${v} ${t('product.pcs')}`,
    },
    {
      key: 'qty_pieces',
      label: t('inventory.total_pcs'),
      render: (v, row) => (
        <div className="flex items-center gap-2">
          <span>{v}</span>
          {row.is_low_stock && <AlertTriangle className="w-3.5 h-3.5 text-warning" />}
        </div>
      ),
    },
    {
      key: 'buy_value',
      label: t('inventory.buy_value'),
      render: (v) => formatBDT(v),
    },
    {
      key: 'sell_value',
      label: t('inventory.sell_value'),
      render: (v) => formatBDT(v),
    },
    {
      key: 'is_low_stock',
      label: t('common.status'),
      render: (v) => <Badge variant={v ? 'warning' : 'success'}>{v ? t('product.low_stock') : t('inventory.in_stock')}</Badge>,
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.inventory')}
        subtitle={`${total} ${t('product.products')} · ${lowStockCount} ${t('product.low_stock')}`}
      />

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card">
          <p className="text-xs text-text-muted mb-1">{t('inventory.total_buy_value')}</p>
          <p className="text-xl font-bold text-primary">{formatBDT(totalBuyValue)}</p>
        </div>
        <div className="card">
          <p className="text-xs text-text-muted mb-1">{t('inventory.total_sell_value')}</p>
          <p className="text-xl font-bold text-success">{formatBDT(totalSellValue)}</p>
        </div>
        <div className="card">
          <p className="text-xs text-text-muted mb-1">{t('inventory.low_stock_items')}</p>
          <p className={`text-xl font-bold ${lowStockCount > 0 ? 'text-danger' : 'text-text'}`}>{lowStockCount}</p>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3 mb-4">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={lowStockOnly}
            onChange={(e) => { setLowStockOnly(e.target.checked); setPage(1); }}
            className="accent-primary"
          />
          {t('inventory.show_low_stock_only')}
        </label>
      </div>

      <div className="card p-0">
        <Table columns={columns} data={stock} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}
