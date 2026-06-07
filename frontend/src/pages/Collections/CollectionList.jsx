import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { DollarSign, Plus, Eye } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import api from '../../utils/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import Table from '../../components/ui/Table';
import Pagination from '../../components/ui/Pagination';
import Modal from '../../components/ui/Modal';

const collectionSchema = z.object({
  invoice_id: z.string().min(1, 'Invoice is required'),
  amount: z.coerce.number().min(0.01, 'Must be greater than 0'),
  payment_method: z.string().min(1, 'Required'),
  reference_no: z.string().optional(),
  notes: z.string().optional(),
  account_id: z.string().min(1, 'Account is required'),
});

export default function CollectionList() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Filters
  const [dealerFilter, setDealerFilter] = useState('');
  const [dsrFilter, setDsrFilter] = useState('');

  // Fetch Lookups
  const { data: dealers } = useQuery({ queryKey: ['dealers'], queryFn: () => api.get('/dealers?per_page=100').then(res => res.data.data) });
  const { data: dsrs } = useQuery({ queryKey: ['dsrs'], queryFn: () => api.get('/dsrs?per_page=100').then(res => res.data.data) });
  const { data: accounts } = useQuery({ queryKey: ['accounts'], queryFn: () => api.get('/accounts?per_page=100').then(res => res.data.data) });
  const { data: invoices } = useQuery({
    queryKey: ['invoices-collect-lookup'],
    queryFn: () => api.get('/invoices?per_page=200').then(res => res.data.data.filter(inv => ['CONFIRMED', 'PARTIAL'].includes(inv.status))),
  });

  // Fetch collections
  const { data, isLoading } = useQuery({
    queryKey: ['collections', page, dealerFilter, dsrFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ page: page.toString(), per_page: '20' });
      if (dealerFilter) params.append('dealer_id', dealerFilter);
      if (dsrFilter) params.append('dsr_id', dsrFilter);
      const res = await api.get(`/collections?${params.toString()}`);
      return res.data;
    },
  });

  // Form setup
  const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm({
    resolver: zodResolver(collectionSchema),
    defaultValues: {
      invoice_id: '',
      amount: 0,
      payment_method: 'CASH',
      account_id: '',
      reference_no: '',
      notes: '',
    }
  });

  const watchInvoiceId = watch('invoice_id');
  const selectedInvoice = invoices?.find(inv => inv.id === watchInvoiceId);
  const outstanding = selectedInvoice ? (Number(selectedInvoice.grand_total) - Number(selectedInvoice.paid_amount)) : 0;

  // Update amount automatically when invoice is selected
  const handleInvoiceChange = (e) => {
    const invId = e.target.value;
    setValue('invoice_id', invId);
    const inv = invoices?.find(i => i.id === invId);
    if (inv) {
      const out = Number(inv.grand_total) - Number(inv.paid_amount);
      setValue('amount', out);
    } else {
      setValue('amount', 0);
    }
  };

  // Add Collection Mutation
  const collectMutation = useMutation({
    mutationFn: (data) => api.post(`/invoices/${data.invoice_id}/collect`, {
      amount: data.amount,
      payment_method: data.payment_method,
      reference_no: data.reference_no,
      notes: data.notes,
      account_id: data.account_id,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['collections']);
      queryClient.invalidateQueries(['invoices-collect-lookup']);
      queryClient.invalidateQueries(['accounts']);
      setIsModalOpen(false);
      reset();
    },
    onError: (err) => {
      alert(err.response?.data?.detail || t('common.error'));
    }
  });

  const collections = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 0;

  const columns = [
    {
      key: 'invoice_no',
      label: t('collections.invoice', 'Invoice No'),
      render: (val, row) => (
        row.invoice_id ? (
          <Link to={`/invoices/${row.invoice_id}`} className="text-primary font-medium hover:underline">
            {val || '—'}
          </Link>
        ) : '—'
      ),
    },
    {
      key: 'collected_at',
      label: t('collections.date', 'Collected At'),
      render: (val) => formatDate(val),
    },
    {
      key: 'dealer_name',
      label: t('collections.dealer', 'Dealer'),
      render: (val) => val || '—',
    },
    {
      key: 'dsr_name',
      label: t('collections.dsr', 'DSR'),
      render: (val) => val || '—',
    },
    {
      key: 'account_name',
      label: t('collections.account', 'Account'),
      render: (val) => val || '—',
    },
    {
      key: 'payment_method',
      label: t('collections.method', 'Method'),
      render: (val) => (
        <span className="badge badge-info uppercase tracking-wider text-xs">
          {val ? val.replace('_', ' ') : '—'}
        </span>
      ),
    },
    {
      key: 'reference_no',
      label: t('collections.reference', 'Reference'),
      render: (val) => val || '—',
    },
    {
      key: 'amount',
      label: t('collections.amount', 'Amount'),
      render: (val) => formatCurrency(val),
      className: 'text-right font-semibold text-success font-mono',
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text flex items-center gap-2">
            <DollarSign className="w-6 h-6 text-success" />
            {t('nav.due_collection', 'Due Collections')}
          </h1>
          <p className="text-text-muted text-sm mt-1">
            {t('collections.list_subtitle', 'Monitor payments collected from dealers and shops')}
          </p>
        </div>
        <button
          onClick={() => {
            reset();
            setIsModalOpen(true);
          }}
          className="btn-primary"
        >
          <Plus className="w-4 h-4 mr-2" />
          {t('collections.add_collection', 'Record Collection')}
        </button>
      </div>

      {/* Filters Card */}
      <div className="card mb-6 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">{t('collections.filter_dealer', 'Filter by Dealer')}</label>
            <select
              className="input"
              value={dealerFilter}
              onChange={(e) => {
                setDealerFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">{t('common.all', 'All Dealers')}</option>
              {dealers?.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">{t('collections.filter_dsr', 'Filter by DSR')}</label>
            <select
              className="input"
              value={dsrFilter}
              onChange={(e) => {
                setDsrFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">{t('common.all', 'All DSRs')}</option>
              {dsrs?.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="card p-0 overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200">
        <Table columns={columns} data={collections} loading={isLoading} />
        {pages > 1 && (
          <div className="p-4 border-t border-border">
            <Pagination
              page={page}
              pages={pages}
              total={total}
              onPageChange={setPage}
            />
          </div>
        )}
      </div>

      {/* Record Collection Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={t('collections.record_title', 'Record Dealer Payment Collection')}>
        <form onSubmit={handleSubmit((d) => collectMutation.mutate(d))} className="space-y-4">
          <div>
            <label className="label">{t('collections.select_invoice', 'Select Outstanding Invoice')}</label>
            <select className="input font-medium" onChange={handleInvoiceChange} value={watchInvoiceId}>
              <option value="">{t('common.select', 'Select Invoice')}</option>
              {invoices?.map(inv => (
                <option key={inv.id} value={inv.id}>
                  {inv.invoice_no} — {inv.dealer_name || 'Dealer'} (Outstanding: {formatCurrency(Number(inv.grand_total) - Number(inv.paid_amount))})
                </option>
              ))}
            </select>
            {errors.invoice_id && <p className="text-danger text-xs mt-1">{errors.invoice_id.message}</p>}
          </div>

          {selectedInvoice && (
            <div className="bg-primary-light/30 border border-primary-light/50 p-3 rounded-lg text-sm text-primary flex justify-between font-medium">
              <span>{t('invoices.outstanding', 'Outstanding Balance')}:</span>
              <span className="font-bold">{formatCurrency(outstanding)}</span>
            </div>
          )}

          <div>
            <label className="label">{t('collections.amount', 'Collection Amount')}</label>
            <input
              type="number"
              step="0.01"
              max={outstanding || undefined}
              className="input text-lg font-bold text-success font-mono"
              {...register('amount')}
            />
            {errors.amount && <p className="text-danger text-xs mt-1">{errors.amount.message}</p>}
          </div>

          <div>
            <label className="label">{t('collections.method', 'Payment Method')}</label>
            <select className="input" {...register('payment_method')}>
              <option value="CASH">Cash</option>
              <option value="BKASH">bKash</option>
              <option value="NAGAD">Nagad</option>
              <option value="ROCKET">Rocket</option>
              <option value="BANK_TRANSFER">Bank Transfer</option>
              <option value="CHEQUE">Cheque</option>
            </select>
            {errors.payment_method && <p className="text-danger text-xs mt-1">{errors.payment_method.message}</p>}
          </div>

          <div>
            <label className="label">{t('accounts.account', 'Deposit Account')}</label>
            <select className="input font-medium" {...register('account_id')}>
              <option value="">{t('common.select', 'Select Account')}</option>
              {accounts?.map(acc => (
                <option key={acc.id} value={acc.id}>
                  {acc.name} ({acc.account_type} — {formatCurrency(acc.balance)})
                </option>
              ))}
            </select>
            {errors.account_id && <p className="text-danger text-xs mt-1">{errors.account_id.message}</p>}
          </div>

          <div>
            <label className="label">{t('collections.reference', 'Reference No / TrxID')}</label>
            <input type="text" className="input" {...register('reference_no')} placeholder="TrxID, Cheque number, etc." />
          </div>

          <div>
            <label className="label">{t('collections.notes', 'Notes')}</label>
            <textarea className="input" rows="2" {...register('notes')} placeholder={t('common.optional', 'Optional notes')}></textarea>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>
              {t('common.cancel')}
            </button>
            <button type="submit" className="btn-success" disabled={collectMutation.isPending}>
              {collectMutation.isPending ? t('common.loading') : t('common.save', 'Record Payment')}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
