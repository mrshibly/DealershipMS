import { useForm, useWatch } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Save, ArrowLeft, Search } from 'lucide-react';
import { useState } from 'react';

export default function ReturnForm() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { register, handleSubmit, control } = useForm();
  
  const [invoiceSearch, setInvoiceSearch] = useState('');
  
  const { data: invoices } = useQuery({
    queryKey: ['invoices', { search: invoiceSearch }],
    queryFn: () => api.get('/invoices?per_page=50').then(res => res.data.data.data), // simplified fetch
  });
  
  const selectedInvoiceId = useWatch({ control, name: 'invoice_id' });
  const selectedInvoice = invoices?.find(i => i.id === selectedInvoiceId);

  const mutation = useMutation({
    mutationFn: (data) => api.post('/returns', {
        ...data,
        qty_returned: parseInt(data.qty_returned, 10)
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['returns']);
      navigate('/returns');
    },
    onError: (err) => {
        alert(err.response?.data?.detail || "Failed to process return");
    }
  });

  const onSubmit = (data) => {
    mutation.mutate(data);
  };

  return (
    <div className="card max-w-2xl mx-auto mt-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/returns')} className="p-2 hover:bg-background rounded-full transition-colors">
          <ArrowLeft className="w-5 h-5 text-text-muted" />
        </button>
        <h2 className="text-xl font-bold">{t('common.add_new')}</h2>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="label">Invoice</label>
          <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-text-muted" />
              <select {...register('invoice_id', { required: true })} className="input pl-9">
                <option value="">Search or Select Invoice...</option>
                {invoices?.map(inv => (
                  <option key={inv.id} value={inv.id}>{inv.invoice_no} ({inv.date})</option>
                ))}
              </select>
          </div>
        </div>
        
        {selectedInvoice && (
            <div className="p-4 bg-background rounded-lg text-sm mb-4">
                <p><strong>Shop:</strong> {selectedInvoice.shop?.name}</p>
                <p><strong>DSR:</strong> {selectedInvoice.dsr?.name}</p>
            </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label className="label">Product</label>
                <select {...register('product_id', { required: true })} className="input" disabled={!selectedInvoice}>
                    <option value="">{t('common.select')}...</option>
                    {selectedInvoice?.items?.map(item => (
                        <option key={item.product_id} value={item.product_id}>
                            {item.product?.name_en || 'Product'} (Billed: {item.total_pieces} pcs)
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label className="label">Quantity Returned (Pcs)</label>
                <input type="number" min="1" {...register('qty_returned', { required: true })} className="input" />
            </div>
        </div>
        
        <div>
            <label className="label">Reason / Notes</label>
            <input type="text" {...register('reason')} className="input" placeholder="e.g. Damaged during transit" />
        </div>
        
        <div>
            <label className="label">Return Date</label>
            <input type="date" {...register('return_date', { required: true })} className="input" defaultValue={new Date().toISOString().split('T')[0]} />
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
