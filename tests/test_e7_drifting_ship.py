from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import missions.e7_drifting_ship as drifting_ship
from missions.e7_drifting_ship import ANCHOR_PATTERN, SYSTEM_CODES, app, solve

client = TestClient(app)


def test_status_returns_one_of_the_known_systems():
    response = client.get("/status")

    assert response.status_code == 200
    assert response.json()["damaged_system"] in SYSTEM_CODES


@pytest.mark.parametrize("system, code", SYSTEM_CODES.items())
def test_repair_bay_shows_the_code_of_the_reported_system(monkeypatch, system, code):
    monkeypatch.setattr(drifting_ship.random, "choice", lambda _: system)

    assert client.get("/status").json() == {"damaged_system": system}
    page = client.get("/repair-bay")

    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert ANCHOR_PATTERN.search(page.text).group(1) == code


def test_repair_bay_matches_status_over_many_rounds():
    for _ in range(30):
        system = client.get("/status").json()["damaged_system"]
        found = ANCHOR_PATTERN.search(client.get("/repair-bay").text).group(1)

        assert found == SYSTEM_CODES[system]


def test_repair_bay_html_matches_the_documented_example(monkeypatch):
    monkeypatch.setattr(drifting_ship.random, "choice", lambda _: "engines")
    client.get("/status")

    assert client.get("/repair-bay").text == (
        "<!DOCTYPE html>\n<html>\n<head>\n    <title>Repair</title>\n</head>\n<body>\n"
        '<div class="anchor-point">ENG-04</div>\n</body>\n</html>\n'
    )


def test_teapot_returns_418():
    assert client.post("/teapot").status_code == 418


def test_teapot_rejects_get():
    assert client.get("/teapot").status_code == 405


def test_solve_without_url_raises():
    with pytest.raises(ValueError):
        solve(Mock())


def test_solve_does_not_register_when_autocheck_fails(monkeypatch):
    monkeypatch.setattr(drifting_ship, "check_deployment", lambda url: ["roto"])
    api = Mock()

    with pytest.raises(RuntimeError):
        solve(api, url="https://x.example")

    api.post.assert_not_called()


def test_solve_with_dry_run_does_not_register(monkeypatch):
    monkeypatch.setattr(drifting_ship, "check_deployment", lambda url: [])
    api = Mock()

    solve(api, dry_run=True, url="https://x.example")

    api.post.assert_not_called()


def test_solve_registers_the_url_without_trailing_slash(monkeypatch):
    monkeypatch.setattr(drifting_ship, "check_deployment", lambda url: [])
    api = Mock()

    solve(api, url="https://x.example/")

    api.post.assert_called_once_with(drifting_ship.SOLUTION_PATH, {"base_url": "https://x.example"})
