import base64

import pytest

from missions.e3_sith_temple import (
    classify_side,
    compute_force_balance,
    decode_oracle_notes,
    find_balanced_planets,
)


def encode(text):
    return base64.b64encode(text.encode()).decode()


def test_decode_oracle_notes_with_base64_returns_text():
    assert decode_oracle_notes(encode("Luke is a Jedi")) == "Luke is a Jedi"


def test_decode_oracle_notes_with_invalid_base64_returns_input():
    assert decode_oracle_notes("esto no es base64!") == "esto no es base64!"


@pytest.mark.parametrize(
    "notes, expected",
    [
        ("Luke Skywalker is a Jedi, and belongs to the Light Side of the Force.", "light"),
        (
            "Darth Vader was once a Jedi but fell to the Dark Side; "
            "he belongs to the Dark Side of the Force.",
            "dark",
        ),
        ("Yoda is wise and balanced.", "unknown"),
        (None, "unknown"),
    ],
)
def test_classify_side_uses_belongs_to_phrase(notes, expected):
    assert classify_side(notes) == expected


DATASET = {
    "people": [
        {"name": "A", "side": "light"},
        {"name": "B", "side": "dark"},
        {"name": "C", "side": "light"},
        {"name": "D", "side": "light"},
    ],
    "planets": [
        {"name": "Balanced", "residents": ["A", "B"]},
        {"name": "Bright", "residents": ["C", "D"]},
        {"name": "Empty", "residents": []},
    ],
}


def test_compute_force_balance_calculates_ibf_and_skips_empty_planets():
    balances = compute_force_balance(DATASET)

    assert [b["planet"] for b in balances] == ["Balanced", "Bright"]
    assert balances[0] == {"planet": "Balanced", "light": 1, "dark": 1, "total": 2, "ibf": 0.0}
    assert balances[1]["ibf"] == 1.0


def test_find_balanced_planets_returns_only_equal_light_and_dark():
    balanced = find_balanced_planets(compute_force_balance(DATASET))

    assert [b["planet"] for b in balanced] == ["Balanced"]
