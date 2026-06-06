import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { PageHeader } from '../../components/ui/index.jsx';

const schema = z.object({
  name: z.string().min(1, 'Required').max(100),
  type: z.enum(['CASH', 'BANK', 'MOBILE_BANKING']),
  account_no: z.string().max(50).optional().nullable(),
  opening_balance: z.number().min(0),
  is_active: z.boolean(),
});

export default function AccountForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { t } = useTranslation();
  const isEdit = !!id;

  const { data: account, isLoading } = useQuery({
    queryKey: ['account', id],
    queryFn: () => api.get(`/accounts/${id}`).then((res) => res.data.data),
    enabled: isEdit,
  });

  const { register, handleSubmit, reset, formState: { errors }, watch } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      type: 'CASH',
      account_no: '',
      opening_balance: 0,
      is_active: true,
    },
  });

  useEffect(() => {
    if (account) {
      reset({
        name: account.name,
        type: account.type,
        account_no: account.account_no || '',
        opening_balance: account.opening_balance,
        is_active: account.is_active,
      });
    }
  }, [account, reset]);

  const mutation = useMutation({
    mutationFn: (data) =>
      isEdit ? api.put(`/accounts/${id}`, data) : api.post('/accounts', data),
    onSuccess: () => {
      qc.invalidateQueries(['accounts']);
      navigate('/accounts');
    },
  });

  const onSubmit = (data) => {
    // Treat empty string as null for account_no
    if (!data.account_no) data.account_no = null;
    mutation.mutate(data);
  };

  const accountType = watch('type');

  if (isEdit && isLoading) return <div className="p-4">{t('common.loading')}</div>;

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader
        title={isEdit ? t('accounts.edit') : t('accounts.add')}
        onBack={() => navigate('/accounts')}
      />
      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
        
        <div className="grid grid-cols-2 gap-4">
           <div>
            <label className="label">{t('accounts.type')}</label>
            <select className="input" {...register('type')}>
              <option value="CASH">{t('accounts.type_cash')}</option>
              <option value="BANK">{t('accounts.type_bank')}</option>
              <option value="MOBILE_BANKING">{t('accounts.type_mobile_banking')}</option>
            </select>
            {errors.type && <span className="text-danger text-sm">{errors.type.message}</span>}
          </div>

          <div>
            <label className="label">{t('accounts.name')}</label>
            <input className="input" {...register('name')} placeholder="e.g. Main Cash Drawer" />
            {errors.name && <span className="text-danger text-sm">{errors.name.message}</span>}
          </div>
        </div>

        {accountType !== 'CASH' && (
            <div>
              <label className="label">{t('accounts.account_no')}</label>
              <input className="input" {...register('account_no')} placeholder="e.g. Bank AC or bKash Number" />
              {errors.account_no && <span className="text-danger text-sm">{errors.account_no.message}</span>}
            </div>
        )}

        {!isEdit && (
            <div>
              <label className="label">{t('accounts.opening_balance')}</label>
              <input type="number" step="0.01" className="input" {...register('opening_balance', { valueAsNumber: true })} />
              {errors.opening_balance && <span className="text-danger text-sm">{errors.opening_balance.message}</span>}
            </div>
        )}

        <div className="flex items-center gap-2">
          <input type="checkbox" id="is_active" {...register('is_active')} className="rounded border-border text-primary focus:ring-primary" />
          <label htmlFor="is_active" className="text-sm font-medium text-text">{t('common.active')}</label>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-border mt-6">
          <button type="button" onClick={() => navigate('/accounts')} className="btn-secondary">
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
