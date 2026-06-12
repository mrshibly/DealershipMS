# 🏪 DMS — Dealership Management System

> A full-stack, production-ready Dealership Management System built for Bangladesh-based distribution businesses.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Overview

DMS is a comprehensive management platform for multi-route, multi-dealer distribution businesses in Bangladesh. It handles the full distribution lifecycle — from supplier purchases and inventory tracking, through dealer/shop/DSR management, to sales invoicing, collections, and financial reporting.

**Key design constraints:**
- 🇧🇩 Bangladesh-first: BDT currency, `dd/mm/yyyy` dates, BD mobile validation, Bangla UI default
- 💰 Strict financial accuracy: `NUMERIC(15,2)` in PostgreSQL, Python `Decimal` throughout — never `float`
- 🔒 JWT + RBAC on every endpoint
- 🗂️ Soft deletes on all financial records (`is_deleted = True`)
- ⚛️ Atomic DB transactions for all write operations

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **Database** | PostgreSQL 15 |
| **Cache / Queue** | Redis 7, Celery |
| **Frontend** | React 19, Vite, TailwindCSS 3, Zustand, React Query |
| **Auth** | JWT (HS256), bcrypt |
| **Containerization** | Docker, Docker Compose |
| **i18n** | react-i18next (Bangla default, English, Hindi, Arabic) |

---

## ✅ Sprint Progress

| Sprint | Module | Status |
|--------|--------|--------|
| S0 | Foundation — Auth, RBAC, Docker, DB setup | ✅ Complete |
| S1 | Products, Inventory, Suppliers, Purchases | ✅ Complete |
| S2 | Routes, Dealers, Shops, DSRs | ✅ Complete |
| S3 | Invoices & Collections | ✅ Complete |
| S4 | Accounts & Finance | ✅ Complete |
| S5 | Reports & Analytics | ✅ Complete |
| S6 | Dashboard Charts | ✅ Complete |
| S7 | Settings & SMS Automation | ✅ Complete |
| S8 | DSR Targets & Returns | ✅ Complete |
| S9 | QA & Production Deployment (Nginx + Locust) | ✅ Complete |

---

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/dms-bd.git
cd dms-bd
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values (at minimum, change `SECRET_KEY` and `POSTGRES_PASSWORD`).

### 3. Start all services

```bash
docker compose up -d --build
```

This starts:
- `dms_postgres` — PostgreSQL 15 on host port **5433**
- `dms_redis` — Redis 7 on host port **6378**
- `dms_backend` — FastAPI on host port **8001**
- `dms_frontend` — Vite dev server on host port **5173**

### 4. Seed the database

```bash
docker compose exec backend python seed.py
```

This creates the default roles and the super-administrator account.

### 5. Open the app

| Service | URL |
|---------|-----|
| Frontend UI | http://localhost:5173 |
| API Docs (Swagger) | http://localhost:8001/api/v1/docs |
| API Redoc | http://localhost:8001/api/v1/redoc |

**Default admin credentials:**
```
Email:    admin@dms.local
Password: Admin@1234
```
> ⚠️ Change these immediately in production.

---

## 📁 Project Structure

```
dms-bd/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/      # FastAPI route handlers (thin layer)
│   │   ├── core/               # Config, security, database session
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic layer
│   ├── alembic/                # Database migrations
│   ├── seed.py                 # Initial data seeder
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page-level components (one per route)
│   │   ├── store/              # Zustand state stores
│   │   ├── utils/              # API client, helpers
│   │   └── i18n/               # Translation files (bn, en, hi, ar)
│   ├── public/
│   └── Dockerfile
├── .env                        # Root environment file (gitignored)
├── .env.example                # Template — safe to commit
└── docker-compose.yml
```

---

## 🔌 API Overview

All endpoints are prefixed with `/api/v1`. Full interactive docs at `/api/v1/docs`.

| Resource | Endpoints |
|----------|-----------|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| Categories | `GET/POST /categories`, `GET/PUT/DELETE /categories/{id}` |
| Products | `GET/POST /products`, `GET/PUT/DELETE /products/{id}` |
| Inventory | `GET /inventory`, `POST /inventory/adjust` |
| Suppliers | `GET/POST /suppliers`, `GET/PUT/DELETE /suppliers/{id}` |
| Purchases | `GET/POST /purchases`, `GET /purchases/{id}` |
| Routes | `GET/POST /routes`, `GET/PUT/DELETE /routes/{id}` |
| Dealers | `GET/POST /dealers`, `GET/PUT/DELETE /dealers/{id}` |
| DSRs | `GET/POST /dsrs`, `GET/PUT/DELETE /dsrs/{id}` |
| Shops | `GET/POST /shops`, `GET/PUT/DELETE /shops/{id}` |
| Invoices | `GET/POST /invoices`, `GET/PUT /invoices/{id}`, `POST /invoices/{id}/confirm`, `POST /invoices/{id}/void`, `GET /invoices/{id}/pdf` |
| Collections | `GET/POST /collections` |
| Returns | `POST /returns` |
| Accounts | `GET/POST /accounts`, `GET /accounts/{id}/ledger` |

---

## 🛡️ Architecture Decisions

### Financial Precision
All monetary values use PostgreSQL `NUMERIC(15,2)` columns and Python `Decimal`. Float types are **never** used in financial calculations.

### Stock Ledger
Stock is never stored as a field on the product. Instead, `current_stock = SUM(stock_movements)` is calculated on-the-fly from the `StockMovement` ledger, which tracks every inward/outward movement with type, quantity, price, and reference.

### Soft Deletes
All financial and operational records use `is_deleted = True` instead of hard deletes. This preserves audit trails and prevents orphaned foreign keys.

### Business Logic Separation
Route handlers in `api/v1/routes/` are thin — they only handle HTTP concerns (request parsing, response formatting). All domain logic lives in `services/`.

---

## 🌐 Internationalization

The UI supports 4 languages, switchable from the login page:

| Code | Language |
|------|----------|
| `bn` | বাংলা (default) |
| `en` | English |
| `hi` | हिन्दी |
| `ar` | عربي |

---

## 🧪 Testing & QA

### Running Backend Tests
To run backend unit and integration tests along with the coverage report:
```bash
cd backend
pip install -r requirements.txt
pytest --cov=app --cov-report=term-missing
```

### Running Load Tests
We use **Locust** to load test heavy dashboard snapshot and daybook reporting endpoints.
To run load tests locally:
```bash
pip install locust
locust -f backend/tests/locustfile.py
```
Then open `http://localhost:8089` to configure and start the load test.

---

## 🚢 Production Deployment

To run the application in a production environment (served using Nginx, optimized docker containers):

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This starts:
- `dms_postgres_prod` — Production PostgreSQL database
- `dms_redis_prod` — Redis queue
- `dms_backend_prod` — FastAPI backend (without auto-reload)
- `dms_worker_prod` — Celery background task worker
- `dms_frontend_prod` — Built React frontend served by Nginx on port **80**

---

## 🔧 Development

### Run migrations manually

```bash
docker compose exec backend alembic upgrade head
```

### Create a new migration

```bash
docker compose exec backend alembic revision --autogenerate -m "description"
```

### View backend logs

```bash
docker compose logs -f backend
```

### Rebuild after dependency changes

```bash
docker compose up -d --build backend
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/sprint-3-invoices`
3. Commit your changes: `git commit -m 'feat: add invoice creation endpoint'`
4. Push to the branch: `git push origin feature/sprint-3-invoices`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">Built for Bangladesh 🇧🇩 — with precision, in Bangla.</p>
<p align="center">This software is built by <a href="https://setuops.xyz">SETU Ops</a>.</p>
