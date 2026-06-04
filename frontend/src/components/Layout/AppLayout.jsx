/**
 * AppLayout — wraps all authenticated pages.
 * Sidebar + Topbar + main content area.
 */
import { Outlet, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { useEffect, useState } from 'react';

// Map route paths to translated page titles
const PAGE_TITLES = {
  '/dashboard':   'nav.dashboard',
  '/products':    'nav.products',
  '/inventory':   'nav.inventory',
  '/suppliers':   'nav.suppliers',
  '/purchases':   'nav.purchases',
  '/dealers':     'nav.dealers',
  '/shops':       'nav.shops',
  '/dsrs':        'nav.dsrs',
  '/routes':      'nav.routes',
  '/invoices':    'nav.invoices',
  '/collections': 'nav.collections',
  '/accounts':    'nav.accounts',
  '/expenses':    'nav.expenses',
  '/reports':     'nav.reports',
  '/settings':    'nav.settings',
};

export default function AppLayout() {
  const { t } = useTranslation();
  const location = useLocation();
  const [toast, setToast] = useState(null);

  const titleKey = PAGE_TITLES[location.pathname] || 'nav.dashboard';

  // Listen for 403 forbidden events from api.js interceptor
  useEffect(() => {
    const handler = (e) => {
      setToast({ type: 'danger', message: e.detail || t('permission_denied') });
      setTimeout(() => setToast(null), 4000);
    };
    window.addEventListener('dms:forbidden', handler);
    return () => window.removeEventListener('dms:forbidden', handler);
  }, [t]);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0">
        <Topbar title={t(titleKey)} />

        {/* Toast notification */}
        {toast && (
          <div
            className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
              toast.type === 'danger'
                ? 'bg-danger text-white'
                : 'bg-success text-white'
            }`}
            id="app-toast"
          >
            {toast.message}
          </div>
        )}

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
