import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.scheduler import start_scheduler, stop_scheduler
from app.routers import (
    auth,
    usuarios,
    categorias,
    alumnos,
    config as config_router,
    mensualidades,
    pagos,
    notificaciones,
    dashboard,
    reportes,
    public,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Sistema Escuela de Futbol", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


app.include_router(auth.router, prefix="/api")
app.include_router(usuarios.router, prefix="/api")
app.include_router(categorias.router, prefix="/api")
app.include_router(alumnos.router, prefix="/api")
app.include_router(config_router.router, prefix="/api")
app.include_router(mensualidades.router, prefix="/api")
app.include_router(pagos.router, prefix="/api")
app.include_router(notificaciones.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(reportes.router, prefix="/api")
app.include_router(public.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
