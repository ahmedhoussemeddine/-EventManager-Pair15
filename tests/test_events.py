
from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models import Event
from app.routers.events import (
    create_event,
    delete_event,
    filter_events_by_location,
    filter_events_by_title,
    get_event,
    list_events,
    update_event,
)
from app.schemas import EventCreate, EventUpdate


# -------------------------
# Happy path tests
# اختبارات البيانات الصحيحة
# -------------------------

def test_valid_event_creation(sample_event_dict):
    event = EventCreate(**sample_event_dict)

    assert event.title == "Python Workshop"
    assert event.capacity == 50


def test_filter_events_by_location(prepopulated_event_store):
    results = filter_events_by_location(
        prepopulated_event_store,
        "setif",
    )

    assert len(results) == 2
    assert all(
        "setif" in event["location"].casefold()
        for event in results
    )


def test_filter_events_by_title(prepopulated_event_store):
    results = filter_events_by_title(
        prepopulated_event_store,
        "python",
    )

    assert len(results) == 1
    assert results[0]["title"] == "Python Workshop"


# -------------------------
# Boundary value tests
# اختبارات الحدود
# -------------------------

def test_capacity_minimum(sample_event_dict):
    data = sample_event_dict.copy()
    data["capacity"] = 1

    event = EventCreate(**data)

    assert event.capacity == 1


def test_capacity_maximum(sample_event_dict):
    data = sample_event_dict.copy()
    data["capacity"] = 10000

    event = EventCreate(**data)

    assert event.capacity == 10000


def test_title_minimum_length(sample_event_dict):
    data = sample_event_dict.copy()
    data["title"] = "ABC"

    event = EventCreate(**data)

    assert len(event.title) == 3


# -------------------------
# Negative tests
# اختبارات البيانات الخاطئة
# -------------------------

def test_short_title_rejected(sample_event_dict):
    data = sample_event_dict.copy()
    data["title"] = "AI"

    with pytest.raises(ValidationError):
        EventCreate(**data)


def test_zero_capacity_rejected(sample_event_dict):
    data = sample_event_dict.copy()
    data["capacity"] = 0

    with pytest.raises(ValidationError):
        EventCreate(**data)


def test_negative_capacity_rejected(sample_event_dict):
    data = sample_event_dict.copy()
    data["capacity"] = -1

    with pytest.raises(ValidationError):
        EventCreate(**data)


# -------------------------
# Router branch coverage
# -------------------------

def test_create_event_success(db_session, sample_event_dict):
    created = create_event(EventCreate(**sample_event_dict), db_session)

    assert created.id is not None
    assert created.title == sample_event_dict["title"]


def test_create_event_rejects_past_date(db_session, sample_event_dict):
    data = sample_event_dict.copy()
    data["date"] = (date.today() - timedelta(days=1)).isoformat()

    with pytest.raises(HTTPException) as exc_info:
        create_event(EventCreate(**data), db_session)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Event date cannot be in the past."


def test_list_events_returns_all_and_filtered(db_session, sample_event_dict):
    create_event(EventCreate(**sample_event_dict), db_session)
    create_event(
        EventCreate(
            title="AI Security Summit",
            description="Future AI event",
            date="2031-06-15",
            location="Algiers",
            capacity=10,
        ),
        db_session,
    )

    assert len(list_events(None, db_session)) == 2
    assert len(list_events("python", db_session)) == 1


def test_get_event_success_and_missing(db_session, sample_event_dict):
    created = create_event(EventCreate(**sample_event_dict), db_session)

    assert get_event(created.id, db_session).id == created.id

    with pytest.raises(HTTPException) as exc_info:
        get_event(9999, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found."


def test_update_event_success_and_error_cases(db_session, sample_event_dict):
    created = create_event(EventCreate(**sample_event_dict), db_session)

    updated = EventUpdate(
        title="Updated Workshop",
        description="Updated description",
        date="2035-01-15",
        location="Oran",
        capacity=75,
    )
    result = update_event(created.id, updated, db_session)

    assert result.title == "Updated Workshop"
    assert result.location == "Oran"

    with pytest.raises(HTTPException) as missing:
        update_event(9999, updated, db_session)
    assert missing.value.status_code == 404

    past_data = EventUpdate(
        title="Past Update",
        description="Should fail",
        date=(date.today() - timedelta(days=1)),
        location="Setif",
        capacity=50,
    )
    with pytest.raises(HTTPException) as past:
        update_event(created.id, past_data, db_session)
    assert past.value.status_code == 400
    assert past.value.detail == "Event date cannot be in the past."


def test_delete_event_success_and_missing(db_session, sample_event_dict):
    created = create_event(EventCreate(**sample_event_dict), db_session)

    delete_event(created.id, db_session)
    assert db_session.query(Event).filter(Event.id == created.id).first() is None

    with pytest.raises(HTTPException) as exc_info:
        delete_event(9999, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found."
