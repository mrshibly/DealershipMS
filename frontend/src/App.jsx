/**
 * App.jsx — React Router v6 root.
 * Sets up QueryClient, i18n, and routing.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './i18n/index.js';

import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/Layout/AppLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

// Sprint 1 pages
import ProductList from './pages/Products/ProductList';
import ProductForm from './pages/Products/ProductForm';
import StockView from './pages/Inventory/StockView';
import SupplierList from './pages/Suppliers/SupplierList';
import SupplierForm from './pages/Suppliers/SupplierForm';
import PurchaseList from './pages/Purchases/PurchaseList';
import PurchaseForm from './pages/Purchases/PurchaseForm';

// Sprint 2 pages
import RouteList from './pages/Routes/RouteList';
import RouteForm from './pages/Routes/RouteForm';
import DealerList from './pages/Dealers/DealerList';
import DealerForm from './pages/Dealers/DealerForm';
import DSRList from './pages/DSRs/DSRList';
import DSRForm from './pages/DSRs/DSRForm';
import DSRLedger from './pages/DSRs/DSRLedger';
import ShopList from './pages/Shops/ShopList';
import ShopForm from './pages/Shops/ShopForm';
import BarcodePrint from './pages/Products/BarcodePrint';

// Sprint 3 pages
import InvoiceList from './pages/Invoices/InvoiceList';
import InvoiceForm from './pages/Invoices/InvoiceForm';
import InvoiceDetail from './pages/Invoices/InvoiceDetail';

// Sprint 4 pages
import AccountList from './pages/Accounts/AccountList';
import AccountForm from './pages/Accounts/AccountForm';
import ContraEntryForm from './pages/Accounts/ContraEntryForm';
import ExpenseList from './pages/Expenses/ExpenseList';
import ExpenseForm from './pages/Expenses/ExpenseForm';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
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
              <Route path="/invoices/:id"     element={<InvoiceDetail />} />

              {/* Sprint 4 — Accounts & Finance */}
              <Route path="/accounts"         element={<AccountList />} />
              <Route path="/accounts/new"     element={<AccountForm />} />
              <Route path="/accounts/contra"  element={<ContraEntryForm />} />
              <Route path="/accounts/:id/edit" element={<AccountForm />} />
              
              <Route path="/expenses"         element={<ExpenseList />} />
              <Route path="/expenses/new"     element={<ExpenseForm />} />

              {/* Placeholder routes for upcoming modules */}
              <Route path="/collections" element={<ComingSoon module="Collections" />} />
              <Route path="/reports"     element={<ComingSoon module="Reports" />} />
              <Route path="/settings"    element={<ComingSoon module="Settings" />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function ComingSoon({ module }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <div className="text-4xl">🚧</div>
      <h2 className="text-xl font-semibold text-text">{module}</h2>
      <p className="text-text-muted text-sm">Coming in a future sprint</p>
    </div>
  );
}
