import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, get_db


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    test_database_url = "sqlite:///./test.db"
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    """Create a test database session."""
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    """Override the get_db dependency for tests."""

    def _get_db():
        try:
            yield db_session
        finally:
            pass

    from app.main import app

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()
