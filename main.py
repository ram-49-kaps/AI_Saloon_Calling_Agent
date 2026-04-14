"""FastAPI application entry point for Salon Booking AI Agent."""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import create_tables, close_engine
from routes.vapi_webhook import router as vapi_router
from routes.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables + seed data. Shutdown: close DB engine."""
    print("🚀 Starting Salon Booking AI Agent...")
    try:
        from init_db import init_db
        await init_db()
        print("✅ Database ready")
    except Exception as e:
        import traceback
        print("❌ DATABASE INITIALIZATION FAILED:")
        traceback.print_exc()
    yield
    try:
        await close_engine()
        print("👋 Shutdown complete")
    except Exception:
        pass


app = FastAPI(
    title="Salon Booking AI Agent",
    description="Backend API for Vapi.ai voice calling agent — handles salon appointment booking, cancellation, and rescheduling.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Vapi and any frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(vapi_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Salon Booking AI Agent"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
