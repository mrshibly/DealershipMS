import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, Globe, Package, CheckCircle2, ArrowRight, TrendingUp, DollarSign, Activity } from 'lucide-react';
import api from '../utils/api';
import { useAuthStore } from '../store/authStore';

const LANGUAGES = [
  { code: 'bn', label: 'বাংলা' },
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'ar', label: 'عربي' },
];

export default function Login() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { login: storeLogin } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState('');

  const schema = z.object({
    email: z
      .string()
      .min(1, t('login.email_required') || 'Email is required')
      .email(t('login.email_invalid') || 'Invalid email'),
    password: z.string().min(1, t('login.password_required') || 'Password is required'),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: async (data) => {
      const res = await api.post('/auth/login', data);
      return res.data;
    },
    onSuccess: (res) => {
      const { access_token, refresh_token } = res.data;
      storeLogin({ access_token, refresh_token });
      navigate('/dashboard');
    },
    onError: (err) => {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        t('login.error_generic') ||
        'Login failed';
      setServerError(msg);
    },
  });

  const onSubmit = (data) => {
    setServerError('');
    mutation.mutate(data);
  };

  const changeLanguage = (code) => {
    i18n.changeLanguage(code);
    localStorage.setItem('dms-lang', code);
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      
      {/* Dynamic Keyframes Styling for animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-12px); }
        }
        @keyframes float-delayed {
          0%, 100% { transform: translateY(0px) scale(0.98); }
          50% { transform: translateY(12px) scale(1); }
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.35; transform: scale(1); }
          50% { opacity: 0.55; transform: scale(1.08); }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        .animate-float-delayed {
          animation: float-delayed 8s ease-in-out infinite;
        }
        .animate-pulse-slow {
          animation: pulse-slow 12s ease-in-out infinite;
        }
      `}</style>

      {/* Left Column: Landing / Hero Section */}
      <div className="hidden md:flex md:w-1/2 lg:w-3/5 bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-900 text-white p-12 lg:p-16 flex-col justify-between relative overflow-hidden">
        
        {/* Glow Effects */}
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-blue-500/10 blur-[120px] animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[100px] animate-pulse-slow"></div>

        {/* Top Header */}
        <div className="flex items-center gap-3.5 z-10">
          <div className="w-11 h-11 bg-white/10 backdrop-blur-md border border-white/25 rounded-2xl flex items-center justify-center shadow-inner">
            <Package className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <span className="text-xl font-black text-white">Dealership Management System</span>
          </div>
        </div>

        {/* Core Presentation Content */}
        <div className="my-auto space-y-10 z-10 max-w-xl">
          <div className="space-y-4">
            <h1 className="text-4xl lg:text-5xl font-extrabold leading-tight">
              Smart Distribution &amp; <span className="bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">Inventory System</span>
            </h1>
            <p className="text-slate-300/90 text-base lg:text-lg font-normal leading-relaxed">
              Simplify distribution workflow, sales monitoring, automatic stock tracking, and complete accounts reconciliation across Bangladesh.
            </p>
          </div>

          {/* Key Value Highlights */}
          <div className="space-y-6">
            <div className="flex items-start gap-3.5">
              <div className="p-1 mt-0.5 bg-emerald-500/10 rounded-lg text-emerald-400 border border-emerald-400/20">
                <CheckCircle2 className="w-4.5 h-4.5" />
              </div>
              <div>
                <h4 className="font-semibold text-slate-150 text-sm">Real-Time Financial Dashboard</h4>
                <p className="text-xs text-slate-400">Instantly evaluate net sales, purchase, P&amp;L, and account cash balances.</p>
              </div>
            </div>

            <div className="flex items-start gap-3.5">
              <div className="p-1 mt-0.5 bg-amber-500/10 rounded-lg text-amber-400 border border-amber-400/20">
                <CheckCircle2 className="w-4.5 h-4.5" />
              </div>
              <div>
                <h4 className="font-semibold text-slate-150 text-sm">Dynamic Threshold Alerts</h4>
                <p className="text-xs text-slate-400">Keep inventory levels optimized with automatic low-stock notifications.</p>
              </div>
            </div>

            <div className="flex items-start gap-3.5">
              <div className="p-1 mt-0.5 bg-blue-500/10 rounded-lg text-blue-400 border border-blue-400/20">
                <CheckCircle2 className="w-4.5 h-4.5" />
              </div>
              <div>
                <h4 className="font-semibold text-slate-150 text-sm">Digital PDF &amp; Barcode Sheets</h4>
                <p className="text-xs text-slate-400">Generate, download, and print product barcode templates and customer invoices.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Floating Animated Widget Mockups */}
        <div className="absolute bottom-12 right-12 hidden lg:flex flex-col gap-4 z-10 pointer-events-none">
          {/* Mockup 1 */}
          <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 p-4 rounded-2xl w-60 shadow-2xl animate-float">
            <div className="flex justify-between items-center mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-semibold text-slate-300">Sales Trend</span>
              </div>
              <span className="text-[10px] bg-emerald-400/10 text-emerald-400 px-1.5 py-0.5 rounded">Active</span>
            </div>
            <div className="text-xl font-extrabold text-white">৳ 7,53,450</div>
            <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-emerald-400" />
              <span>+18.4% vs target</span>
            </div>
          </div>

          {/* Mockup 2 */}
          <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 p-4 rounded-2xl w-52 shadow-2xl animate-float-delayed self-end">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-semibold text-slate-300">Net Profit</span>
            </div>
            <div className="text-lg font-bold text-indigo-300">৳ 96,180</div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-indigo-400 h-full rounded-full" style={{ width: '78%' }}></div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="z-10 text-xs text-slate-400 flex justify-between items-center">
          <span>
            DMS &copy; {new Date().getFullYear()} — Built by{' '}
            <a href="https://setuops.xyz" target="_blank" rel="noopener noreferrer" className="underline hover:text-white transition-colors">
              SETU Ops
            </a>
          </span>
        </div>
      </div>

      {/* Right Column: Login Card Section */}
      <div className="w-full md:w-1/2 lg:w-2/5 flex items-center justify-center p-8 relative">
        
        {/* Language switcher — top right */}
        <div className="absolute top-4 right-4 flex items-center gap-1.5 bg-white shadow-sm border border-border px-3 py-1.5 rounded-full z-20">
          <Globe className="w-3.5 h-3.5 text-text-muted" />
          <div className="flex gap-0.5">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => changeLanguage(lang.code)}
                className={`px-2 py-0.5 text-[10px] font-bold rounded-full transition-colors ${
                  i18n.language === lang.code
                    ? 'bg-primary text-white'
                    : 'text-text-muted hover:bg-background'
                }`}
                id={`lang-switch-${lang.code}`}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>

        <div className="w-full max-w-md space-y-6">
          {/* Card Wrapper */}
          <div className="bg-white rounded-2xl border border-border shadow-card p-8 lg:p-10 relative">
            
            {/* Logo / Brand (Visible on mobile) */}
            <div className="flex flex-col items-center mb-8 text-center">
              <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center mb-4 md:hidden">
                <Package className="w-7 h-7 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-text">{t('login.title') || 'Welcome Back'}</h2>
              <p className="text-text-muted text-sm mt-1">{t('login.subtitle') || 'Access your DMS dashboard'}</p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              
              {/* Email */}
              <div>
                <label htmlFor="email" className="label">
                  {t('login.email') || 'Email Address'}
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder={t('login.email_placeholder') || 'Enter your email'}
                  className={`input ${errors.email ? 'input-error' : ''}`}
                  {...register('email')}
                />
                {errors.email && (
                  <p className="error-msg">{errors.email.message}</p>
                )}
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="label">
                  {t('login.password') || 'Password'}
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder={t('login.password_placeholder') || 'Enter your password'}
                    className={`input pr-10 ${errors.password ? 'input-error' : ''}`}
                    {...register('password')}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
                    id="toggle-password-visibility"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="error-msg">{errors.password.message}</p>
                )}
              </div>

              {/* Server error */}
              {serverError && (
                <div className="p-3 bg-danger-light border border-danger rounded-lg text-sm text-danger animate-pulse">
                  {serverError}
                </div>
              )}

              {/* Submit */}
              <button
                id="login-submit-btn"
                type="submit"
                disabled={mutation.isPending}
                className="btn-primary w-full py-3 text-sm font-semibold mt-2 shadow-lg shadow-primary/25 hover:shadow-primary/35 transition-all"
              >
                {mutation.isPending ? t('login.logging_in') || 'Authenticating...' : t('login.submit') || 'Login to Dashboard'}
              </button>
            </form>
          </div>

          {/* Footer info for mobile */}
          <p className="text-center text-[10px] text-text-muted md:hidden">
            DMS &copy; {new Date().getFullYear()} — Built by{' '}
            <a href="https://setuops.xyz" target="_blank" rel="noopener noreferrer" className="underline hover:text-primary transition-colors">
              SETU Ops
            </a>
          </p>
        </div>
      </div>

    </div>
  );
}
