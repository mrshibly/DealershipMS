import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Save } from 'lucide-react';

export default function CompanySettings() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { register, handleSubmit, reset } = useForm();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => api.get('/settings').then(res => res.data.data),
  });

  useEffect(() => {
    if (settings) {
      reset({
        company_name: settings.company_name || '',
        company_address: settings.company_address || '',
        company_phone: settings.company_phone || '',
        company_email: settings.company_email || '',
      });
    }
  }, [settings, reset]);

  const mutation = useMutation({
    mutationFn: (data) => api.put('/settings', data),
    onSuccess: () => {
      queryClient.invalidateQueries(['settings']);
    },
  });

  const onSubmit = (data) => {
    mutation.mutate(data);
  };

  if (isLoading) return <div>{t('common.loading')}</div>;

  return (
    <div className="card">
      <h2 className="text-xl font-bold mb-6">{t('settings.company_profile')}</h2>
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-2xl">
        <div>
          <label className="label">{t('settings.company_name')}</label>
          <input {...register('company_name')} className="input" />
        </div>
        
        <div>
          <label className="label">{t('settings.company_address')}</label>
          <textarea {...register('company_address')} className="input h-24" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">{t('settings.phone')}</label>
            <input {...register('company_phone')} className="input" />
          </div>
          <div>
            <label className="label">{t('settings.email')}</label>
            <input type="email" {...register('company_email')} className="input" />
          </div>
        </div>

        <div className="pt-4 flex justify-end">
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            <Save className="w-4 h-4" />
            {mutation.isPending ? t('common.saving') : t('common.save')}
          </button>
        </div>
      </form>
    </div>
  );
}
