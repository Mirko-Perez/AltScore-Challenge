import pytest

from missions.e5_valiant_defense import (
    LOGBOOK_RADAR,
    SimulatedBattleClient,
    encode_radar,
    explains_readings,
    from_label,
    next_jumps,
    parse_radar,
    predict,
    solve,
    to_label,
)

BOARD = parse_radar(LOGBOOK_RADAR)


def real_board(enemy):
    """Batalla real: Hope en e8 y obstáculos c3, c4, d2, d6."""
    return BOARD._replace(
        enemy=from_label(enemy),
        hope=from_label("e8"),
        obstacles=frozenset(map(from_label, ["c3", "c4", "d2", "d6"])),
    )


def labels(cells):
    return [to_label(cell) for cell in cells]


def test_parse_radar_reads_logbook_positions():
    assert to_label(BOARD.enemy) == "g5"
    assert to_label(BOARD.hope) == "f8"
    assert sorted(labels(BOARD.obstacles)) == ["e2", "e5", "e6", "h3"]


def test_encode_radar_roundtrips_the_logbook():
    assert encode_radar(BOARD) == LOGBOOK_RADAR


def test_parse_radar_with_wrong_size_raises():
    with pytest.raises(ValueError):
        parse_radar("a01b01|")


def test_labels_roundtrip():
    assert to_label(from_label("g5")) == "g5"


def test_next_jumps_logbook_goes_g5_to_h7_then_f8():
    assert labels(next_jumps(BOARD, BOARD.enemy)) == ["h7"]
    assert labels(predict(BOARD, jumps_ahead=2)) == ["f8"]


def test_next_jumps_from_b1_is_forced_to_a3_because_c3_and_d2_are_obstacles():
    assert labels(next_jumps(real_board("b1"), from_label("b1"))) == ["a3"]


def test_next_jumps_never_lands_on_an_obstacle():
    board = real_board("b5")

    assert "d6" not in labels(next_jumps(board, board.enemy))  # d6 es obstáculo


def test_real_battle_readings_are_explained_by_knight_jumps():
    boards = [real_board("b1"), real_board("a3"), real_board("b5")]

    assert explains_readings(boards)


def test_real_battle_predicts_c7_then_hope():
    board = real_board("b5")

    assert labels(predict(board)) == ["c7"]
    assert labels(predict(board, jumps_ahead=2)) == ["e8"]


def test_straight_line_movement_is_not_explained_by_knight_jumps():
    boards = [real_board("b1"), real_board("b2")]

    assert not explains_readings(boards)


def test_simulated_battle_hits_when_prediction_is_right():
    response = solve(None, dry_run=True)

    assert response["action_result"] == "hit"
    assert response["turns_remaining"] == 0


def test_solve_cancel_does_not_attack():
    client = SimulatedBattleClient()

    assert solve(client, confirm=lambda _: "n") is None
    assert client.turns == 1  # solo se gastaron las 3 lecturas
