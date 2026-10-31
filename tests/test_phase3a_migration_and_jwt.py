import os
import sys
import tempfile
import sqlite3
import pytest
from pathlib import Path
from alembic.config import Config
from alembic import command

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import Settings, INSECURE_FALLBACK_SECRET_KEY


def test_alembic_migration_from_scratch_success():
    """
    Verify that an empty database running alembic upgrade head from None succeeds
    without 'duplicate column' or foreign key errors.
    """
    scratch_dir = PROJECT_ROOT / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    db_path = scratch_dir / "test_scratch_migration_unit.db"
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass

    orig_env = os.environ.get("DATABASE_URL")
    db_url = f"sqlite:///{db_path.as_posix()}"
    os.environ["DATABASE_URL"] = db_url

    try:
        ini_path = str(PROJECT_ROOT / "alembic.ini")
        cfg = Config(ini_path)
        cfg.set_main_option("sqlalchemy.url", db_url)

        # 1. Upgrade from scratch to head
        command.upgrade(cfg, "head")

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        # Check version
        cur.execute("SELECT version_num FROM alembic_version;")
        assert cur.fetchone()[0] == "c8f39a4d12e5"

        # Check notifications columns
        cur.execute("PRAGMA table_info(notifications);")
        cols = [r[1] for r in cur.fetchall()]
        assert "reference_key" in cols

        # Check partial unique index
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='uq_notif_user_ref';")
        assert cur.fetchone() is not None

        conn.close()

        # 2. Downgrade by 1 and re-upgrade
        command.downgrade(cfg, "-1")
        command.upgrade(cfg, "head")

        # 3. Clean no-op on re-running upgrade head
        command.upgrade(cfg, "head")
    finally:
        if orig_env is not None:
            os.environ["DATABASE_URL"] = orig_env
        else:
            os.environ.pop("DATABASE_URL", None)
        if db_path.exists():
            try:
                db_path.unlink()
            except Exception:
                pass


def test_jwt_secret_validation_in_development():
    """
    Ensure development environment allows default fallback key without error.
    """
    s = Settings(ENVIRONMENT="development", SECRET_KEY=INSECURE_FALLBACK_SECRET_KEY)
    # Should not raise
    s.validate_production_secrets()


def test_jwt_secret_validation_in_production_missing():
    """
    Ensure production environment strictly rejects missing/empty SECRET_KEY.
    """
    s = Settings(ENVIRONMENT="production", SECRET_KEY="")
    with pytest.raises(RuntimeError, match="SECRET_KEY is not set for production"):
        s.validate_production_secrets()


def test_jwt_secret_validation_in_production_fallback():
    """
    Ensure production environment strictly rejects known insecure fallback SECRET_KEY.
    """
    s = Settings(ENVIRONMENT="production", SECRET_KEY=INSECURE_FALLBACK_SECRET_KEY)
    with pytest.raises(RuntimeError, match="SECRET_KEY is set to the default insecure fallback"):
        s.validate_production_secrets()


def test_jwt_secret_validation_in_production_short_key():
    """
    Ensure production environment rejects keys shorter than 32 characters.
    """
    s = Settings(ENVIRONMENT="production", SECRET_KEY="short-secret-key")
    with pytest.raises(RuntimeError, match="SECRET_KEY is too short"):
        s.validate_production_secrets()


def test_jwt_secret_validation_in_production_valid():
    """
    Ensure production environment accepts a cryptographically strong 64-character key.
    """
    strong_key = "f" * 64
    s = Settings(ENVIRONMENT="production", SECRET_KEY=strong_key)
    # Should not raise
    s.validate_production_secrets()
