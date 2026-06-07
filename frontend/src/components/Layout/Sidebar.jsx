/**
 * Sidebar navigation — white bg, blue active state, collapsible.
 * All labels use t() for i18n.
 */
import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  Package,
  Boxes,
  Truck,
  ShoppingCart,
  Users,
  Store,
  UserCheck,
  MapPin,
  FileText,
  Wallet,
  Banknote,
  Receipt,
  BarChart2,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Package2,
  PackageSearch,
  UserSquare,
  CreditCard,
  Settings as SettingsIcon,
  Target,
  RotateCcw,
  PlusCircle,
  FileEdit,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import api from '../../utils/api';

const NAV_GROUPS = [
  {
    label: 'nav.dashboard',
    items: [{ key: 'dashboard', label: 'nav.dashboard', icon: LayoutDashboard, to: '/dashboard' }],
  },
  {
    label: 'Sales',
    items: [
      { key: 'add-wholesale',      label: 'nav.add_wholesale',          icon: PlusCircle,   to: '/invoices/new' },
      { key: 'invoices',           label: 'nav.wholesale_list',          icon: FileText,     to: '/invoices' },
      { key: 'wholesale-adjust',   label: 'nav.wholesale_adjust_list',   icon: FileEdit,     to: '/invoices/adjustments' },
      { key: 'returns',            label: 'nav.bulk_return',             icon: RotateCcw,    to: '/returns' },
      { key: 'collections',        label: 'nav.due_collection',          icon: Wallet,       to: '/collections' },
      { key: 'targets',            label: 'nav.dsr_target',              icon: Target,       to: '/targets' },
    ],
  },
  {
    label: 'Inventory',
    items: [
      { key: 'products',  label: 'nav.products',  icon: Package,      to: '/products' },
      { key: 'inventory', label: 'nav.inventory', icon: Boxes,        to: '/inventory' },
      { key: 'suppliers', label: 'nav.suppliers', icon: Truck,        to: '/suppliers' },
      { key: 'purchases', label: 'nav.purchases', icon: ShoppingCart, to: '/purchases' },
    ],
  },
  {
    label: 'People',
    items: [
      { key: 'dealers', label: 'nav.dealers', icon: Users,     to: '/dealers' },
      { key: 'shops',   label: 'nav.shops',   icon: Store,     to: '/shops' },
      { key: 'dsrs',    label: 'nav.dsrs',    icon: UserCheck, to: '/dsrs' },
      { key: 'routes',  label: 'nav.routes',  icon: MapPin,    to: '/routes' },
    ],
  },
  {
    label: 'Finance',
    items: [
      { key: 'accounts', label: 'nav.accounts', icon: Banknote, to: '/accounts' },
      { key: 'expenses', label: 'nav.expenses', icon: Receipt,  to: '/expenses' },
    ],
  },
  {
    label: 'nav.reports',
    items: [{ key: 'reports', label: 'nav.reports', icon: BarChart2, to: '/reports' }],
  },
  {
    label: 'nav.settings',
    items: [
      { key: 'settings', label: 'nav.settings', icon: SettingsIcon, to: '/settings' },
    ],
  },
];

export default function Sidebar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { logout: storeLogout, accessToken } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (_) { /* ignore */ }
    storeLogout();
    navigate('/login');
  };

  return (
    <aside
      className={`flex flex-col bg-sidebar border-r border-border transition-all duration-200 ${
        collapsed ? 'w-16' : 'w-60'
      } min-h-screen flex-shrink-0`}
      id="app-sidebar"
    >
      {/* Logo / Brand */}
      <div className="flex items-center gap-3 px-4 py-4 border-b border-border">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
          <Package2 className="w-4 h-4 text-white" />
        </div>
        {!collapsed && (
          <span className="font-bold text-primary text-sm truncate">DMS</span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto text-text-muted hover:text-text transition-colors"
          id="sidebar-collapse-btn"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} className="mb-1">
            {!collapsed && group.items.length > 1 && (
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wider px-2 py-1.5 mt-2">
                {t(group.label, group.label)}
              </p>
            )}
            {group.items.map((item) => (
              <NavLink
                key={item.key}
                to={item.to}
                id={`nav-${item.key}`}
                end
                className={({ isActive }) =>
                  `flex items-center gap-3 px-2 py-2 rounded-lg text-sm font-medium transition-colors group ${
                    isActive
                      ? 'bg-primary-light text-primary'
                      : 'text-text-muted hover:bg-background hover:text-text'
                  }`
                }
                title={collapsed ? t(item.label) : undefined}
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                {!collapsed && <span>{t(item.label)}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Logout */}
      <div className="border-t border-border p-2">
        <button
          onClick={handleLogout}
          id="nav-logout"
          className="flex items-center gap-3 w-full px-2 py-2 rounded-lg text-sm font-medium text-text-muted hover:bg-danger-light hover:text-danger transition-colors"
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {!collapsed && <span>{t('nav.logout')}</span>}
        </button>
      </div>
    </aside>
  );
}
