from __future__ import annotations

from time import sleep

from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import SessionLocal

logger = get_logger("realmeet.runtime")


def sanitize_database_url() -> str:
    url: URL = make_url(settings.database_url)
    return url.render_as_string(hide_password=True)


def database_summary() -> str:
    url: URL = make_url(settings.database_url)
    return f"{url.drivername}://{url.host}:{url.port}/{url.database}"


def check_database_connection() -> bool:
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as exc:
        logger.warning("database_check_failed error=%s", exc.__class__.__name__)
        return False
    finally:
        try:
            db.close()
        except Exception:
            pass


def check_critical_configuration() -> bool:
    errors = settings.critical_config_errors()
    if errors:
        logger.warning("critical_config_check_failed errors=%s", ",".join(errors))
        return False
    return True


def wait_for_database(max_attempts: int = 30, delay_seconds: int = 2) -> None:
    logger.info("waiting_for_database target=%s", database_summary())
    for attempt in range(1, max_attempts + 1):
        if check_database_connection():
            logger.info("database_ready target=%s attempt=%s", database_summary(), attempt)
            return
        logger.info("database_not_ready target=%s attempt=%s", database_summary(), attempt)
        sleep(delay_seconds)
    raise RuntimeError(f"Database not reachable after {max_attempts} attempts: {sanitize_database_url()}")
