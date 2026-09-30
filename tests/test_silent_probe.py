from unittest.mock import Mock

import pytest

import missions.silent_probe as silent_probe
from missions.silent_probe import (
    REQUIRED_MATCHES,
    SOLUTION_PATH,
    collect_confirmed_speed,
    compute_speed,
    parse_number,
    solve,
)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(silent_probe.time, "sleep", lambda _: None)


FAILED = {"distance": "failed to measure, try again", "time": "failed to measure, try again"}
VALID = {"distance": "100 AU", "time": "4 hours"}


@pytest.mark.parametrize(
    "text, expected",
    [("12.5 AU", 12.5), ("712 AU", 712.0), ("", None), ("failed", None), (None, None)],
)
def test_parse_number_with_text_returns_first_number_or_none(text, expected):
    assert parse_number(text) == expected


@pytest.mark.parametrize("distance, time_h, expected", [(10, 3, 3), (11, 3, 4), (596, 1.4716, 405)])
def test_compute_speed_rounds_to_nearest_integer(distance, time_h, expected):
    assert compute_speed(distance, time_h) == expected


def test_collect_confirmed_speed_stops_when_required_matches_reached():
    client = Mock()
    client.get.side_effect = [FAILED, VALID, FAILED, VALID, VALID, VALID]

    result = collect_confirmed_speed(client, required_matches=3, delay_s=0)

    assert result == (25, 3, 1 + 1)
    assert client.get.call_count == 5


def test_collect_confirmed_speed_counts_each_speed_separately():
    other = {"distance": "50 AU", "time": "1 hours"}
    client = Mock()
    client.get.side_effect = [VALID, other, VALID, other, VALID]

    speed, hits, failures = collect_confirmed_speed(client, required_matches=3, delay_s=0)

    assert (speed, hits, failures) == (25, 5, 0)


def test_collect_confirmed_speed_ignores_zero_time():
    client = Mock()
    client.get.side_effect = [{"distance": "5 AU", "time": "0 hours"}, VALID]

    assert collect_confirmed_speed(client, required_matches=1, delay_s=0) == (25, 1, 1)


def test_collect_confirmed_speed_when_attempts_exhausted_raises():
    client = Mock()
    client.get.return_value = FAILED

    with pytest.raises(RuntimeError):
        collect_confirmed_speed(client, required_matches=2, max_attempts=3, delay_s=0)

    assert client.get.call_count == 3


def test_solve_with_dry_run_does_not_post():
    client = Mock()
    client.get.return_value = VALID

    assert solve(client, dry_run=True) == 25
    client.post.assert_not_called()


def test_solve_posts_confirmed_speed_once():
    client = Mock()
    client.get.return_value = VALID

    solve(client)

    client.post.assert_called_once_with(SOLUTION_PATH, {"speed": 25})


def test_solve_prints_summary_table_with_hits_and_failures(capsys):
    client = Mock()
    client.get.side_effect = [FAILED, FAILED] + [VALID] * REQUIRED_MATCHES

    solve(client, dry_run=True)

    out = capsys.readouterr().out
    assert f"| Aciertos | {REQUIRED_MATCHES:>8} |" in out
    assert "| Fallidas |        2 |" in out
