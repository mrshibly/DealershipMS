import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Save, ArrowLeft } from 'lucide-react';

export default function UserForm() {
  const { id } = useParams();
  const isEdit = id !== 'new';
  const navigate = useNavigate();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { register, handleSubmit, reset } = useForm();

  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: () => api.get('/roles?is_active=true').then(res => res.data.data),
  });
  const roles = rolesData || [];

  const { data: user } = useQuery({
    queryKey: ['users', id],
    queryFn: () => api.get(`/users/${id}`).then(res => res.data.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (user) {
      reset({
        name: user.name,
        email: user.email,
        phone: user.phone || '',
        language: user.language,
        role_id: user.role_id || '',
        is_active: user.is_active,
      });
    }
  }, [user, reset]);

  const mutation = useMutation({
    mutationFn: (data) => {
      const payload = { ...data };
      if (!payload.password) delete payload.password; // Don't send empty password on edit
      if (!payload.role_id) payload.role_id = null;
      return isEdit ? api.put(`/users/${id}`, payload) : api.post('/users', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      navigate('/settings/users');
    },
  });

  const onSubmit = (data) => {
    mutation.mutate(data);
  };

  return (
    <div className="card max-w-2xl">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/settings/users')} className="p-2 hover:bg-background rounded-full transition-colors">
          <ArrowLeft className="w-5 h-5 text-text-muted" />
        </button>
        <h2 className="text-xl font-bold">{isEdit ? t('settings.edit_user') : t('settings.add_user')}</h2>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="label">{t('common.name')}</label>
          <input {...register('name', { required: true })} className="input" />
        </div>

        <div>
          <label className="label">{t('settings.email')}</label>
          <input type="email" {...register('email', { required: true })} className="input" />
        </div>

        <div>
          <label className="label">{t('settings.password')} {!isEdit && '*'}</label>
          <input 
            type="password" 
            {...register('password', { required: !isEdit })} 
            className="input" 
            placeholder={isEdit ? t('settings.leave_blank_password') : ''}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">{t('settings.phone')}</label>
            <input {...register('phone')} className="input" placeholder="e.g. 017..." />
          </div>
          
          <div>
            <label className="label">{t('settings.role')}</label>
            <select {...register('role_id')} className="input">
              <option value="">{t('common.select')}...</option>
              {roles.map(r => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">{t('settings.language')}</label>
          <select {...register('language')} className="input">
            <option value="bn">বাংলা (Bengali)</option>
            <option value="en">English</option>
          </select>
        </div>

        <div className="flex items-center gap-2 mt-4">
          <input type="checkbox" id="is_active" {...register('is_active')} className="w-4 h-4 text-primary" defaultChecked />
          <label htmlFor="is_active" className="text-sm font-medium">{t('common.active')}</label>
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
