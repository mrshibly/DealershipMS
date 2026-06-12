/**
 * App.jsx — React Router v6 root.
 * Sets up QueryClient, i18n, and routing.
 */
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './i18n/index.js';

import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/Layout/AppLayout';
import Spinner from './components/ui';

// Lazy load all page components for code-splitting
const Login = lazy(() => import('./pages/Login'));
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'));

// Sprint 1 pages
const ProductList = lazy(() => import('./pages/Products/ProductList'));
const ProductForm = lazy(() => import('./pages/Products/ProductForm'));
const StockView = lazy(() => import('./pages/Inventory/StockView'));
const SupplierList = lazy(() => import('./pages/Suppliers/SupplierList'));
const SupplierForm = lazy(() => import('./pages/Suppliers/SupplierForm'));
const PurchaseList = lazy(() => import('./pages/Purchases/PurchaseList'));
const PurchaseForm = lazy(() => import('./pages/Purchases/PurchaseForm'));
const PurchaseReturnList = lazy(() => import('./pages/Purchases/PurchaseReturnList'));
const PurchaseReturnForm = lazy(() => import('./pages/Purchases/PurchaseReturnForm'));
const SupplierPaymentList = lazy(() => import('./pages/Purchases/SupplierPaymentList'));

// Sprint 2 pages
const RouteList = lazy(() => import('./pages/Routes/RouteList'));
const RouteForm = lazy(() => import('./pages/Routes/RouteForm'));
const DealerList = lazy(() => import('./pages/Dealers/DealerList'));
const DealerForm = lazy(() => import('./pages/Dealers/DealerForm'));
const DSRList = lazy(() => import('./pages/DSRs/DSRList'));
const DSRForm = lazy(() => import('./pages/DSRs/DSRForm'));
const DSRLedger = lazy(() => import('./pages/DSRs/DSRLedger'));
const ShopList = lazy(() => import('./pages/Shops/ShopList'));
const ShopForm = lazy(() => import('./pages/Shops/ShopForm'));
const BarcodePrint = lazy(() => import('./pages/Products/BarcodePrint'));

// Sprint 3 pages
const InvoiceList = lazy(() => import('./pages/Invoices/InvoiceList'));
const InvoiceForm = lazy(() => import('./pages/Invoices/InvoiceForm'));
const InvoiceDetail = lazy(() => import('./pages/Invoices/InvoiceDetail'));
const WholesaleAdjustList = lazy(() => import('./pages/Invoices/WholesaleAdjustList'));
const CollectionList = lazy(() => import('./pages/Collections/CollectionList'));

// Sprint 4 pages
const AccountList = lazy(() => import('./pages/Accounts/AccountList'));
const AccountForm = lazy(() => import('./pages/Accounts/AccountForm'));
const ContraEntryForm = lazy(() => import('./pages/Accounts/ContraEntryForm'));
const ExpenseList = lazy(() => import('./pages/Expenses/ExpenseList'));
const ExpenseForm = lazy(() => import('./pages/Expenses/ExpenseForm'));

// Sprint 5 pages
const ReportDashboard = lazy(() => import('./pages/Reports/ReportDashboard'));
const DaybookReport = lazy(() => import('./pages/Reports/DaybookReport'));
const SalesProfitReport = lazy(() => import('./pages/Reports/SalesProfitReport'));
const StockMovementReport = lazy(() => import('./pages/Reports/StockMovementReport'));

// Sprint 7 pages
const SettingsLayout = lazy(() => import('./pages/Settings/SettingsLayout'));
const CompanySettings = lazy(() => import('./pages/Settings/CompanySettings'));
const SmsSettings = lazy(() => import('./pages/Settings/SmsSettings'));
const RoleList = lazy(() => import('./pages/Settings/RoleList'));
const RoleForm = lazy(() => import('./pages/Settings/RoleForm'));
const UserList = lazy(() => import('./pages/Settings/UserList'));
const UserForm = lazy(() => import('./pages/Settings/UserForm'));

// Sprint 8 pages
const TargetList = lazy(() => import('./pages/Targets/TargetList'));
const TargetForm = lazy(() => import('./pages/Targets/TargetForm'));
const ReturnList = lazy(() => import('./pages/Returns/ReturnList'));
const ReturnForm = lazy(() => import('./pages/Returns/ReturnForm'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[400px] w-full">
      <Spinner size="lg" />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<Login />} />

            {/* Protected */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />

                {/* Sprint 1 — Products & Inventory */}
                <Route path="/products"         element={<ProductList />} />
                <Route path="/products/new"     element={<ProductForm />} />
                <Route path="/products/:id/edit" element={<ProductForm />} />
                <Route path="/inventory"        element={<StockView />} />
                <Route path="/suppliers"        element={<SupplierList />} />
                <Route path="/suppliers/new"    element={<SupplierForm />} />
                <Route path="/suppliers/:id/edit" element={<SupplierForm />} />
                <Route path="/purchases"        element={<PurchaseList />} />
                <Route path="/purchases/new"    element={<PurchaseForm />} />
                <Route path="/purchases/returns"      element={<PurchaseReturnList />} />
                <Route path="/purchases/returns/new"  element={<PurchaseReturnForm />} />
                <Route path="/purchases/payments"     element={<SupplierPaymentList />} />

                {/* Sprint 2 — People & Routes */}
                <Route path="/dealers"          element={<DealerList />} />
                <Route path="/dealers/new"      element={<DealerForm />} />
                <Route path="/dealers/:id/edit"  element={<DealerForm />} />
                <Route path="/shops"            element={<ShopList />} />
                <Route path="/shops/new"        element={<ShopForm />} />
                <Route path="/shops/:id/edit"    element={<ShopForm />} />
                <Route path="/dsrs"             element={<DSRList />} />
                <Route path="/dsrs/new"         element={<DSRForm />} />
                <Route path="/dsrs/:id/edit"     element={<DSRForm />} />
                <Route path="/dsrs/:id/ledger"   element={<DSRLedger />} />
                <Route path="/routes"           element={<RouteList />} />
                <Route path="/routes/new"       element={<RouteForm />} />
                <Route path="/routes/:id/edit"   element={<RouteForm />} />
                <Route path="/barcodes"         element={<BarcodePrint />} />

                {/* Sprint 3 — Invoices & Collections */}
                <Route path="/invoices"         element={<InvoiceList />} />
                <Route path="/invoices/new"     element={<InvoiceForm />} />
                <Route path="/invoices/adjustments" element={<WholesaleAdjustList />} />
                <Route path="/invoices/:id/edit" element={<InvoiceForm />} />
                <Route path="/invoices/:id"     element={<InvoiceDetail />} />

                {/* Sprint 4 — Accounts & Finance */}
                <Route path="/accounts"         element={<AccountList />} />
                <Route path="/accounts/new"     element={<AccountForm />} />
                <Route path="/accounts/contra"  element={<ContraEntryForm />} />
                <Route path="/accounts/:id/edit" element={<AccountForm />} />
                
                <Route path="/expenses"         element={<ExpenseList />} />
                <Route path="/expenses/new"     element={<ExpenseForm />} />

                {/* Sprint 5 — Reports */}
                <Route path="/reports"                 element={<ReportDashboard />} />
                <Route path="/reports/daybook"         element={<DaybookReport />} />
                <Route path="/reports/sales-profit"    element={<SalesProfitReport />} />
                <Route path="/reports/stock-movement"  element={<StockMovementReport />} />

                {/* Sprint 3 — Collections */}
                <Route path="/collections" element={<CollectionList />} />
                
                {/* Sprint 8 — Targets & Returns */}
                <Route path="/targets" element={<TargetList />} />
                <Route path="/targets/new" element={<TargetForm />} />
                <Route path="/targets/:id" element={<TargetForm />} />
                
                <Route path="/returns" element={<ReturnList />} />
                <Route path="/returns/new" element={<ReturnForm />} />
                <Route path="/returns/:id" element={<ReturnForm />} />

                {/* Sprint 7 — Settings */}
                <Route path="/settings" element={<SettingsLayout />}>
                  <Route index element={<CompanySettings />} />
                  <Route path="company" element={<CompanySettings />} />
                  <Route path="sms" element={<SmsSettings />} />
                  <Route path="roles" element={<RoleList />} />
                  <Route path="roles/:id" element={<RoleForm />} />
                  <Route path="users" element={<UserList />} />
                  <Route path="users/:id" element={<UserForm />} />
                </Route>
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
