
import pytest
from pydantic import ValidationError

from app.schemas import EventCreate
from app.routers.events import (
    filter_events_by_location,
    filter_events_by_title,
)


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
