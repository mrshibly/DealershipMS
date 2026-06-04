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
  name: z.string().min(1, 'Shop name is required'),
  owner_name: z.string().optional().or(z.literal('')),
  address: z.string().optional().or(z.literal('')),
  shop_type: z.enum(['Retailer', 'Wholesaler'], { errorMap: () => ({ message: 'Shop type must be Retailer or Wholesaler' }) }),
  dealer_id: z.string().uuid('Please select a dealer').nullable().or(z.literal('')),
  is_active: z.boolean().default(true),
});

export default function ShopForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const qc = useQueryClient();

  const { data: dealersData } = useQuery({
    queryKey: ['dealers-lookup'],
    queryFn: async () => {
      const res = await api.get('/dealers?page=1&per_page=100');
      return res.data?.data || [];
    },
  });

  const { data: existing } = useQuery({
    queryKey: ['shop', id],
    queryFn: async () => { const r = await api.get(`/shops/${id}`); return r.data.data; },
    enabled: isEdit,
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { shop_type: 'Retailer', is_active: true },
  });

  useEffect(() => {
    if (existing) {
      reset({
        ...existing,
        dealer_id: existing.dealer_id || '',
      });
    }
  }, [existing, reset]);

  const mutation = useMutation({
    mutationFn: (data) => {
      const payload = {
        ...data,
        dealer_id: data.dealer_id === '' ? null : data.dealer_id,
      };
      return isEdit ? api.put(`/shops/${id}`, payload) : api.post('/shops', payload);
    },
    onSuccess: () => { qc.invalidateQueries(['shops']); navigate('/shops'); },
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
        title={isEdit ? t('shop.edit') : t('shop.add')}
        action={<button onClick={() => navigate(-1)} className="btn-secondary"><ArrowLeft className="w-4 h-4" />{t('common.cancel')}</button>}
      />
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
        <div className="max-w-xl card">
          <Field name="name" label={t('shop.name')}>
            <input id="name" className={`input ${errors.name ? 'input-error' : ''}`} {...register('name')} />
          </Field>
          <Field name="owner_name" label={t('shop.owner')}>
            <input id="owner_name" className={`input ${errors.owner_name ? 'input-error' : ''}`} {...register('owner_name')} />
          </Field>
          <Field name="shop_type" label={t('shop.type')}>
            <select id="shop_type" className={`input ${errors.shop_type ? 'input-error' : ''}`} {...register('shop_type')}>
              <option value="Retailer">Retailer</option>
              <option value="Wholesaler">Wholesaler</option>
            </select>
          </Field>
          <Field name="dealer_id" label={t('shop.dealer')}>
            <select id="dealer_id" className={`input ${errors.dealer_id ? 'input-error' : ''}`} {...register('dealer_id')}>
              <option value="">-- select dealer --</option>
              {(dealersData || []).map((d) => (
                <option key={d.id} value={d.id}>{d.name} ({d.phone})</option>
              ))}
            </select>
          </Field>
          <Field name="address" label={t('shop.address')}>
            <textarea id="address" rows={2} className="input resize-none" {...register('address')} />
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
            <button id="shop-save-btn" type="submit" disabled={mutation.isPending} className="btn-primary">
              <Save className="w-4 h-4" />
              {mutation.isPending ? t('common.loading') : t('common.save')}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
