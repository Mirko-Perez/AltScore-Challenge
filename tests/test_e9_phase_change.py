from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import missions.e9_phase_change as phase_change
from missions.e7_drifting_ship import app
from missions.e9_phase_change import SOLUTION_PATH, saturation_volumes, solve

client = TestClient(app)


def test_critical_point_gives_the_same_volume_for_liquid_and_vapor():
    assert saturation_volumes(10) == {
        "specific_volume_liquid": 0.0035,
        "specific_volume_vapor": 0.0035,
    }


def test_30c_point_gives_the_values_from_the_diagram():
    assert saturation_volumes(0.05) == {
        "specific_volume_liquid": 0.00105,
        "specific_volume_vapor": 30.0,
    }


def test_midpoint_pressure_interpolates_each_line_linearly():
    volumes = saturation_volumes(5)

    assert volumes["specific_volume_liquid"] == pytest.approx(0.00226884, abs=1e-8)
    assert volumes["specific_volume_vapor"] == pytest.approx(15.07712, abs=1e-5)


@pytest.mark.parametrize("pressure", [0.05, 0.1, 1, 2.5, 5, 7.77, 9.99, 10])
def test_liquid_volume_is_always_below_vapor_volume_until_the_critical_point(pressure):
    volumes = saturation_volumes(pressure)

    assert volumes["specific_volume_liquid"] <= volumes["specific_volume_vapor"]


def test_volumes_move_toward_the_critical_volume_as_pressure_rises():
    low, high = saturation_volumes(1), saturation_volumes(9)

    assert low["specific_volume_liquid"] < high["specific_volume_liquid"] < 0.0035
    assert low["specific_volume_vapor"] > high["specific_volume_vapor"] > 0.0035


@pytest.mark.parametrize("pressure", [0.049, 0, -1, 10.01, 11])
def test_saturation_volumes_rejects_pressures_outside_the_probed_range(pressure):
    with pytest.raises(ValueError):
        saturation_volumes(pressure)


def test_endpoint_matches_the_example_from_the_statement():
    response = client.get("/phase-change-diagram", params={"pressure": 10})

    assert response.status_code == 200
    assert response.json() == {"specific_volume_liquid": 0.0035, "specific_volume_vapor": 0.0035}


def test_endpoint_rejects_out_of_range_and_missing_pressure_with_422():
    assert client.get("/phase-change-diagram", params={"pressure": 11}).status_code == 422
    assert client.get("/phase-change-diagram", params={"pressure": 0.01}).status_code == 422
    assert client.get("/phase-change-diagram").status_code == 422
    assert client.get("/phase-change-diagram", params={"pressure": "abc"}).status_code == 422


def test_the_exercise_7_routes_still_work_in_the_same_app():
    assert client.get("/status").status_code == 200
    assert client.get("/repair-bay").status_code == 200
    assert client.post("/teapot").status_code == 418


def test_solve_without_url_raises():
    with pytest.raises(ValueError):
        solve(Mock())


def test_solve_does_not_register_when_autocheck_fails(monkeypatch):
    monkeypatch.setattr(phase_change, "check_deployment", lambda url: ["roto"])
    api = Mock()

    with pytest.raises(RuntimeError):
        solve(api, url="https://x.example")

    api.post.assert_not_called()


def test_solve_with_dry_run_does_not_register(monkeypatch):
    monkeypatch.setattr(phase_change, "check_deployment", lambda url: [])
    api = Mock()

    solve(api, dry_run=True, url="https://x.example")

    api.post.assert_not_called()


def test_solve_registers_the_url_without_trailing_slash(monkeypatch):
    monkeypatch.setattr(phase_change, "check_deployment", lambda url: [])
    api = Mock()

    solve(api, url="https://x.example/")

    api.post.assert_called_once_with(SOLUTION_PATH, {"base_url": "https://x.example"})
