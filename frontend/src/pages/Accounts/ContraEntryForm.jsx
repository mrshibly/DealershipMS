import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { PageHeader } from '../../components/ui/index.jsx';

const schema = z.object({
  from_account_id: z.string().uuid('Required'),
  to_account_id: z.string().uuid('Required'),
  amount: z.number().min(1, 'Must be greater than 0'),
  date: z.string().min(1, 'Required'),
  narration: z.string().max(200).optional().nullable(),
  reference: z.string().max(100).optional().nullable(),
}).refine(data => data.from_account_id !== data.to_account_id, {
  message: "Source and destination accounts must be different",
  path: ["to_account_id"],
});

export default function ContraEntryForm() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { t } = useTranslation();

  const { data: accountsData } = useQuery({
    queryKey: ['accounts-active'],
    queryFn: () => api.get('/accounts?is_active=true').then(res => res.data.data),
  });
  
  const accounts = accountsData || [];

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      from_account_id: '',
      to_account_id: '',
      amount: 0,
      date: new Date().toISOString().split('T')[0],
      narration: '',
      reference: '',
    },
  });

  const mutation = useMutation({
    mutationFn: (data) => api.post('/contra-entries', data),
    onSuccess: () => {
      qc.invalidateQueries(['accounts']);
      navigate('/accounts');
    },
    onError: (err) => {
        alert(err.response?.data?.detail || "Failed to record contra entry");
    }
  });

  const onSubmit = (data) => {
    mutation.mutate(data);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader
        title={t('accounts.contra_transfer')}
        onBack={() => navigate('/accounts')}
      />
      
      <div className="bg-warning/10 text-warning p-4 rounded-xl mb-6 text-sm">
          {t('accounts.contra_help')}
      </div>
      
      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
        
        <div className="grid grid-cols-2 gap-4">
           <div>
            <label className="label">{t('accounts.from_account')}</label>
            <select className="input" {...register('from_account_id')}>
              <option value="">{t('common.select')}...</option>
              {accounts.map(a => (
                  <option key={a.id} value={a.id}>{a.name} ({a.current_balance} ৳)</option>
              ))}
            </select>
            {errors.from_account_id && <span className="text-danger text-sm">{errors.from_account_id.message}</span>}
          </div>

          <div>
            <label className="label">{t('accounts.to_account')}</label>
            <select className="input" {...register('to_account_id')}>
              <option value="">{t('common.select')}...</option>
              {accounts.map(a => (
                  <option key={a.id} value={a.id}>{a.name} ({a.current_balance} ৳)</option>
              ))}
            </select>
            {errors.to_account_id && <span className="text-danger text-sm">{errors.to_account_id.message}</span>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">{t('common.amount')}</label>
              <input type="number" step="0.01" className="input" {...register('amount', { valueAsNumber: true })} />
              {errors.amount && <span className="text-danger text-sm">{errors.amount.message}</span>}
            </div>
            
            <div>
              <label className="label">{t('common.date')}</label>
              <input type="date" className="input" {...register('date')} />
              {errors.date && <span className="text-danger text-sm">{errors.date.message}</span>}
            </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">{t('accounts.reference')} <span className="text-text-muted text-xs">({t('common.optional')})</span></label>
              <input type="text" className="input" {...register('reference')} placeholder="e.g. Cheque No" />
            </div>
            
            <div>
              <label className="label">{t('accounts.narration')} <span className="text-text-muted text-xs">({t('common.optional')})</span></label>
              <input type="text" className="input" {...register('narration')} placeholder="e.g. Cash withdrawn for petty cash" />
            </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-border mt-6">
          <button type="button" onClick={() => navigate('/accounts')} className="btn-secondary">
            {t('common.cancel')}
          </button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? t('common.loading') : t('common.confirm')}
          </button>
        </div>
      </form>
    </div>
  );
}
