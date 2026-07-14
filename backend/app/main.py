from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import get_logger
from app.core.runtime import check_critical_configuration, check_database_connection, database_summary
from app.core.scheduler import scheduler

logger = get_logger("realmeet.app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "app_lifespan_started env=%s db=%s cors=%s",
        settings.app_env,
        database_summary(),
        settings.cors_origins,
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/ready", tags=["health"])
def readiness() -> dict[str, str]:
    if not check_critical_configuration():
        raise HTTPException(status_code=503, detail={"status": "not_ready", "configuration": "invalid"})

    if check_database_connection():
        return {"status": "ready", "database": "ok", "configuration": "ok"}

    raise HTTPException(status_code=503, detail={"status": "not_ready", "database": "unavailable"})
