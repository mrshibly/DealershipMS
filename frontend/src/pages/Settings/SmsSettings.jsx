import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Save, Phone } from 'lucide-react';

export default function SmsSettings() {
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
        sms_enabled: settings.sms_enabled === 'true',
        sms_api_key: settings.sms_api_key || '',
        sms_sender_id: settings.sms_sender_id || '',
      });
    }
  }, [settings, reset]);

  const mutation = useMutation({
    mutationFn: (data) => api.put('/settings', {
        ...data,
        sms_enabled: data.sms_enabled ? 'true' : 'false'
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['settings']);
    },
  });

  const onSubmit = (data) => {
    mutation.mutate(data);
  };

  const testSmsMutation = useMutation({
    mutationFn: (phone) => api.post('/settings/test-sms', { phone }),
    onSuccess: () => alert('Test SMS dispatched to Celery worker!'),
  });

  if (isLoading) return <div>{t('common.loading')}</div>;

  return (
    <div className="card">
      <h2 className="text-xl font-bold mb-6">{t('settings.sms_configuration')}</h2>
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-2xl">
        <div className="flex items-center gap-2 mb-6">
          <input type="checkbox" id="sms_enabled" {...register('sms_enabled')} className="w-4 h-4 text-primary" />
          <label htmlFor="sms_enabled" className="text-sm font-medium">{t('settings.enable_sms')}</label>
        </div>

        <div>
          <label className="label">{t('settings.api_key')}</label>
          <input type="password" {...register('sms_api_key')} className="input" placeholder="SSL Commerz API Key" />
        </div>
        
        <div>
          <label className="label">{t('settings.sender_id')}</label>
          <input {...register('sms_sender_id')} className="input" placeholder="e.g. 8809612345678" />
        </div>

        <div className="pt-4 flex justify-between items-center border-t border-border mt-6">
            <button 
                type="button" 
                className="btn-secondary"
                onClick={() => {
                    const phone = prompt('Enter a valid BD phone number (+880...) to test:');
                    if (phone) testSmsMutation.mutate(phone);
                }}
            >
                <Phone className="w-4 h-4" /> {t('settings.test_sms')}
            </button>
            <button type="submit" className="btn-primary" disabled={mutation.isPending}>
                <Save className="w-4 h-4" />
                {mutation.isPending ? t('common.saving') : t('common.save')}
            </button>
        </div>
      </form>
    </div>
  );
}
