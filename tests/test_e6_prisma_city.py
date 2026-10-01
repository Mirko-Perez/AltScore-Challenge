import json
from unittest.mock import Mock

import pytest

import missions.e6_prisma_city as prisma_city
from missions.e6_prisma_city import SOLUTION_PATH, TYPES, compute_average_heights, solve

DATASET = {
    "types": {"water": ["a", "b"], "fire": ["a", "c"], "bug": ["c"]},
    "heights": {"a": 10, "b": 7, "c": 4},
}


def test_compute_average_heights_averages_each_type():
    averages = compute_average_heights(DATASET)

    assert averages == {"bug": 4.0, "fire": 7.0, "water": 8.5}


def test_compute_average_heights_orders_types_alphabetically():
    assert list(compute_average_heights(DATASET)) == ["bug", "fire", "water"]


def test_compute_average_heights_rounds_to_three_decimals():
    dataset = {"types": {"bug": ["a", "b", "c"]}, "heights": {"a": 1, "b": 1, "c": 2}}

    assert compute_average_heights(dataset) == {"bug": 1.333}


def test_compute_average_heights_with_empty_type_raises():
    with pytest.raises(ValueError):
        compute_average_heights({"types": {"bug": []}, "heights": {}})


def test_types_match_the_api_schema():
    assert list(TYPES) == sorted(TYPES)
    assert len(TYPES) == 18


@pytest.fixture
def dataset_file(tmp_path, monkeypatch):
    path = tmp_path / "heights.json"
    path.write_text(json.dumps(DATASET))
    monkeypatch.setattr(prisma_city, "DATASET_PATH", path)


def test_solve_with_dry_run_does_not_post(dataset_file):
    client = Mock()

    solve(client, dry_run=True)

    client.post.assert_not_called()


def test_solve_posts_heights_once(dataset_file):
    client = Mock()

    solve(client)

    client.post.assert_called_once_with(
        SOLUTION_PATH, {"heights": {"bug": 4.0, "fire": 7.0, "water": 8.5}}
    )
