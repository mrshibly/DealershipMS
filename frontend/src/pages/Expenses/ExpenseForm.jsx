import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { PageHeader } from '../../components/ui/index.jsx';

const schema = z.object({
  head_id: z.string().uuid('Required'),
  account_id: z.string().uuid('Required'),
  amount: z.number().min(1, 'Must be greater than 0'),
  date: z.string().min(1, 'Required'),
  description: z.string().max(200).optional().nullable(),
  reference: z.string().max(100).optional().nullable(),
});

export default function ExpenseForm() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { t } = useTranslation();

  const { data: headsData } = useQuery({
    queryKey: ['expense-heads-active'],
    queryFn: () => api.get('/expenses/heads?is_active=true').then(res => res.data.data),
  });
  
  const { data: accountsData } = useQuery({
    queryKey: ['accounts-active'],
    queryFn: () => api.get('/accounts?is_active=true').then(res => res.data.data),
  });

  const heads = headsData || [];
  const accounts = accountsData || [];

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      head_id: '',
      account_id: '',
      amount: 0,
      date: new Date().toLocaleDateString('en-CA'), // local date YYYY-MM-DD
      description: '',
      reference: '',
    },
  });

  const mutation = useMutation({
    mutationFn: (data) => api.post('/expenses', data),
    onSuccess: () => {
      qc.invalidateQueries(['expenses']);
      qc.invalidateQueries(['accounts']);
      navigate('/expenses');
    },
    onError: (err) => {
      alert(err.response?.data?.detail || "Failed to record expense");
    }
  });

  const onSubmit = (data) => {
    const payload = { ...data };
    if (!payload.description) payload.description = null;
    if (!payload.reference) payload.reference = null;
    mutation.mutate(payload);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader
        title={t('expenses.record')}
        onBack={() => navigate('/expenses')}
      />
      
      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">{t('expenses.head_name')}</label>
            <select className={`input ${errors.head_id ? 'input-error' : ''}`} {...register('head_id')}>
              <option value="">{t('common.select')}...</option>
              {heads.map(h => (
                <option key={h.id} value={h.id}>{h.name}</option>
              ))}
            </select>
            {errors.head_id && <p className="error-msg">{errors.head_id.message}</p>}
          </div>

          <div>
            <label className="label">{t('expenses.paid_from')}</label>
            <select className={`input ${errors.account_id ? 'input-error' : ''}`} {...register('account_id')}>
              <option value="">{t('common.select')}...</option>
              {accounts.map(a => (
                <option key={a.id} value={a.id}>{a.name} ({a.current_balance} ৳)</option>
              ))}
            </select>
            {errors.account_id && <p className="error-msg">{errors.account_id.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">{t('common.amount')}</label>
            <input type="number" step="0.01" className={`input ${errors.amount ? 'input-error' : ''}`} {...register('amount', { valueAsNumber: true })} />
            {errors.amount && <p className="error-msg">{errors.amount.message}</p>}
          </div>
          
          <div>
            <label className="label">{t('common.date')}</label>
            <input type="date" className={`input ${errors.date ? 'input-error' : ''}`} {...register('date')} />
            {errors.date && <p className="error-msg">{errors.date.message}</p>}
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">{t('expenses.reference')} <span className="text-text-muted text-xs">({t('common.optional')})</span></label>
            <input type="text" className="input" {...register('reference')} placeholder="e.g. Voucher 101" />
          </div>
          
          <div>
            <label className="label">{t('expenses.description')} <span className="text-text-muted text-xs">({t('common.optional')})</span></label>
            <input type="text" className="input" {...register('description')} placeholder="e.g. Monthly transport bill" />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-border mt-6">
          <button type="button" onClick={() => navigate('/expenses')} className="btn-secondary">
            {t('common.cancel')}
          </button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? t('common.loading') : t('common.save')}
          </button>
        </div>
      </form>
    </div>
  );
}
