"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes import auth as auth_router
from app.api.v1.routes import products as products_router
from app.api.v1.routes import inventory as inventory_router
from app.api.v1.routes import suppliers as suppliers_router
from app.api.v1.routes import purchases as purchases_router
from app.api.v1.routes import routes as routes_router
from app.api.v1.routes import dealers as dealers_router
from app.api.v1.routes import dsrs as dsrs_router
from app.api.v1.routes import shops as shops_router
from app.api.v1.routes import invoices as invoices_router
from app.api.v1.routes.products import cat_router as categories_router
from app.core.config import get_settings
# Import all models to register them with SQLAlchemy metadata
from app import models  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title=f"{settings.app_name} API",
    version=settings.app_version,
    description="Dealership Management System — Bangladesh distribution business",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# -------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Global exception handlers — standard response envelope
# -------------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.app_env == "development" else None,
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"success": False, "error": "Not found", "detail": str(request.url)},
    )


# -------------------------------------------------------------------
# Health check — public, no auth
# -------------------------------------------------------------------
@app.get("/health", tags=["health"], include_in_schema=True)
async def health_check() -> dict:
    return {"status": "ok", "version": settings.app_version, "app": settings.app_name}


# -------------------------------------------------------------------
# API Routers
# -------------------------------------------------------------------
from app.api.v1.routes import accounts as accounts_router
from app.api.v1.routes import expenses as expenses_router
from app.api.v1.routes import contra as contra_router
from app.api.v1.routes import reports as reports_router
from app.api.v1.routes import dashboard as dashboard_router
from app.api.v1.routes import roles as roles_router
from app.api.v1.routes import users as users_router
from app.api.v1.routes import settings as settings_router
from app.api.v1.routes import targets as targets_router
from app.api.v1.routes import returns as returns_router

app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(products_router.router, prefix="/api/v1")
app.include_router(inventory_router.router, prefix="/api/v1")
app.include_router(suppliers_router.router, prefix="/api/v1")
app.include_router(purchases_router.router, prefix="/api/v1")
app.include_router(routes_router.router, prefix="/api/v1")
app.include_router(dealers_router.router, prefix="/api/v1")
app.include_router(dsrs_router.router, prefix="/api/v1")
app.include_router(shops_router.router, prefix="/api/v1")
app.include_router(invoices_router.router, prefix="/api/v1")
app.include_router(accounts_router.router, prefix="/api/v1")
app.include_router(expenses_router.router, prefix="/api/v1")
app.include_router(contra_router.router, prefix="/api/v1")
app.include_router(reports_router.router, prefix="/api/v1")
app.include_router(dashboard_router.router, prefix="/api/v1")
app.include_router(roles_router.router, prefix="/api/v1")
app.include_router(users_router.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")
app.include_router(targets_router.router, prefix="/api/v1")
app.include_router(returns_router.router, prefix="/api/v1")
