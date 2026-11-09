from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.main import app

API_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Create a separate test database next to the dev one, migrate it, drop it afterwards."""
    dev_url = make_url(get_settings().database_url)
    test_db_name = f"{dev_url.database}_test"
    test_url = dev_url.set(database=test_db_name)

    admin_engine = create_engine(dev_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))

    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", test_url.render_as_string(hide_password=False))
    command.upgrade(cfg, "head")

    eng = create_engine(test_url)
    yield eng
    eng.dispose()

    with admin_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}" WITH (FORCE)'))
    admin_engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """Each test runs in a transaction that is rolled back at the end."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()
