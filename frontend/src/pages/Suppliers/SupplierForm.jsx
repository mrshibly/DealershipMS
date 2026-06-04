/**
 * Supplier Create/Edit form.
 */
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
  name: z.string().min(1, 'Supplier name is required'),
  contact_person: z.string().optional(),
  phone: z.string().regex(BD_PHONE, 'Enter valid BD phone (+880XXXXXXXXXX)').optional().or(z.literal('')),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  address: z.string().optional(),
  district: z.string().optional(),
  vat_no: z.string().optional(),
  bank_name: z.string().optional(),
  bank_account: z.string().optional(),
  opening_balance: z.coerce.number().min(0).default(0),
});

export default function SupplierForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const qc = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ['supplier', id],
    queryFn: async () => { const r = await api.get(`/suppliers/${id}`); return r.data.data; },
    enabled: isEdit,
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { opening_balance: 0 },
  });

  useEffect(() => { if (existing) reset(existing); }, [existing, reset]);

  const mutation = useMutation({
    mutationFn: (data) => isEdit ? api.put(`/suppliers/${id}`, data) : api.post('/suppliers', data),
    onSuccess: () => { qc.invalidateQueries(['suppliers']); navigate('/suppliers'); },
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
        title={isEdit ? t('supplier.edit') : t('supplier.add')}
        action={<button onClick={() => navigate(-1)} className="btn-secondary"><ArrowLeft className="w-4 h-4" />{t('common.cancel')}</button>}
      />
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="font-semibold text-text mb-4">{t('supplier.basic_info')}</h2>
            <Field name="name" label={t('supplier.name')}>
              <input id="name" className={`input ${errors.name ? 'input-error' : ''}`} {...register('name')} />
            </Field>
            <Field name="contact_person" label={t('supplier.contact')}>
              <input id="contact_person" className="input" {...register('contact_person')} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field name="phone" label={t('common.phone')}>
                <input id="phone" className={`input ${errors.phone ? 'input-error' : ''}`} placeholder="+880XXXXXXXXXX" {...register('phone')} />
              </Field>
              <Field name="email" label="Email">
                <input id="email" type="email" className={`input ${errors.email ? 'input-error' : ''}`} {...register('email')} />
              </Field>
            </div>
            <Field name="address" label={t('supplier.address')}>
              <textarea id="address" rows={2} className="input resize-none" {...register('address')} />
            </Field>
            <Field name="district" label={t('supplier.district')}>
              <input id="district" className="input" {...register('district')} />
            </Field>
          </div>

          <div className="card">
            <h2 className="font-semibold text-text mb-4">{t('supplier.financial_info')}</h2>
            <Field name="vat_no" label={t('supplier.vat_no')}>
              <input id="vat_no" className="input" {...register('vat_no')} />
            </Field>
            <Field name="opening_balance" label={`${t('supplier.opening_balance')} (৳)`}>
              <input id="opening_balance" type="number" step="0.01" min="0" className="input" {...register('opening_balance')} />
            </Field>
            <Field name="bank_name" label={t('supplier.bank_name')}>
              <input id="bank_name" className="input" {...register('bank_name')} />
            </Field>
            <Field name="bank_account" label={t('supplier.bank_account')}>
              <input id="bank_account" className="input" {...register('bank_account')} />
            </Field>
          </div>
        </div>

        {mutation.isError && (
          <div className="mt-4 p-3 bg-danger-light border border-danger rounded-lg text-sm text-danger">
            {mutation.error?.response?.data?.detail || 'An error occurred'}
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">{t('common.cancel')}</button>
          <button id="supplier-save-btn" type="submit" disabled={mutation.isPending} className="btn-primary">
            <Save className="w-4 h-4" />
            {mutation.isPending ? t('common.loading') : t('common.save')}
          </button>
        </div>
      </form>
    </div>
  );
}
