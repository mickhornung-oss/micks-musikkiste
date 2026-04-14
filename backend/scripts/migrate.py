"""Run Alembic migrations for Micks Musikkiste."""

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


def main():
    alembic_dir = Path(__file__).parent.parent / "alembic"
    config_path = Path(__file__).parent.parent / "alembic.ini"

    config = Config(str(config_path))
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    config.set_main_option("script_location", str(alembic_dir))

    try:
        print("Running Alembic upgrade...")
        command.upgrade(config, "head")
        print("Migrations applied successfully.")
    except Exception as exc:
        print(f"Migration failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
