import base64
from unittest.mock import Mock

import pytest

import missions.e8_magic_door as magic_door
from missions.e8_magic_door import (
    SOLUTION_PATH,
    build_message,
    decode_cookie,
    open_doors,
    solve,
    wait_for_second_zero,
)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(magic_door.time, "sleep", lambda _: None)


def encode(word, quoted=True, padded=True):
    value = base64.b64encode(word.encode()).decode()
    value = value if padded else value.rstrip("=")
    return f'"{value}"' if quoted else value


def door_response(word=None, status=200, text='{"response":"Correcto"}'):
    cookies = {} if word is None else {"gryffindor": encode(word)}
    return Mock(status_code=status, text=text, cookies=cookies)


def final_response():
    return door_response(text='{"response":"Has llegado al final. Usa revelio."}')


@pytest.mark.parametrize(
    "value, expected",
    [
        ('"QWx0d2FydHM="', "Altwarts"),
        ("cmV2ZWxh", "revela"),
        ('"Y8OzbW8="', "cómo"),
        ("Y29u", "con"),
        (encode("desafíos.", quoted=False, padded=False), "desafíos."),
    ],
)
def test_decode_cookie_handles_quotes_padding_and_accents(value, expected):
    assert decode_cookie(value) == expected


def test_open_doors_collects_words_in_order_until_the_final_door():
    session = Mock()
    session.post.side_effect = [door_response("uno"), door_response("dos"), final_response()]

    assert open_doors(session, "https://x/door") == ["uno", "dos"]
    assert session.post.call_count == 3


def test_open_doors_does_not_count_the_stale_cookie_of_the_final_door():
    final = door_response("continuamente", text='{"response":"Has llegado al final."}')
    session = Mock()
    session.post.side_effect = [door_response("continuamente"), final]

    assert open_doors(session, "https://x/door") == ["continuamente"]


def test_open_doors_with_forbidden_door_raises_with_the_hint():
    session = Mock()
    session.post.return_value = door_response(
        status=403, text='{"detail":"Siempre es bueno un atajo"}'
    )

    with pytest.raises(RuntimeError, match="403.*atajo"):
        open_doors(session, "https://x/door")


def test_open_doors_without_cookie_raises():
    session = Mock()
    session.post.return_value = door_response()

    with pytest.raises(RuntimeError, match="cookie"):
        open_doors(session, "https://x/door")


def test_open_doors_stops_after_max_doors():
    session = Mock()
    session.post.side_effect = lambda *a, **k: door_response("x")

    with pytest.raises(RuntimeError, match="No se llegó al final"):
        open_doors(session, "https://x/door", max_doors=3)


def test_build_message_joins_words_with_spaces():
    assert build_message(["Altwarts", "revela", "cómo"]) == "Altwarts revela cómo"


def test_wait_for_second_zero_waits_until_the_next_minute():
    waited = []

    wait_for_second_zero(now=lambda: 600 + 14.0, sleep=waited.append)

    assert waited == [pytest.approx(46.05)]


def test_wait_for_second_zero_does_not_wait_when_already_at_second_zero():
    waited = []

    wait_for_second_zero(now=lambda: 600 + 0.2, sleep=waited.append)

    assert waited == []


def patch_door_flow(monkeypatch, responses):
    session = Mock()
    session.headers = {}
    session.post.side_effect = responses
    monkeypatch.setattr(magic_door.requests, "Session", lambda: session)
    monkeypatch.setattr(magic_door, "wait_for_second_zero", lambda: None)
    return session


def make_client():
    client = Mock()
    client.headers = {"API-KEY": "k"}
    client.base_url = "https://api.example"
    return client


def test_solve_sends_the_spell_header_and_posts_the_joined_message(monkeypatch):
    session = patch_door_flow(
        monkeypatch, [door_response("hola"), door_response("mundo"), final_response()]
    )
    client = make_client()

    message = solve(client)

    assert message == "hola mundo"
    assert session.headers == {"API-KEY": "k", "Revelio": "true"}
    client.post.assert_called_once_with(SOLUTION_PATH, {"hidden_message": "hola mundo"})


def test_solve_with_dry_run_does_not_post_the_solution(monkeypatch):
    patch_door_flow(monkeypatch, [door_response("hola"), final_response()])
    client = make_client()

    solve(client, dry_run=True)

    client.post.assert_not_called()
