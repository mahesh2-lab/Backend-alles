import logging
from time import sleep
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from src.core.config import settings

logger = logging.getLogger(__name__)

# Create engine (does not open a connection immediately)
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
except Exception:
    logger.exception("Failed to create SQLAlchemy engine with DATABASE_URL: %s", getattr(
        settings, 'DATABASE_URL', None))
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a DB session with a connection health check and simple retry/backoff.

    On OperationalError (e.g. connection refused) this will retry a few times
    and then raise a RuntimeError with a clear message to help debugging.
    """
    db = None
    retries = getattr(settings, "DB_CONNECT_RETRIES", 3)
    delay = getattr(settings, "DB_CONNECT_RETRY_DELAY", 1)
    attempt = 0

    while True:
        attempt += 1
        try:
            db = SessionLocal()
            # quick health check: will raise OperationalError if the DB is unreachable
            db.execute(text("SELECT 1"))
            break
        except OperationalError as oe:
            # common case: connection refused / server down
            logger.warning(
                "Database connection attempt %d/%d failed: %s", attempt, retries, oe)
            try:
                if db is not None:
                    db.close()
            except Exception:
                logger.debug(
                    "Failed to close DB session after connection failure")

            if attempt >= retries:
                logger.exception(
                    "Exceeded %d database connection retries. Last error: %s", retries, oe)
                # Raise a clearer, higher-level error for callers to handle/log
                raise RuntimeError(
                    "Unable to connect to the database. Ensure the database server is running and DATABASE_URL is correct."
                ) from oe

            sleep(delay)
        except Exception:
            # Any other unexpected error while creating session
            logger.exception("Unexpected error while obtaining DB session")
            raise

    try:
        yield db
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            logger.exception("Failed to close database session")
