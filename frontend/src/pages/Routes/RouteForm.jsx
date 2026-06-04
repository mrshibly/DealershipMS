import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Save, ArrowLeft } from 'lucide-react';
import api from '../../utils/api';
import { PageHeader } from '../../components/ui/index.jsx';

const schema = z.object({
  name: z.string().min(1, 'Route name is required'),
  area: z.string().min(1, 'Area is required'),
  description: z.string().optional().or(z.literal('')),
  is_active: z.boolean().default(true),
});

export default function RouteForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const qc = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ['route', id],
    queryFn: async () => { const r = await api.get(`/routes/${id}`); return r.data.data; },
    enabled: isEdit,
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { is_active: true },
  });

  useEffect(() => { if (existing) reset(existing); }, [existing, reset]);

  const mutation = useMutation({
    mutationFn: (data) => isEdit ? api.put(`/routes/${id}`, data) : api.post('/routes', data),
    onSuccess: () => { qc.invalidateQueries(['routes']); navigate('/routes'); },
  });

  const Field = ({ name, label, children }) => (
    <div className="mb-4">
      <label htmlFor={name} className="label">{label}</label>
      {children}
      {errors[name] && <p className="error-msg">{errors[name]?.message}</p>}
    </div>
  );

  return (
    <div>
      <PageHeader
        title={isEdit ? t('route.edit') : t('route.add')}
        action={<button onClick={() => navigate(-1)} className="btn-secondary"><ArrowLeft className="w-4 h-4" />{t('common.cancel')}</button>}
      />
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
        <div className="max-w-xl card">
          <Field name="name" label={t('route.name')}>
            <input id="name" className={`input ${errors.name ? 'input-error' : ''}`} {...register('name')} />
          </Field>
          <Field name="area" label={t('route.area')}>
            <input id="area" className={`input ${errors.area ? 'input-error' : ''}`} {...register('area')} />
          </Field>
          <Field name="description" label={t('route.description')}>
            <textarea id="description" rows={3} className="input resize-none" {...register('description')} />
          </Field>
          {isEdit && (
            <div className="mb-4 flex items-center gap-2">
              <input id="is_active" type="checkbox" className="checkbox" {...register('is_active')} />
              <label htmlFor="is_active" className="label cursor-pointer mb-0">{t('common.active')}</label>
            </div>
          )}

          {mutation.isError && (
            <div className="mt-4 p-3 bg-danger-light border border-danger rounded-lg text-sm text-danger">
              {mutation.error?.response?.data?.detail || 'An error occurred'}
            </div>
          )}

          <div className="flex justify-end gap-3 mt-6">
            <button type="button" onClick={() => navigate(-1)} className="btn-secondary">{t('common.cancel')}</button>
            <button id="route-save-btn" type="submit" disabled={mutation.isPending} className="btn-primary">
              <Save className="w-4 h-4" />
              {mutation.isPending ? t('common.loading') : t('common.save')}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
