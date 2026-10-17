import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.seed import seed_database_defaults

# Import all routers
from backend.app.routers import (
    auth, dashboard, medicines, purchases, pos,
    customers, suppliers, alerts, returns,
    reports, expenses, excel, invoices, settings as app_settings
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables exist & seed defaults
    print("=" * 60)
    print("Initializing Baalaji Pharmacy Management System Database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database_defaults(db)
        print("Database initialized & default credentials verified.")
    except Exception as e:
        print(f"Notice on seed initialization: {e}")
    finally:
        db.close()
    print("Backend Server Ready! Serving at http://127.0.0.1:8000")
    print("=" * 60)
    yield
    # Shutdown logic if needed

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(medicines.router)
app.include_router(purchases.router)
app.include_router(pos.router)
app.include_router(customers.router)
app.include_router(suppliers.router)
app.include_router(alerts.router)
app.include_router(returns.router)
app.include_router(reports.router)
app.include_router(expenses.router)
app.include_router(excel.router)
app.include_router(invoices.router)
app.include_router(app_settings.router)

# Mount frontend directory for Web & Electron app
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")
