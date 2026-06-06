import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Save, ArrowLeft } from 'lucide-react';

export default function TargetForm() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { register, handleSubmit } = useForm();

  const { data: dsrs } = useQuery({
    queryKey: ['dsrs'],
    queryFn: () => api.get('/dsrs').then(res => res.data.data),
  });

  const mutation = useMutation({
    mutationFn: (data) => api.post('/targets', {
        ...data,
        target_month: data.target_month + '-01',
        target_amount: parseFloat(data.target_amount)
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['targets']);
      navigate('/targets');
    },
  });

  const onSubmit = (data) => {
    mutation.mutate(data);
  };

  return (
    <div className="card max-w-2xl mx-auto mt-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/targets')} className="p-2 hover:bg-background rounded-full transition-colors">
          <ArrowLeft className="w-5 h-5 text-text-muted" />
        </button>
        <h2 className="text-xl font-bold">{t('common.add_new')}</h2>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="label">DSR</label>
          <select {...register('dsr_id', { required: true })} className="input">
            <option value="">{t('common.select')}...</option>
            {dsrs?.map(dsr => (
              <option key={dsr.id} value={dsr.id}>{dsr.name}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
            <label className="label">Month</label>
            <input type="month" {...register('target_month', { required: true })} className="input" />
            </div>

            <div>
            <label className="label">Target Amount (BDT)</label>
            <input type="number" step="0.01" {...register('target_amount', { required: true })} className="input" />
            </div>
        </div>

        <div className="pt-4 flex justify-end border-t border-border mt-6">
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            <Save className="w-4 h-4" />
            {mutation.isPending ? t('common.saving') : t('common.save')}
          </button>
        </div>
      </form>
    </div>
  );
}
