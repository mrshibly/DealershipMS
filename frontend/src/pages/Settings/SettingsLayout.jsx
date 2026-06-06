import { Outlet, NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Building2, MessageSquare, Shield, Users } from 'lucide-react';
import { PageHeader } from '../../components/ui/index.jsx';

export default function SettingsLayout() {
  const { t } = useTranslation();

  const navItems = [
    { to: '/settings/company', icon: <Building2 className="w-5 h-5" />, label: t('settings.company') },
    { to: '/settings/sms', icon: <MessageSquare className="w-5 h-5" />, label: t('settings.sms') },
    { to: '/settings/roles', icon: <Shield className="w-5 h-5" />, label: t('settings.roles') },
    { to: '/settings/users', icon: <Users className="w-5 h-5" />, label: t('settings.users') },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.settings')}
        subtitle={t('settings.subtitle')}
      />

      <div className="flex flex-col lg:flex-row gap-6 mt-6">
        {/* Sidebar Nav */}
        <div className="w-full lg:w-64 flex-shrink-0">
          <nav className="card p-2 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-muted hover:bg-background hover:text-text'
                  }`
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Content Area */}
        <div className="flex-1">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
