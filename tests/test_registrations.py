from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.models import Event, Participant, Registration
from app.routers.registrations import (
    list_event_participants,
    register_participant,
)


def _create_event(db_session, payload):
    event = Event(
        title=payload["title"],
        description=payload.get("description"),
        date=date.fromisoformat(payload["date"]),
        location=payload["location"],
        capacity=payload["capacity"],
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def _create_participant(db_session, payload):
    participant = Participant(
        name=payload["name"],
        email=payload["email"],
    )
    db_session.add(participant)
    db_session.commit()
    db_session.refresh(participant)
    return participant


def test_register_participant_success(db_session, sample_event_dict, sample_participant_dict):
    event = _create_event(db_session, sample_event_dict)
    participant = _create_participant(db_session, sample_participant_dict)

    registration = register_participant(event.id, participant.id, db_session)

    assert registration.event_id == event.id
    assert registration.participant_id == participant.id


def test_register_participant_event_not_found(db_session, sample_participant_dict):
    participant = _create_participant(db_session, sample_participant_dict)

    with pytest.raises(HTTPException) as exc_info:
        register_participant(9999, participant.id, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found."


def test_register_participant_missing_participant(db_session, sample_event_dict):
    event = _create_event(db_session, sample_event_dict)

    with pytest.raises(HTTPException) as exc_info:
        register_participant(event.id, 9999, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Participant not found."


def test_register_participant_duplicate_registration(db_session, sample_event_dict, sample_participant_dict):
    event = _create_event(db_session, sample_event_dict)
    participant = _create_participant(db_session, sample_participant_dict)

    register_participant(event.id, participant.id, db_session)

    with pytest.raises(HTTPException) as exc_info:
        register_participant(event.id, participant.id, db_session)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Participant is already registered."


def test_register_participant_capacity_reached(db_session, sample_event_dict, sample_participant_dict):
    data = sample_event_dict.copy()
    data["capacity"] = 1
    event = _create_event(db_session, data)
    first_participant = _create_participant(
        db_session,
        {"name": "Ali Ben", "email": "ali@example.com"},
    )
    second_participant = _create_participant(
        db_session,
        {"name": "Sara Ben", "email": "sara@example.com"},
    )

    registration = Registration(event_id=event.id, participant_id=first_participant.id)
    db_session.add(registration)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        register_participant(event.id, second_participant.id, db_session)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Event capacity has been reached."


def test_list_event_participants_success_and_missing_event(db_session, sample_event_dict, sample_participant_dict):
    event = _create_event(db_session, sample_event_dict)
    participant = _create_participant(db_session, sample_participant_dict)

    register_participant(event.id, participant.id, db_session)

    result = list_event_participants(event.id, db_session)

    assert result == [{
        "id": participant.id,
        "name": participant.name,
        "email": participant.email,
    }]

    with pytest.raises(HTTPException) as exc_info:
        list_event_participants(9999, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found."
