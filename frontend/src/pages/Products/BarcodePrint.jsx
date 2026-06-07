import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Printer, Tag, Check, Square, CheckSquare } from 'lucide-react';
import api from '../../utils/api';

export default function BarcodePrint() {
  const { t, i18n } = useTranslation();
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [copies, setCopies] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);

  const { data: productsData, isLoading } = useQuery({
    queryKey: ['products-all'],
    queryFn: () => api.get('/products?per_page=500&is_active=true').then(r => r.data),
  });

  const products = productsData?.data || [];

  const toggleSelect = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === products.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(products.map(p => p.id)));
    }
  };

  const handlePrint = async () => {
    if (selectedIds.size === 0) {
      alert('Please select at least one product');
      return;
    }
    setIsGenerating(true);
    try {
      const res = await api.post(
        '/products/barcode-sheet',
        { product_ids: Array.from(selectedIds), copies },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'barcode-sheet.pdf';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to generate barcode sheet');
    } finally {
      setIsGenerating(false);
    }
  };

  const allSelected = products.length > 0 && selectedIds.size === products.length;

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text flex items-center gap-2">
            <Tag className="w-6 h-6 text-primary" />
            {t('barcodes.title')}
          </h1>
          <p className="text-text-muted text-sm mt-1">{t('barcodes.subtitle')}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-text-muted whitespace-nowrap">{t('barcodes.copies')}</label>
            <input
              type="number"
              min="1"
              max="20"
              value={copies}
              onChange={e => setCopies(Math.max(1, Number(e.target.value)))}
              className="input w-16 text-center"
            />
          </div>
          <button
            className="btn-primary"
            onClick={handlePrint}
            disabled={isGenerating || selectedIds.size === 0}
          >
            {isGenerating ? (
              t('common.loading')
            ) : (
              <>
                <Printer className="w-4 h-4 mr-2" />
                {t('barcodes.print_selected')} ({selectedIds.size})
              </>
            )}
          </button>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-border bg-background/50 flex items-center gap-3">
          <button
            className="btn-icon"
            onClick={toggleAll}
            title={allSelected ? 'Deselect all' : 'Select all'}
          >
            {allSelected
              ? <CheckSquare className="w-5 h-5 text-primary" />
              : <Square className="w-5 h-5 text-text-muted" />
            }
          </button>
          <span className="text-sm text-text-muted">
            {selectedIds.size > 0
              ? `${selectedIds.size} ${t('barcodes.selected')}`
              : t('barcodes.select_hint')}
          </span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-text-muted">{t('common.loading')}...</div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-background text-text-muted">
              <tr>
                <th className="px-4 py-3 w-12"></th>
                <th className="px-4 py-3">{t('product.name')}</th>
                <th className="px-4 py-3">SKU</th>
                <th className="px-4 py-3">Barcode</th>
                <th className="px-4 py-3 text-right">{t('product.sell_price')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {products.map(p => (
                <tr
                  key={p.id}
                  className={`cursor-pointer transition-colors ${
                    selectedIds.has(p.id) ? 'bg-primary/5' : 'hover:bg-background/50'
                  }`}
                  onClick={() => toggleSelect(p.id)}
                >
                  <td className="px-4 py-3">
                    {selectedIds.has(p.id)
                      ? <CheckSquare className="w-5 h-5 text-primary" />
                      : <Square className="w-5 h-5 text-text-muted" />
                    }
                  </td>
                  <td className="px-4 py-3 font-medium text-text">
                    {i18n.language === 'bn' && p.name_bn ? p.name_bn : p.name_en}
                  </td>
                  <td className="px-4 py-3 text-text-muted font-mono text-xs">{p.sku || '-'}</td>
                  <td className="px-4 py-3 text-text-muted font-mono text-xs">{p.barcode || <span className="text-danger/60 italic">no barcode</span>}</td>
                  <td className="px-4 py-3 text-right font-medium">৳{Number(p.sell_price || 0).toLocaleString('en-BD', { minimumFractionDigits: 2 })}</td>
                </tr>
              ))}
              {products.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-text-muted">
                    {t('common.no_data')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
