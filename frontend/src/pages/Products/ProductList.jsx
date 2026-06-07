/**
 * Product List Page — searchable, paginated, with barcode download.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Plus, Download, Edit, Trash2, BarChart3 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import { formatBDT } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import { Badge, PageHeader, SearchInput } from '../../components/ui/index.jsx';

export default function ProductList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['products', page, search],
    queryFn: async () => {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (search) params.set('search', search);
      const res = await api.get(`/products?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/products/${id}`),
    onSuccess: () => {
      qc.invalidateQueries(['products']);
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: t('common.delete_success'), type: 'success' } }));
    },
    onError: (err) => {
      window.dispatchEvent(new CustomEvent('dms:toast', { detail: { message: err.response?.data?.detail || t('common.error'), type: 'danger' } }));
    }
  });

  const downloadBarcode = async (productId, sku) => {
    const res = await api.get(`/products/${productId}/barcode`, { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${sku}.png`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const products = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const columns = [
    {
      key: 'name_en',
      label: t('product.name'),
      render: (v, row) => (
        <div>
          <p className="font-medium text-text">{v}</p>
          {row.name_bn && <p className="text-xs text-text-muted font-bn">{row.name_bn}</p>}
        </div>
      ),
    },
    { key: 'sku', label: 'SKU' },
    { key: 'brand', label: 'Brand', render: (v) => v || '—' },
    {
      key: 'category_name',
      label: t('product.category'),
      render: (v) => v || '—',
    },
    {
      key: 'sell_price',
      label: t('product.sell_price'),
      render: (v) => <span className="font-medium">{formatBDT(v)}</span>,
    },
    {
      key: 'stock_qty_pieces',
      label: t('product.stock'),
      render: (v, row) => (
        <div>
          <span className={row.is_low_stock ? 'text-danger font-semibold' : 'text-text'}>
            {row.stock_qty_cartons} {t('product.ctn')} + {v % (row.pcs_per_carton || 1)} {t('product.pcs')}
          </span>
          {row.is_low_stock && (
            <span className="ml-2 badge badge-danger">{t('product.low_stock')}</span>
          )}
        </div>
      ),
    },
    {
      key: 'is_active',
      label: t('common.status'),
      render: (v) => (
        <Badge variant={v ? 'success' : 'muted'}>
          {v ? t('common.active') : t('common.inactive')}
        </Badge>
      ),
    },
    {
      key: 'id',
      label: t('common.actions'),
      render: (id, row) => (
        <div className="flex items-center gap-1">
          <button
            onClick={() => navigate(`/products/${id}/edit`)}
            className="p-1.5 rounded hover:bg-primary-light text-text-muted hover:text-primary transition-colors"
            title={t('common.edit')}
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => downloadBarcode(id, row.sku)}
            className="p-1.5 rounded hover:bg-border text-text-muted hover:text-text transition-colors"
            title="Download barcode"
          >
            <BarChart3 className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              if (window.confirm(t('common.delete_confirm'))) {
                deleteMutation.mutate(id);
              }
            }}
            className="p-1.5 rounded hover:bg-danger-light text-text-muted hover:text-danger transition-colors"
            title={t('common.delete')}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.products')}
        subtitle={`${total} ${t('product.total_products')}`}
        action={
          <Link to="/products/new" className="btn-primary">
            <Plus className="w-4 h-4" />
            {t('product.add_product')}
          </Link>
        }
      />

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <SearchInput
          value={search}
          onChange={(v) => { setSearch(v); setPage(1); }}
          placeholder={t('product.search_placeholder')}
        />
      </div>

      <div className="card p-0">
        <Table columns={columns} data={products} loading={isLoading} />
        <div className="px-4 pb-4">
          <Pagination page={page} pages={pages} total={total} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}
