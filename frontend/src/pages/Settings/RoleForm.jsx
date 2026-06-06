import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Save, ArrowLeft } from 'lucide-react';

const MODULES = [
  'dashboard', 'products', 'inventory', 'suppliers', 'purchases',
  'dealers', 'shops', 'dsrs', 'routes', 'invoices', 'collections',
  'accounts', 'expenses', 'contra', 'reports', 'settings',
  'targets', 'returns', 'users', 'roles'
];

const DEFAULT_PERMISSIONS = MODULES.reduce((acc, module) => {
  acc[module] = { view: false, create: false, update: false, delete: false };
  return acc;
}, {});

export default function RoleForm() {
  const { id } = useParams();
  const isEdit = id !== 'new';
  const navigate = useNavigate();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { register, handleSubmit, reset } = useForm();
  
  const [permissions, setPermissions] = useState(DEFAULT_PERMISSIONS);

  const { data: role } = useQuery({
    queryKey: ['roles', id],
    queryFn: () => api.get(`/roles/${id}`).then(res => res.data.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (role) {
      reset({ name: role.name, is_active: role.is_active });
      setPermissions({ ...DEFAULT_PERMISSIONS, ...role.permissions });
    }
  }, [role, reset]);

  const mutation = useMutation({
    mutationFn: (data) => {
      const payload = { ...data, permissions };
      return isEdit ? api.put(`/roles/${id}`, payload) : api.post('/roles', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['roles']);
      navigate('/settings/roles');
    },
  });

  const togglePermission = (module, action) => {
    setPermissions(prev => ({
      ...prev,
      [module]: {
        ...prev[module],
        [action]: !prev[module]?.[action]
      }
    }));
  };

  const onSubmit = (data) => {
    mutation.mutate(data);
  };

  return (
    <div className="card">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/settings/roles')} className="p-2 hover:bg-background rounded-full transition-colors">
          <ArrowLeft className="w-5 h-5 text-text-muted" />
        </button>
        <h2 className="text-xl font-bold">{isEdit ? t('settings.edit_role') : t('settings.add_role')}</h2>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl">
          <div>
            <label className="label">{t('settings.role_name')}</label>
            <input {...register('name', { required: true })} className="input" placeholder="e.g. Sales Manager" />
          </div>
          <div className="flex items-center gap-2 mt-8">
            <input type="checkbox" id="is_active" {...register('is_active')} className="w-4 h-4 text-primary" defaultChecked />
            <label htmlFor="is_active" className="text-sm font-medium">{t('common.active')}</label>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-bold mb-4">{t('settings.permissions')}</h3>
          <div className="overflow-x-auto border border-border rounded-xl">
            <table className="w-full text-left text-sm">
              <thead className="bg-background text-text-muted border-b border-border">
                <tr>
                  <th className="p-4 font-medium">{t('settings.module')}</th>
                  <th className="p-4 font-medium text-center">{t('common.view')}</th>
                  <th className="p-4 font-medium text-center">{t('common.create')}</th>
                  <th className="p-4 font-medium text-center">{t('common.update')}</th>
                  <th className="p-4 font-medium text-center">{t('common.delete')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {MODULES.map(module => (
                  <tr key={module} className="hover:bg-background/50 transition-colors">
                    <td className="p-4 font-medium capitalize">{module}</td>
                    {['view', 'create', 'update', 'delete'].map(action => (
                      <td key={`${module}-${action}`} className="p-4 text-center">
                        <input 
                          type="checkbox" 
                          className="w-4 h-4 text-primary rounded border-border focus:ring-primary"
                          checked={permissions[module]?.[action] || false}
                          onChange={() => togglePermission(module, action)}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
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
