
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models import Participant
from app.routers.participants import (
    create_participant,
    delete_participant,
    get_participant,
    list_participants,
)
from app.schemas import ParticipantCreate
from app.services import (
    has_available_capacity,
    check_duplicate_registration,
)


# =========================================
# 1. HAPPY PATH TESTS
# =========================================

def test_valid_participant_creation():
    participant = ParticipantCreate(
        name="Ahmed",
        email="ahmed@example.com"
    )

    assert participant.name == "Ahmed"
    assert participant.email == "ahmed@example.com"


def test_available_capacity():
    assert has_available_capacity(5, 10) is True


# =========================================
# 2. BOUNDARY VALUE TESTS
# =========================================

def test_capacity_one_below_max():
    assert has_available_capacity(9, 10) is True


def test_capacity_equal_to_max():
    assert has_available_capacity(10, 10) is False


def test_capacity_above_max():
    assert has_available_capacity(11, 10) is False


# =========================================
# 3. NEGATIVE TESTS
# =========================================

def test_invalid_email_rejected():
    with pytest.raises(ValidationError):
        ParticipantCreate(
            name="Ahmed",
            email="invalid-email"
        )


def test_short_name_rejected():
    with pytest.raises(ValidationError):
        ParticipantCreate(
            name="A",
            email="ahmed@example.com"
        )


def test_duplicate_registration_rejected():
    registered_ids = [1, 2, 3]

    with pytest.raises(ValueError):
        check_duplicate_registration(registered_ids, 2)


# =========================================
# ROUTER BRANCH COVERAGE
# =========================================


def test_create_participant_success(db_session):
    data = ParticipantCreate(name="Ahmed", email="ahmed@example.com")

    created = create_participant(data, db_session)

    assert created.id is not None
    assert created.email == "ahmed@example.com"


def test_create_participant_duplicate_email_rejected(db_session):
    data = ParticipantCreate(name="Ahmed", email="ahmed@example.com")
    create_participant(data, db_session)

    with pytest.raises(HTTPException) as exc_info:
        create_participant(data, db_session)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Email is already registered."


def test_list_and_get_participant(db_session):
    create_participant(ParticipantCreate(name="Ahmed", email="ahmed@example.com"), db_session)
    create_participant(ParticipantCreate(name="Karim", email="karim@example.com"), db_session)

    participants = list_participants(db_session)
    assert len(participants) == 2

    found = get_participant(participants[0].id, db_session)
    assert found.name == "Ahmed"

    with pytest.raises(HTTPException) as exc_info:
        get_participant(9999, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Participant not found."


def test_delete_participant_success_and_missing(db_session):
    created = create_participant(ParticipantCreate(name="Ahmed", email="ahmed@example.com"), db_session)

    delete_participant(created.id, db_session)
    assert db_session.query(Participant).filter(Participant.id == created.id).first() is None

    with pytest.raises(HTTPException) as exc_info:
        delete_participant(9999, db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Participant not found."
