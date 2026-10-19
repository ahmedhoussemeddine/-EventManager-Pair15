
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.routers import events, participants, registrations


@pytest.fixture
def sample_event_dict():
    return {
        "title": "Python Workshop",
        "description": "Learn Python testing",
        "date": "2030-05-20",
        "location": "Setif",
        "capacity": 50,
    }


@pytest.fixture
def sample_participant_dict():
    return {
        "name": "Ali Ben",
        "email": "ali@example.com",
    }


@pytest.fixture
def mock_event_store():
    store = []
    yield store
    store.clear()


@pytest.fixture
def prepopulated_event_store(mock_event_store):
    mock_event_store.extend([
        {
            "title": "Python Workshop",
            "location": "Setif",
            "capacity": 50,
        },
        {
            "title": "Cybersecurity Day",
            "location": "Algiers",
            "capacity": 100,
        },
        {
            "title": "Web Development",
            "location": "Setif",
            "capacity": 30,
        },
    ])
    return mock_event_store


@pytest.fixture(autouse=True)
def global_environment_logger():
    print("\n[SETUP] Starting test")
    yield
    print("\n[TEARDOWN] Test finished")


@pytest.fixture
def api_client(tmp_path):
    # Create an isolated SQLite database for this test.
    test_db_path = tmp_path / "test_events.db"

    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    # Create the tables in the test database.
    Base.metadata.create_all(bind=test_engine)

    # Override the application's database dependency.
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    test_app = FastAPI()
    test_app.include_router(events.router)
    test_app.include_router(participants.router)
    test_app.include_router(registrations.router)

    test_app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(test_app) as client:
            yield client
    finally:
        test_app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
