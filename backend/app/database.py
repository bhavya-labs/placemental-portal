from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings

def normalize_database_url(url: str) -> str:
    """
    Normalize PostgreSQL database URLs to ensure the explicit psycopg2 driver
    dialect (postgresql+psycopg2://) is used and deprecated prefixes are corrected.
    
    Handles:
      - postgres:// -> postgresql+psycopg2:// (Render default prefix)
      - postgresql:// -> postgresql+psycopg2:// (Standard dialect without driver)
      - postgresql+psycopg:// -> postgresql+psycopg2:// (psycopg3 prefix mapped to psycopg2)
      - postgresql+psycopg2:// -> untouched
      - sqlite:///... -> untouched
    """
    if not url:
        return url
    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    if url.startswith("postgresql+psycopg://"):
        return "postgresql+psycopg2://" + url[len("postgresql+psycopg://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url

# Configure database engine options based on dialect
normalized_url = normalize_database_url(settings.DATABASE_URL)
engine_kwargs = {}
if normalized_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Enterprise connection pooling for PostgreSQL / production databases
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 1800
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(
    normalized_url,
    **engine_kwargs
)

# Enforce SQLite foreign key constraints on every connection
@event.listens_for(Engine, "connect")
def set_sqlite_foreign_keys(dbapi_connection, connection_record):
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

