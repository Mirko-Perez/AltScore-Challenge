from unittest.mock import Mock

from missions.e4_elven_forge import SOLUTION_PATH, build_credentials, solve


def test_build_credentials_joins_into_the_tolkien_quote():
    credentials = build_credentials()

    assert f"{credentials['username']} {credentials['password']}" == (
        "Not all those who wander are lost"
    )


def test_solve_with_dry_run_does_not_post():
    client = Mock()

    solve(client, dry_run=True)

    client.post.assert_not_called()


def test_solve_posts_credentials_once():
    client = Mock()

    solve(client)

    client.post.assert_called_once_with(
        SOLUTION_PATH, {"username": "Not all those who wander", "password": "are lost"}
    )
