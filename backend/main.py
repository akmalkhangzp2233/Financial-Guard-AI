import os
import time
import logging

from dotenv import load_dotenv
load_dotenv()  # must run before any local module reads os.getenv() at import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from logging_config import configure_logging
from rate_limit import limiter
from database import engine, Base
from routers import auth, transactions, budgets, ml, categories, ai_advice, ocr, admin, reports

configure_logging()
logger = logging.getLogger("finguard")

# Creates tables from models.py if they don't exist yet.
# (You can also just run database/schema.sql directly against SQLite/MySQL/Postgres.)
Base.metadata.create_all(bind=engine)
# Seed default categories if none exist
from database import SessionLocal
from models import Category

db = SessionLocal()
if db.query(Category).count() == 0:
    db.add_all([
        Category(name="Groceries", icon="🛒", is_income=False),
        Category(name="Rent", icon="🏠", is_income=False),
        Category(name="Transport", icon="🚗", is_income=False),
        Category(name="Entertainment", icon="🎬", is_income=False),
        Category(name="Utilities", icon="💡", is_income=False),
        Category(name="Dining Out", icon="🍔", is_income=False),
        Category(name="Healthcare", icon="🏥", is_income=False),
        Category(name="Shopping", icon="🛍️", is_income=False),
        Category(name="Salary", icon="💰", is_income=True),
        Category(name="Other", icon="📦", is_income=False),
    ])
    db.commit()
db.close()

ENV = os.getenv("ENV", "development")

if ENV == "production" and os.getenv("JWT_SECRET", "change-this-in-your-.env-file") == "change-this-in-your-.env-file":
    # Fail loud, not quiet — a default JWT secret in production means anyone can forge tokens.
    raise RuntimeError(
        "Refusing to start: ENV=production but JWT_SECRET is unset/default. "
        "Set a strong JWT_SECRET env var (see backend/.env.example)."
    )

app = FastAPI(
    title="FinGuard AI API",
    version="1.0.0",
    description="Personal finance tracker with ML fraud detection, spend forecasting, "
                "OCR receipt scanning, and GPT-powered savings advice.",
    docs_url="/docs" if ENV != "production" else "/docs",  # keep Swagger on for viva/demo; disable by setting docs_url=None if truly public
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS origins come from env so the same image works in dev, staging, and prod
# without a code change. Comma-separated, e.g.:
#   CORS_ORIGINS=http://localhost:5173,https://finguard.vercel.app
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers_and_log(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000

    # Baseline production security headers (defense-in-depth; the real HTTPS
    # termination happens at the platform edge — see DEPLOYMENT.md)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

    logger.info(f'{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)')
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Uniform error shape across the whole API: {"error": {"code": ..., "message": ...}}"""
    logger.warning(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.info(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": 422, "message": "Validation failed", "details": exc.errors()}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Last line of defense: never leak a stack trace to the client. Full traceback
    still goes to the server log (visible via `docker compose logs` / your platform's log tab)."""
    logger.exception(f"Unhandled exception on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "Internal server error"}},
    )


app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(ml.router)
app.include_router(categories.router)
app.include_router(ai_advice.router)
app.include_router(ocr.router)
app.include_router(admin.router)
app.include_router(reports.router)


@app.get("/")
def health_check():
    return {"status": "FinGuard AI API is running", "env": ENV, "version": "1.0.0"}


@app.get("/health")
def health():
    """Liveness/readiness probe for Docker/Render/Railway/K8s health checks."""
    return {"status": "ok"}
