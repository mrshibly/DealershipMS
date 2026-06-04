/**
 * Login page — company logo, email/password form, language switcher.
 * Uses react-hook-form + zod validation.
 * On success → stores tokens in authStore → navigates to /dashboard.
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, Globe, Package } from 'lucide-react';
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
      .min(1, t('login.email_required'))
      .email(t('login.email_invalid')),
    password: z.string().min(1, t('login.password_required')),
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
        t('login.error_generic');
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
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      {/* Language switcher — top right */}
      <div className="fixed top-4 right-4 flex items-center gap-2">
        <Globe className="w-4 h-4 text-text-muted" />
        <div className="flex gap-1">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                i18n.language === lang.code
                  ? 'bg-primary text-white'
                  : 'text-text-muted hover:bg-border'
              }`}
              id={`lang-switch-${lang.code}`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </div>

      <div className="w-full max-w-md">
        {/* Card */}
        <div className="card">
          {/* Logo / Brand */}
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center mb-4 shadow-lg">
              <Package className="w-9 h-9 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-text">{t('login.title')}</h1>
            <p className="text-text-muted text-sm mt-1">{t('login.subtitle')}</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            {/* Email */}
            <div className="mb-4">
              <label htmlFor="email" className="label">
                {t('login.email')}
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder={t('login.email_placeholder')}
                className={`input ${errors.email ? 'input-error' : ''}`}
                {...register('email')}
              />
              {errors.email && (
                <p className="error-msg">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div className="mb-6">
              <label htmlFor="password" className="label">
                {t('login.password')}
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder={t('login.password_placeholder')}
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
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="error-msg">{errors.password.message}</p>
              )}
            </div>

            {/* Server error */}
            {serverError && (
              <div className="mb-4 p-3 bg-danger-light border border-danger rounded-lg text-sm text-danger">
                {serverError}
              </div>
            )}

            {/* Submit */}
            <button
              id="login-submit-btn"
              type="submit"
              disabled={mutation.isPending}
              className="btn-primary w-full py-2.5 text-base"
            >
              {mutation.isPending ? t('login.logging_in') : t('login.submit')}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-text-muted mt-6">
          DMS &copy; {new Date().getFullYear()} — Bangladesh Distribution Management
        </p>
      </div>
    </div>
  );
}
