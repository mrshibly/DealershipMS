# INSTRUCTION.md — DMS Build Agent Guide

> **Project:** Dealership Management System (DMS)  
> **Stack:** Python FastAPI + PostgreSQL + React (Light Theme)  
> **Locale:** Bangladesh (BDT, NBR VAT, bKash/Nagad/Rocket)  
> **PRD Reference:** `DMS_PRD.docx` (read this first before building anything)

---

## 0. Read Before You Begin

1. Read `DMS_PRD.docx` fully before writing a single line of code.
2. Every decision must trace back to a PRD section. If something is ambiguous, default to the conservative/simpler interpretation and leave a `// TODO: clarify` comment.
3. Do **not** add features not in the PRD without a comment explaining why.
4. This is a **Bangladesh-focused** system. Respect locale specifics at all times — BDT currency, dd/mm/yyyy dates, +880 phone format, NBR VAT rules.

---

## 1. Repository Structure

Set up the monorepo as follows:

```
dms/
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── routes/    # One file per module
│   │   ├── core/
│   │   │   ├── config.py      # Settings (Pydantic BaseSettings)
│   │   │   ├── database.py    # Async SQLAlchemy engine + session
│   │   │   └── security.py    # JWT, bcrypt
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic layer (no DB queries in routes)
│   │   └── utils/
│   │       ├── pdf.py         # Invoice & report PDF generation
│   │       ├── barcode.py     # Code128 barcode generation
│   │       └── sms.py         # SMS gateway integration
│   ├── alembic/               # Database migrations
│   ├── tests/                 # pytest tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/              # React SPA
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── store/             # Zustand
│   │   ├── i18n/              # bn.json, en.json, hi.json, ar.json
│   │   └── utils/
│   ├── public/
│   ├── tailwind.config.js
│   └── package.json
└── docker-compose.yml
```

---

## 2. Environment & Dependencies

### Backend `requirements.txt` must include:
```
fastapi>=0.111.0
uvicorn[standard]
sqlalchemy[asyncio]>=2.0
asyncpg
alembic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
python-multipart
reportlab        # PDF generation
python-barcode[images]
celery
redis
pillow
httpx            # For async HTTP calls (SMS gateway)
pytest
pytest-asyncio
httpx            # Test client
```

### Frontend `package.json` key deps:
```json
{
  "react": "^18",
  "react-router-dom": "^6",
  "tailwindcss": "^3",
  "@tanstack/react-query": "^5",
  "zustand": "^4",
  "recharts": "^2",
  "react-i18next": "^14",
  "i18next": "^23",
  "axios": "^1",
  "react-hook-form": "^7",
  "zod": "^3",
  "@hookform/resolvers": "^3",
  "date-fns": "^3",
  "lucide-react": "^0.383"
}
```

---

## 3. Database Rules

- Use **PostgreSQL 15+** — no other DB.
- Use **SQLAlchemy 2.0 async** (`asyncpg` driver).
- Every model must have: `id` (UUID, default gen_random_uuid()), `created_at`, `updated_at`, `created_by` (FK to users), `is_deleted` (bool, default false).
- **No hard deletes** on financial records (invoices, purchases, collections, expenses). Use `is_deleted = True`.
- All monetary values stored as **NUMERIC(15, 2)** — never float.
- Quantities stored as **INTEGER** (pieces). Cartons are derived: `qty_pieces / pcs_per_carton`.
- All migrations via **Alembic** — never modify schema manually.

### Required Indexes:
- `invoices.date`, `invoices.dealer_id`, `invoices.dsr_id`, `invoices.status`
- `products.barcode`, `products.sku`
- `collections.date`, `collections.dsr_id`
- `expenses.date`, `expenses.head_id`

---

## 4. API Rules

- All routes under `/api/v1/`
- All routes require `Authorization: Bearer <token>` except `/api/v1/auth/login`
- Every route must check permissions using a dependency: `require_permission(module="invoices", action="create")`
- Standard response envelope:
  ```json
  { "success": true, "data": {...}, "message": "OK" }
  { "success": false, "error": "Error message", "detail": "..." }
  ```
- Pagination on all list endpoints: `?page=1&per_page=20` → response includes `total`, `page`, `per_page`, `pages`
- Date filters always: `?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
- Never return passwords or password_hash in any response

### Module Route Files:
| File | Prefix |
|------|--------|
| `auth.py` | `/auth` |
| `users.py` | `/users` |
| `roles.py` | `/roles` |
| `dashboard.py` | `/dashboard` |
| `products.py` | `/products` |
| `inventory.py` | `/inventory` |
| `suppliers.py` | `/suppliers` |
| `purchases.py` | `/purchases` |
| `dealers.py` | `/dealers` |
| `shops.py` | `/shops` |
| `dsrs.py` | `/dsrs` |
| `routes_mgmt.py` | `/routes` |
| `invoices.py` | `/invoices` |
| `collections.py` | `/collections` |
| `accounts.py` | `/accounts` |
| `expenses.py` | `/expenses` |
| `contra.py` | `/contra-entries` |
| `reports.py` | `/reports` |
| `settings.py` | `/settings` |
| `targets.py` | `/targets` |
| `returns.py` | `/returns` |

---

## 5. Business Logic Rules (Critical)

### Invoice Creation:
1. Validate all product IDs exist and are active.
2. Check stock availability before confirming. If insufficient stock, return HTTP 422 with which products are short.
3. On confirm: deduct stock atomically in a DB transaction.
4. If payment mode is Cash/bKash/Nagad/Rocket: create a `collection` record immediately with full amount.
5. If Credit: invoice status = `PARTIAL` if partial payment given, `CONFIRMED` (due) if no payment.
6. Invoice number format: `INV-{YYYY}-{5-digit-padded}` e.g. `INV-2026-00042` — sequential, never reuse.

### DSR Ledger Balance:
```
balance_owed = sum(stock_given_value) - sum(sales_collected) - sum(returns_value) + sum(dsr_expenses_approved)
```
This balance is computed at query time, never stored (to prevent drift).

### Stock Calculation:
```
current_stock = opening_stock + purchases_received + sales_returns - confirmed_sales - damages - free_items_given - stock_adjustments_out + stock_adjustments_in
```
Always computed via SUM queries, not stored separately (except for performance caching after Sprint 1 passes load tests).

### VAT Calculation:
- VAT = `(unit_price × qty) × (vat_rate / 100)`
- If product has `vat_applicable = false`, VAT = 0
- Grand Total = Subtotal − Discount + VAT
- Never apply VAT on free items or returned items

### Contra Entry:
- Debit from-account, credit to-account in same DB transaction
- Both account balances updated atomically
- Never allow contra if from-account would go below 0 (configurable — default: warn but allow)

---

## 6. Frontend Rules

### Theme (Light — STRICTLY ENFORCED):
```js
// tailwind.config.js — extend these colours
colors: {
  primary: '#2563EB',     // Blue 600
  'primary-dark': '#1D4ED8',
  surface: '#FFFFFF',
  background: '#F8FAFC',
  border: '#E2E8F0',
  text: '#1E293B',
  'text-muted': '#64748B',
  success: '#16A34A',
  warning: '#D97706',
  danger: '#DC2626',
}
```
- **No dark mode** in v1. Background is always white/light-gray.
- Sidebar: white bg, blue active state, gray icons.
- Tables: white rows, light gray alternating (`#F8FAFC`), blue header row.

### i18n Rules:
- Default language: Bangla (`bn`)
- Use `react-i18next`. Translation keys in `src/i18n/bn.json`, `en.json`, `hi.json`, `ar.json`
- Every visible string must use `t('key')` — no hardcoded English strings in JSX
- Numbers in BDT: `৳{amount.toLocaleString('bn-BD')}` when Bangla is active

### Form Validation:
- All forms use `react-hook-form` + `zod` schema validation
- Phone numbers: validate `^(\+880|0)[0-9]{10}$`
- Amounts: positive numbers only, max 2 decimal places
- Required fields show red border + error message below on blur

### API Calls:
- All API calls via `axios` instance in `src/utils/api.js` with base URL from env
- Use `@tanstack/react-query` for all data fetching — no raw useEffect for API calls
- On 401 response: clear tokens and redirect to `/login`
- On 403: show "You don't have permission" toast — do not crash

---

## 7. Sprint-by-Sprint Build Order

Build in this exact order. Do not skip ahead. Each sprint must pass its tests before the next begins.

### Sprint 0 — Foundation
- [ ] Docker Compose: backend, frontend, postgres, redis services
- [ ] FastAPI app skeleton with health endpoint `GET /health → {"status": "ok"}`
- [ ] Database connection (async SQLAlchemy + asyncpg)
- [ ] Alembic setup + initial migration
- [ ] `users` and `roles` models
- [ ] Auth endpoints: POST /auth/login, POST /auth/refresh, POST /auth/logout
- [ ] JWT middleware dependency
- [ ] RBAC permission dependency
- [ ] React app scaffold with TailwindCSS, routing, i18n setup
- [ ] Login page UI

### Sprint 1 — Products & Inventory
- [ ] `categories`, `products`, `stock_movements` models + migrations
- [ ] CRUD: POST/GET/PUT/DELETE /products
- [ ] Barcode generation endpoint: GET /products/{id}/barcode (returns PNG)
- [ ] Stock: GET /inventory/stock (list with carton/piece breakdown)
- [ ] Opening stock entry: POST /inventory/opening-stock
- [ ] Stock adjustment: POST /inventory/adjustments
- [ ] `suppliers`, `purchases`, `purchase_items` models
- [ ] CRUD: /suppliers, /purchases
- [ ] Frontend: Product list page, product form, stock view page, purchase form

### Sprint 2 — People & Routes
- [ ] `routes`, `dealers`, `shops`, `dsrs` models + migrations
- [ ] CRUD: /routes, /dealers, /shops, /dsrs
- [ ] DSR Ledger endpoint: GET /dsrs/{id}/ledger
- [ ] DSR stock issue: POST /dsrs/{id}/stock-issue
- [ ] DSR stock return: POST /dsrs/{id}/stock-return
- [ ] Frontend: Dealer list, DSR list, DSR ledger view, route management

### Sprint 3 — Invoices & Collections
- [ ] `invoices`, `invoice_items`, `collections` models + migrations
- [ ] POST /invoices (with stock deduction in transaction)
- [ ] GET /invoices (filterable list)
- [ ] GET /invoices/{id} (full detail)
- [ ] POST /invoices/{id}/confirm
- [ ] POST /invoices/{id}/collect (payment collection)
- [ ] POST /invoices/{id}/void
- [ ] PDF generation: GET /invoices/{id}/pdf
- [ ] Frontend: Invoice creation form (multi-line with live totals), invoice list, collection modal

### Sprint 4 — Accounts & Finance
- [ ] `accounts`, `expense_heads`, `expenses`, `contra_entries` models + migrations
- [ ] CRUD: /accounts, /expense-heads, /expenses, /contra-entries
- [ ] Account balance computation endpoint: GET /accounts/{id}/balance
- [ ] Frontend: Account list, expense form, contra entry form

### Sprint 5 — Reports
- [ ] GET /reports/daybook?date=YYYY-MM-DD
- [ ] GET /reports/cashbook?date_from=&date_to=
- [ ] GET /reports/bankbook/{account_id}?date_from=&date_to=
- [ ] GET /reports/sales?date_from=&date_to=&dsr_id=&dealer_id=
- [ ] GET /reports/product-sales?date_from=&date_to=
- [ ] GET /reports/profit?date_from=&date_to= (product-wise and DSR-wise)
- [ ] GET /reports/vat?date_from=&date_to=
- [ ] GET /reports/stock-movement/{product_id}
- [ ] Excel export for all reports (openpyxl)
- [ ] Frontend: Report pages with date filters and export buttons

### Sprint 6 — Dashboard
- [ ] GET /dashboard/snapshot (daily cards)
- [ ] GET /dashboard/analytics?period=monthly|yearly
- [ ] Frontend: Dashboard page with cards and charts (Recharts)

### Sprint 7 — Settings & Automation
- [ ] CRUD /roles with permission JSONB management
- [ ] CRUD /users with role assignment
- [ ] GET/PUT /settings/company
- [ ] GET/PUT /settings/sms
- [ ] SMS service implementation (ssl commerz or configurable)
- [ ] Celery worker for async SMS
- [ ] Frontend: Settings page (tabbed), role editor with permission grid, user management

### Sprint 8 — Additional Features
- [ ] `targets` model + /targets CRUD
- [ ] `returns` model + /returns CRUD
- [ ] DSR target vs actual: GET /dsrs/{id}/targets
- [ ] WhatsApp/SMS receipt on collection confirm (Celery task)
- [ ] Frontend: Target setting UI, returns management page

### Sprint 9 — QA & Deployment
- [ ] Write pytest tests for all service functions (not just routes)
- [ ] Load test dashboard and report endpoints
- [ ] Add DB query optimisation (EXPLAIN ANALYZE on slow queries)
- [ ] Production Docker Compose with nginx, SSL
- [ ] Environment variables documentation
- [ ] Seed data script for demo setup

---

## 8. Testing Requirements

- Minimum **70% code coverage** on backend services layer
- Use `pytest-asyncio` for async tests
- Use `httpx.AsyncClient` as test client
- Each module must have:
  - Happy path test (valid data → expected result)
  - Auth failure test (no token → 401)
  - Permission failure test (wrong role → 403)
  - Validation failure test (bad data → 422)
- Financial calculation tests must be **exact** (use `Decimal` comparison, not float)

---

## 9. Security Checklist

Before any endpoint is marked done, verify:
- [ ] Requires valid JWT
- [ ] Checks permission for the action
- [ ] Validates all input with Pydantic schema
- [ ] Does not expose internal IDs in error messages
- [ ] Financial write operations wrapped in DB transaction
- [ ] No raw SQL string concatenation

---

## 10. Bangladesh-Specific Implementation Notes

| Topic | Implementation |
|-------|---------------|
| Currency | Store as `NUMERIC(15,2)` BDT. Display as `৳1,23,456.00` (BD comma format) |
| VAT | Default 15% (NBR standard). Store `vat_rate` per product. VAT field on invoice PDF |
| Phone | Store with +880 prefix. Validate 11-digit BD mobile numbers |
| Dates | Store as UTC. Display as `dd/mm/yyyy` in UI. Report exports use same format |
| MFS accounts | Type = `MOBILE_BANKING`, sub-type = `bKash` / `Nagad` / `Rocket` / `Upay` |
| Bangla | Use `Hind Siliguri` Google Font for Bangla text in UI. PDF: embed SolaimanLipi |
| SMS | Use SSL Commerz SMS API (primary). Configuration: API key in `.env` |
| Districts | Pre-seed `districts` lookup table with all 64 Bangladesh districts |
| Invoice | Must print VAT BIN number on invoice as required by NBR |

---

## 11. Common Mistakes to Avoid

1. **Float for money** — always `Decimal` in Python, `NUMERIC` in DB, never `float`
2. **Storing derived balance** — compute DSR balance and stock from transactions, don't store
3. **Hard deleting financial records** — use `is_deleted` flag
4. **Blocking endpoints with heavy computation** — put PDF generation and report export in Celery tasks, return job ID immediately
5. **Missing DB transaction** — invoice confirm + stock deduct must be one atomic transaction
6. **Hardcoded strings in frontend** — every string goes through `t()` for i18n
7. **Not paginating list endpoints** — every list must be paginated
8. **VAT on free/returned items** — VAT is zero on these line types

---

## 12. Definition of Done

A feature is **Done** when:
1. Backend endpoint implemented with correct business logic
2. Pydantic schema validates input
3. Permission check applied
4. At least 3 tests pass (happy path, 401, 403)
5. Frontend page/component built and connected to API
6. Bangla translation key added for all new UI strings
7. No console errors or TypeScript warnings
8. Reviewed against relevant PRD section

---

*Built for Bangladesh distribution businesses. Keep it fast, accurate, and honest.*
