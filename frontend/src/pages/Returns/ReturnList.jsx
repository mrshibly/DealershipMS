import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Plus, RotateCcw } from 'lucide-react';
import api from '../../utils/api';
import Table from '../../components/ui/Table';
import { PageHeader } from '../../components/ui/index.jsx';

export default function ReturnList() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const { data: returns, isLoading } = useQuery({
    queryKey: ['returns'],
    queryFn: () => api.get('/returns').then((res) => res.data.data),
  });

  const columns = [
    { key: 'return_date', label: t('invoices.date') },
    { key: 'invoice_no', label: t('invoices.invoice_no'), render: (v) => <span className="font-semibold">{v}</span> },
    { key: 'product_name', label: t('inventory.product') },
    { key: 'qty_returned', label: t('inventory.stock_pcs') },
    { key: 'reason', label: t('common.notes'), render: (v) => <span className="text-sm text-text-muted">{v || '-'}</span> },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.returns')}
        action={
          <button onClick={() => navigate('/returns/new')} className="btn-primary">
            <Plus className="w-4 h-4" /> {t('common.add_new')}
          </button>
        }
      />
      <div className="card p-0 mt-6">
        <div className="p-4 border-b border-border flex items-center gap-2 text-text-muted">
            <RotateCcw className="w-5 h-5" />
            <span className="font-medium">{t('returns.title', 'Merchandise Returns')}</span>
        </div>
        <Table columns={columns} data={returns || []} loading={isLoading} />
      </div>
    </div>
  );
}
