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
  name: z.string().min(1, 'Dealer name is required'),
  owner_name: z.string().optional().or(z.literal('')),
  phone: z.string().regex(BD_PHONE, 'Enter valid BD phone (+880XXXXXXXXXX)'),
  address: z.string().optional().or(z.literal('')),
  district: z.string().optional().or(z.literal('')),
  upazila: z.string().optional().or(z.literal('')),
  trade_license: z.string().optional().or(z.literal('')),
  nid: z.string().optional().or(z.literal('')),
  route_id: z.string().uuid('Please select a route').nullable().or(z.literal('')),
  is_active: z.boolean().default(true),
});

export default function DealerForm() {
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
    queryKey: ['dealer', id],
    queryFn: async () => { const r = await api.get(`/dealers/${id}`); return r.data.data; },
    enabled: isEdit,
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { is_active: true },
  });

  useEffect(() => {
    if (existing) {
      reset({
        ...existing,
        route_id: existing.route_id || '',
      });
    }
  }, [existing, reset]);

  const mutation = useMutation({
    mutationFn: (data) => {
      const payload = {
        ...data,
        route_id: data.route_id === '' ? null : data.route_id,
      };
      return isEdit ? api.put(`/dealers/${id}`, payload) : api.post('/dealers', payload);
    },
    onSuccess: () => { qc.invalidateQueries(['dealers']); navigate('/dealers'); },
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
        title={isEdit ? t('dealer.edit') : t('dealer.add')}
        action={<button onClick={() => navigate(-1)} className="btn-secondary"><ArrowLeft className="w-4 h-4" />{t('common.cancel')}</button>}
      />
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="font-semibold text-text mb-4">{t('supplier.basic_info')}</h2>
            <Field name="name" label={t('dealer.name')}>
              <input id="name" className={`input ${errors.name ? 'input-error' : ''}`} {...register('name')} />
            </Field>
            <Field name="owner_name" label={t('dealer.owner')}>
              <input id="owner_name" className={`input ${errors.owner_name ? 'input-error' : ''}`} {...register('owner_name')} />
            </Field>
            <Field name="phone" label={t('dealer.phone')}>
              <input id="phone" className={`input ${errors.phone ? 'input-error' : ''}`} placeholder="+880XXXXXXXXXX" {...register('phone')} />
            </Field>
            <Field name="address" label={t('dealer.address')}>
              <textarea id="address" rows={2} className="input resize-none" {...register('address')} />
            </Field>
          </div>

          <div className="card">
            <h2 className="font-semibold text-text mb-4">Location & Details</h2>
            <div className="grid grid-cols-2 gap-3">
              <Field name="district" label={t('dealer.district')}>
                <input id="district" className="input" {...register('district')} />
              </Field>
              <Field name="upazila" label={t('dealer.upazila')}>
                <input id="upazila" className="input" {...register('upazila')} />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field name="trade_license" label={t('dealer.trade_license')}>
                <input id="trade_license" className="input" {...register('trade_license')} />
              </Field>
              <Field name="nid" label={t('dealer.nid')}>
                <input id="nid" className="input" {...register('nid')} />
              </Field>
            </div>
            <Field name="route_id" label={t('dealer.route')}>
              <select id="route_id" className={`input ${errors.route_id ? 'input-error' : ''}`} {...register('route_id')}>
                <option value="">-- select route --</option>
                {(routesData || []).map((r) => (
                  <option key={r.id} value={r.id}>{r.name} ({r.area})</option>
                ))}
              </select>
            </Field>
            {isEdit && (
              <div className="mb-4 flex items-center gap-2">
                <input id="is_active" type="checkbox" className="checkbox" {...register('is_active')} />
                <label htmlFor="is_active" className="label cursor-pointer mb-0">{t('common.active')}</label>
              </div>
            )}
          </div>
        </div>

        {mutation.isError && (
          <div className="mt-4 p-3 bg-danger-light border border-danger rounded-lg text-sm text-danger">
            {mutation.error?.response?.data?.detail || 'An error occurred'}
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">{t('common.cancel')}</button>
          <button id="dealer-save-btn" type="submit" disabled={mutation.isPending} className="btn-primary">
            <Save className="w-4 h-4" />
            {mutation.isPending ? t('common.loading') : t('common.save')}
          </button>
        </div>
      </form>
    </div>
  );
}
