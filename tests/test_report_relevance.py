import pytest
from fastapi.testclient import TestClient

from matching_system.api import app
from matching_system.report_relevance import INVALID_DESCRIPTION, is_relevant_description


@pytest.mark.parametrize("description", [
    "I had chicken for lunch.", "We ate rice for dinner yesterday.",
    "Good morning!", "How are you?", "asdfghjkl", "qwerty", "!!!!",
    "zzzzzz", "this is a test",
])
def test_clearly_irrelevant_description(description):
    assert not is_relevant_description(description)


@pytest.mark.parametrize("description", [
    "Black HP 65W laptop charger", "Purple telescope with a broken handle",
    "Violet xylophone", "Chicken-shaped keyring",
    "I had chicken for lunch and lost my wallet",
    "I ate lunch and left my bag in the cafeteria",
    "Red", "X200", "Blak samsng smrtfone", "Lunch container",
    "I lost the ring after dinner", "Navy umbrella with wooden handle",
])
def test_valid_or_uncertain_description_is_not_blocked(description):
    assert is_relevant_description(description)


def test_preview_rejects_off_topic_and_reports_zero_matches():
    client = TestClient(app)
    invalid = client.post("/preview/matches", json={
        "item_name": "Bottle", "description": "I had chicken for lunch."
    })
    assert invalid.status_code == 422
    assert invalid.json()["detail"] == INVALID_DESCRIPTION
    absent = client.post("/preview/matches", json={
        "item_name": "Telescope", "description": "Violet telescope marked SYNTHETIC-X999"
    })
    assert absent.status_code == 200
    assert absent.json()["status"] == "no_lexical_candidates"
    assert absent.json()["match_count"] == 0
    assert absent.json()["matches"] == []
    valid = client.post("/preview/matches", json={
        "item_name": "Metal water bottle", "description": "Blue bottle with a scratched lid"
    })
    assert valid.status_code == 200
    assert valid.json()["match_count"] > 0
