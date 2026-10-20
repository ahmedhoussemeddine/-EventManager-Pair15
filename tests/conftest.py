
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


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
