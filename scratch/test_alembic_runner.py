from alembic.config import Config
from alembic import command
from pathlib import Path

def test_alembic_programmatic():
    ini_path = Path("alembic.ini").resolve()
    print(f"Using ini: {ini_path}")
    cfg = Config(str(ini_path))
    command.upgrade(cfg, "head")
    print("Programmatic upgrade finished!")

if __name__ == "__main__":
    test_alembic_programmatic()
