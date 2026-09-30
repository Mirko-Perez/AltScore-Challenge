from unittest.mock import Mock

import pytest

import missions.e2_kepler_oracle as kepler_oracle
from missions.e2_kepler_oracle import (
    SOLUTION_PATH,
    compute_average_resonance,
    fetch_all_stars,
    solve,
)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(kepler_oracle.time, "sleep", lambda _: None)


def star(star_id, resonance):
    return {"id": star_id, "resonance": resonance, "position": {"x": 0, "y": 0, "z": 0}}


@pytest.mark.parametrize(
    "resonances, expected",
    [([10, 20, 30], 20), ([1, 2], 1), ([388, 389], 388), ([5], 5), ([1, 1, 2], 1)],
)
def test_compute_average_resonance_truncates_to_integer(resonances, expected):
    stars = [star(str(i), r) for i, r in enumerate(resonances)]

    assert compute_average_resonance(stars) == expected


def test_compute_average_resonance_with_no_stars_raises():
    with pytest.raises(ValueError):
        compute_average_resonance([])


def test_fetch_all_stars_reads_pages_until_empty_and_dedupes():
    client = Mock()
    client.get.side_effect = [[star("a", 1), star("b", 2)], [star("b", 2), star("c", 3)], []]

    stars = fetch_all_stars(client)

    assert [s["id"] for s in stars] == ["a", "b", "c"]
    assert client.get.call_count == 3
    assert client.get.call_args_list[1].kwargs == {"params": {"page": 2}}


def test_fetch_all_stars_with_error_payload_raises():
    client = Mock()
    client.get.return_value = {"detail": "Are you registered?"}

    with pytest.raises(RuntimeError):
        fetch_all_stars(client)


def test_solve_with_dry_run_does_not_post():
    client = Mock()
    client.get.side_effect = [[star("a", 10), star("b", 20)], []]

    assert solve(client, dry_run=True) == 15
    client.post.assert_not_called()


def test_solve_posts_average_once():
    client = Mock()
    client.get.side_effect = [[star("a", 10), star("b", 20)], []]

    solve(client)

    client.post.assert_called_once_with(SOLUTION_PATH, {"average_resonance": 15})
