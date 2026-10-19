from datetime import date, timedelta


def test_create_event(api_client, sample_event_dict):
    response = api_client.post("/events/", json=sample_event_dict)

    assert response.status_code == 201
    assert response.json()["title"] == sample_event_dict["title"]


def test_create_event_with_past_date(api_client, sample_event_dict):
    data = sample_event_dict.copy()
    data["date"] = (date.today() - timedelta(days=1)).isoformat()

    response = api_client.post("/events/", json=data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Event date cannot be in the past."


def test_list_events(api_client, sample_event_dict):
    api_client.post("/events/", json=sample_event_dict)

    response = api_client.get("/events/")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_events_by_title(api_client, sample_event_dict):
    api_client.post("/events/", json=sample_event_dict)

    response = api_client.get("/events/?search=python")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_events_by_location(api_client, sample_event_dict):
    api_client.post("/events/", json=sample_event_dict)

    response = api_client.get("/events/?location=setif")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_event(api_client, sample_event_dict):
    created = api_client.post("/events/", json=sample_event_dict)
    event_id = created.json()["id"]

    response = api_client.get(f"/events/{event_id}")

    assert response.status_code == 200
    assert response.json()["id"] == event_id


def test_get_missing_event(api_client):
    response = api_client.get("/events/99999")

    assert response.status_code == 404


def test_update_event(api_client, sample_event_dict):
    created = api_client.post("/events/", json=sample_event_dict)
    event_id = created.json()["id"]

    updated_data = sample_event_dict.copy()
    updated_data["title"] = "Updated Workshop"

    response = api_client.put(
        f"/events/{event_id}",
        json=updated_data,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Workshop"


def test_update_missing_event(api_client, sample_event_dict):
    response = api_client.put(
        "/events/99999",
        json=sample_event_dict,
    )

    assert response.status_code == 404


def test_update_event_with_past_date(api_client, sample_event_dict):
    created = api_client.post("/events/", json=sample_event_dict)
    event_id = created.json()["id"]

    updated_data = sample_event_dict.copy()
    updated_data["date"] = (date.today() - timedelta(days=1)).isoformat()

    response = api_client.put(
        f"/events/{event_id}",
        json=updated_data,
    )

    assert response.status_code == 400


def test_delete_event(api_client, sample_event_dict):
    created = api_client.post("/events/", json=sample_event_dict)
    event_id = created.json()["id"]

    response = api_client.delete(f"/events/{event_id}")

    assert response.status_code == 204
    assert api_client.get(f"/events/{event_id}").status_code == 404


def test_delete_missing_event(api_client):
    response = api_client.delete("/events/99999")

    assert response.status_code == 404
