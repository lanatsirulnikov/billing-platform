import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import Base
from app.main import app
from app.models import init  # registers models
from app.api.customers import get_db as customers_get_db
from app.api.plans import get_db as plans_get_db
from app.api.subscriptions import get_db as subscriptions_get_db
from app.api.invoices import get_db as invoices_get_db
from app.api.invoice_items import get_db as invoice_items_get_db
from app.api.usage_records import get_db as usage_records_get_db

@pytest.fixture(scope="session")
def test_engine(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("billing-tests")
    db_file = db_dir / "test_billing.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def testing_session_factory(test_engine):
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

@pytest.fixture(scope="session", autouse=True)
def setup_database(test_engine):
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(test_engine, testing_session_factory):
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    session = testing_session_factory()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[customers_get_db] = override_get_db
    app.dependency_overrides[plans_get_db] = override_get_db
    app.dependency_overrides[subscriptions_get_db] = override_get_db
    app.dependency_overrides[invoices_get_db] = override_get_db
    app.dependency_overrides[invoice_items_get_db] = override_get_db
    app.dependency_overrides[usage_records_get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
