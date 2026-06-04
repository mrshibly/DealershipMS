/**
 * Top navigation bar — page title, user info, language switcher.
 */
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { Globe, User } from 'lucide-react';

const LANGUAGES = [
  { code: 'bn', label: 'বাং' },
  { code: 'en', label: 'EN' },
  { code: 'hi', label: 'हि' },
  { code: 'ar', label: 'ع' },
];

export default function Topbar({ title }) {
  const { t, i18n } = useTranslation();
  const { user } = useAuthStore();

  const changeLanguage = (code) => {
    i18n.changeLanguage(code);
    localStorage.setItem('dms-lang', code);
  };

  return (
    <header className="h-14 flex items-center justify-between px-6 bg-surface border-b border-border flex-shrink-0">
      {/* Page title */}
      <h2 className="font-semibold text-text text-base">{title}</h2>

      <div className="flex items-center gap-4">
        {/* Language switcher */}
        <div className="flex items-center gap-1" id="topbar-lang-switcher">
          <Globe className="w-3.5 h-3.5 text-text-muted" />
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`px-1.5 py-0.5 text-xs rounded transition-colors ${
                i18n.language === lang.code
                  ? 'bg-primary text-white'
                  : 'text-text-muted hover:bg-border'
              }`}
              id={`topbar-lang-${lang.code}`}
            >
              {lang.label}
            </button>
          ))}
        </div>

        {/* User info */}
        <div className="flex items-center gap-2 text-sm text-text" id="topbar-user">
          <div className="w-8 h-8 rounded-full bg-primary-light flex items-center justify-center">
            <User className="w-4 h-4 text-primary" />
          </div>
          <span className="font-medium hidden sm:block">{user?.name || 'Admin'}</span>
        </div>
      </div>
    </header>
  );
}
