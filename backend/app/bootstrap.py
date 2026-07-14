import subprocess

import uvicorn

from app.core.config import settings
from app.core.logging import get_logger
from app.core.runtime import database_summary, wait_for_database
from app.seed.run import seed

logger = get_logger("realmeet.bootstrap")


def run() -> None:
    config_errors = settings.critical_config_errors()
    if config_errors:
        raise RuntimeError(f"Invalid critical configuration: {', '.join(config_errors)}")

    logger.info(
        "app_starting env=%s host=%s port=%s db=%s cors=%s",
        settings.app_env,
        settings.backend_host,
        settings.backend_port,
        database_summary(),
        settings.cors_origins,
    )
    wait_for_database()
    logger.info("running_migrations")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    logger.info("running_seed")
    seed()
    logger.info("starting_uvicorn host=%s port=%s", settings.backend_host, settings.backend_port)
    uvicorn.run("app.main:app", host=settings.backend_host, port=settings.backend_port, reload=False)


if __name__ == "__main__":
    run()
