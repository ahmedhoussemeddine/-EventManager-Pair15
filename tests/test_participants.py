
import pytest
from pydantic import ValidationError

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
