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

const BD_PHONE = /^(\+880|0)[0-9]{10}$/;

const schema = z.object({
  name: z.string().min(1, 'DSR name is required'),
  phone: z.string().regex(BD_PHONE, 'Enter valid BD phone (+880XXXXXXXXXX)'),
  nid: z.string().optional().or(z.literal('')),
  route_id: z.string().uuid('Please select a route').nullable().or(z.literal('')),
  commission_rate: z.coerce.number().min(0).max(100).default(0),
  joining_date: z.string().optional().or(z.literal('')),
  is_active: z.boolean().default(true),
});

export default function DSRForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const qc = useQueryClient();

  const { data: routesData } = useQuery({
    queryKey: ['routes-lookup'],
    queryFn: async () => {
      const res = await api.get('/routes?page=1&per_page=100');
      return res.data?.data || [];
    },
  });

  const { data: existing } = useQuery({
    queryKey: ['dsr', id],
    queryFn: async () => { const r = await api.get(`/dsrs/${id}`); return r.data.data; },
    enabled: isEdit,
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { commission_rate: 0, is_active: true },
  });

  useEffect(() => {
    if (existing) {
      reset({
        ...existing,
        route_id: existing.route_id || '',
        joining_date: existing.joining_date ? existing.joining_date.substring(0, 10) : '',
      });
    }
  }, [existing, reset]);

  const mutation = useMutation({
    mutationFn: (data) => {
      const payload = {
        ...data,
        route_id: data.route_id === '' ? null : data.route_id,
        joining_date: data.joining_date === '' ? null : data.joining_date,
      };
      return isEdit ? api.put(`/dsrs/${id}`, payload) : api.post('/dsrs', payload);
    },
    onSuccess: () => { qc.invalidateQueries(['dsrs']); navigate('/dsrs'); },
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
        title={isEdit ? t('dsr.edit') : t('dsr.add')}
        action={<button onClick={() => navigate(-1)} className="btn-secondary"><ArrowLeft className="w-4 h-4" />{t('common.cancel')}</button>}
      />
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
        <div className="max-w-xl card">
          <Field name="name" label={t('dsr.name')}>
            <input id="name" className={`input ${errors.name ? 'input-error' : ''}`} {...register('name')} />
          </Field>
          <Field name="phone" label={t('dsr.phone')}>
            <input id="phone" className={`input ${errors.phone ? 'input-error' : ''}`} placeholder="+880XXXXXXXXXX" {...register('phone')} />
          </Field>
          <Field name="nid" label={t('dsr.nid')}>
            <input id="nid" className={`input ${errors.nid ? 'input-error' : ''}`} {...register('nid')} />
          </Field>
          <Field name="route_id" label={t('dsr.route')}>
            <select id="route_id" className={`input ${errors.route_id ? 'input-error' : ''}`} {...register('route_id')}>
              <option value="">-- select route --</option>
              {(routesData || []).map((r) => (
                <option key={r.id} value={r.id}>{r.name} ({r.area})</option>
              ))}
            </select>
          </Field>
          <Field name="commission_rate" label={t('dsr.commission_rate')}>
            <input id="commission_rate" type="number" step="0.01" min="0" max="100" className="input" {...register('commission_rate')} />
          </Field>
          <Field name="joining_date" label={t('dsr.joining_date')}>
            <input id="joining_date" type="date" className="input" {...register('joining_date')} />
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
            <button id="dsr-save-btn" type="submit" disabled={mutation.isPending} className="btn-primary">
              <Save className="w-4 h-4" />
              {mutation.isPending ? t('common.loading') : t('common.save')}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
