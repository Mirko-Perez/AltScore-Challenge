"""S1E5 - La Última Defensa de la "Valiant" - ¡Cuenta Regresiva! (300 puntos).

Una nave enemiga se acerca a la nave de suministros "Hope" por la ruta más directa, esquivando
obstáculos. Hay un único disparo que debe caer en las coordenadas exactas donde estará el
enemigo al momento del impacto. Son 4 turnos (cada uno: leer el radar o atacar) y 10 minutos
desde que se llama a `start`; solo hay un intento.

Cuadrícula de 8x8, de "a1" a "h8". Símbolos: "^" enemigo, "#" Hope, "$" obstáculo, "0" libre.
El radar es texto sin formato; cada celda son 3 caracteres (columna, símbolo, fila) y "|"
separa las filas. Ejemplo (bitácora, última lectura de la batalla anterior):

    a01b01c01d01e01f01g01h01|a02b02c02d02e$2f02g02h02|a03b03c03d03e03f03g03h$3|...

Captura de la bitácora. Las columnas son letras de izquierda a derecha y las filas números de
ABAJO hacia ARRIBA (la fila 8 es la de más arriba):
         a b c d e f g h
     8   0 0 0 0 0 # 0 0        Hope en f8
     7   0 0 0 0 0 0 0 0
     6   0 0 0 0 $ 0 0 0        obstáculo e6
     5   0 0 0 0 $ 0 ^ 0        obstáculo e5, enemigo en g5
     4   0 0 0 0 0 0 0 0
     3   0 0 0 0 0 0 0 $        obstáculo h3
     2   0 0 0 0 $ 0 0 0        obstáculo e2
     1   0 0 0 0 0 0 0 0

Recursos:
    [POST] /v1/s1/e5/actions/start         -> "string" (inicia la batalla y el reloj)
    [POST] /v1/s1/e5/actions/perform-turn  -> body {"action": "radar"|"attack",
           "attack_position": {"x": "a".."h", "y": 1..8} | null}; responde
           {performed_action, turns_remaining, time_remaining, action_result, message}

Estrategia: 3 lecturas del radar para observar el movimiento del enemigo y el 4º turno
dispara a la celda donde estará.

Resultado (batalla real): el enemigo se mueve como un CABALLO DE AJEDREZ (saltos en L de
(±1, ±2) o (±2, ±1)), siempre por el camino de menos saltos hacia Hope; los obstáculos bloquean
la casilla de llegada. Lecturas: b1 -> a3 -> b5, con Hope en e8 y obstáculos c3, c4, d2, d6.
El camino mínimo era b1 -> a3 -> b5 -> c7 -> e8 (4 saltos = 4 turnos); tras la 3ª lectura el
enemigo saltaba a c7. Se disparó a c7 y la API respondió "You hit the target, congratulations".
Aprendizaje: una primera versión modelaba el movimiento como pasos rectos/diagonales y predecía
mal (d7); lo corrigió mirar la forma de los saltos observados.

Batalla real (1, 2 y 3 = lecturas del radar, X = disparo, # = Hope). Es otro tablero que el de
la bitácora de arriba:
         a b c d e f g h
     8   . . . . # . . .      Hope en e8
     7   . . X . . . . .      disparo a c7 (acertó)
     6   . . . $ . . . .      obstáculo d6
     5   . 3 . . . . . .      lectura 3: enemigo en b5
     4   . . $ . . . . .      obstáculo c4
     3   2 . $ . . . . .      lectura 2: enemigo en a3, obstáculo c3
     2   . . . $ . . . .      obstáculo d2
     1   . 1 . . . . . .      lectura 1: enemigo en b1
    b1 -(-1,+2)-> a3 -(+1,+2)-> b5 -(+1,+2)-> c7 -(+2,+1)-> e8
Desde b1 las salidas c3 y d2 son obstáculos (solo queda a3); desde b5 el salto a d6 está
bloqueado (queda c7, a un salto de Hope).

`--dry-run` ensaya todo contra un simulador local, sin llamar a la API.
"""

import re
from collections import deque
from functools import lru_cache
from typing import NamedTuple

START_PATH = "/v1/s1/e5/actions/start"
TURN_PATH = "/v1/s1/e5/actions/perform-turn"
COLUMNS = "abcdefgh"
SIZE = 8
READS = 3
LOGBOOK_RADAR = (
    "a01b01c01d01e01f01g01h01|a02b02c02d02e$2f02g02h02|a03b03c03d03e03f03g03h$3|"
    "a04b04c04d04e04f04g04h04|a05b05c05d05e$5f05g^5h05|a06b06c06d06e$6f06g06h06|"
    "a07b07c07d07e07f07g07h07|a08b08c08d08e08f#8g08h08|"
)
CELL_PATTERN = re.compile(r"([a-h])([0$#^])([1-8])")
LABEL_PATTERN = re.compile(r"^[a-h][1-8]$")
KNIGHT_MOVES = (
    (1, 2),
    (2, 1),
    (2, -1),
    (1, -2),
    (-1, -2),
    (-2, -1),
    (-2, 1),
    (-1, 2),
)


class Board(NamedTuple):
    enemy: tuple
    hope: tuple
    obstacles: frozenset


def to_label(position):
    x, y = position
    return f"{COLUMNS[x]}{y}"


def from_label(label):
    return COLUMNS.index(label[0]), int(label[1])


def parse_radar(text):
    cells = CELL_PATTERN.findall(text)
    if len(cells) != SIZE * SIZE:
        raise ValueError(f"El radar debe tener {SIZE * SIZE} celdas y tiene {len(cells)}")
    enemy = hope = None
    obstacles = set()
    for letter, symbol, row in cells:
        position = (COLUMNS.index(letter), int(row))
        if symbol == "^":
            enemy = position
        elif symbol == "#":
            hope = position
        elif symbol == "$":
            obstacles.add(position)
    if enemy is None or hope is None:
        raise ValueError("El radar no muestra al enemigo o a la nave Hope")
    return Board(enemy, hope, frozenset(obstacles))


def encode_radar(board):
    symbols = {board.enemy: "^", board.hope: "#", **{o: "$" for o in board.obstacles}}
    rows = []
    for y in range(1, SIZE + 1):
        rows.append("".join(f"{COLUMNS[x]}{symbols.get((x, y), '0')}{y}" for x in range(SIZE)))
    return "|".join(rows) + "|"


REAL_BATTLE_RADAR = encode_radar(
    Board(from_label("b1"), from_label("e8"), frozenset(map(from_label, ["c3", "c4", "d2", "d6"])))
)


def knight_jumps(position):
    for dx, dy in KNIGHT_MOVES:
        x, y = position[0] + dx, position[1] + dy
        if 0 <= x < SIZE and 1 <= y <= SIZE:
            yield x, y


@lru_cache(maxsize=None)
def jumps_to_hope(obstacles, hope):
    """BFS desde Hope: saltos mínimos de cada casilla hasta la nave amiga (sin pisar obstáculos)."""
    distances = {hope: 0}
    queue = deque([hope])
    while queue:
        current = queue.popleft()
        for cell in knight_jumps(current):
            if cell not in obstacles and cell not in distances:
                distances[cell] = distances[current] + 1
                queue.append(cell)
    return distances


def next_jumps(board, position):
    """Casillas a las que puede saltar el enemigo para acercarse a Hope por un camino mínimo."""
    distances = jumps_to_hope(board.obstacles, board.hope)
    if position not in distances:
        return []
    return [
        cell for cell in knight_jumps(position) if distances.get(cell) == distances[position] - 1
    ]


def predict(board, jumps_ahead=1):
    """Casillas posibles del enemigo tras `jumps_ahead` saltos más (varias si hay empate)."""
    positions = {board.enemy}
    for _ in range(jumps_ahead):
        positions = {cell for position in positions for cell in next_jumps(board, position)}
    return sorted(positions)


def explains_readings(boards):
    """True si cada lectura es uno de los saltos mínimos posibles desde la anterior."""
    return all(b.enemy in next_jumps(a, a.enemy) for a, b in zip(boards, boards[1:]))


class SimulatedBattleClient:
    """Ensaya el flujo sin tocar la API (por defecto con el tablero de la batalla real).

    El disparo se resuelve primero y luego el enemigo salta.
    """

    def __init__(self, radar=REAL_BATTLE_RADAR, turns=4):
        self.board = parse_radar(radar)
        self.turns = turns

    def post(self, path, body=None):
        if path == START_PATH:
            return "Simulación iniciada"
        action = body["action"]
        self.turns -= 1
        result = encode_radar(self.board) if action == "radar" else ""
        if action == "attack":
            target = body["attack_position"]
            hit = (COLUMNS.index(target["x"]), target["y"]) == self.board.enemy
            result = "hit" if hit else f"miss (el enemigo estaba en {to_label(self.board.enemy)})"
        jumps = next_jumps(self.board, self.board.enemy)
        if jumps:
            self.board = self.board._replace(enemy=jumps[0])
        return {
            "performed_action": action,
            "turns_remaining": self.turns,
            "time_remaining": 600,
            "action_result": result,
            "message": "",
        }


def read_radar(client):
    response = client.post(TURN_PATH, {"action": "radar", "attack_position": None})
    for text in (response["action_result"], response["message"]):
        try:
            return parse_radar(text), response
        except ValueError:
            continue
    raise RuntimeError(f"No se pudo interpretar el radar: {response}")


def choose_target(candidates, confirm):
    best = to_label(candidates[0]) if len(candidates) == 1 else None
    if candidates:
        print("\ncasillas posibles tras el próximo salto: " + ", ".join(map(to_label, candidates)))
    else:
        print("\nEl modelo de caballo no da ninguna casilla: hay que decidir a mano.")
    default = f"Enter = disparar a {best} | " if best else ""
    prompt = f"{default}celda (ej. c7) | n = cancelar: "
    while True:
        answer = (confirm(prompt) or best or "").strip().lower()
        if answer == "n":
            return None
        if LABEL_PATTERN.match(answer):
            return from_label(answer)
        print("Celda inválida, usa una letra a-h y un número 1-8.")


def solve(client, dry_run=False, reads=READS, confirm=input, resume=False):
    if dry_run:
        client, confirm = SimulatedBattleClient(), lambda _: ""
        print("DRY-RUN: simulador local, no se llama a la API")
    if resume:
        print("RESUME: se omite start, la batalla ya fue iniciada")
    else:
        print("start:", client.post(START_PATH, None))
    boards = []
    for number in range(1, reads + 1):
        board, response = read_radar(client)
        boards.append(board)
        print(
            f"lectura {number}/{reads}: enemigo={to_label(board.enemy)} "
            f"hope={to_label(board.hope)} obstáculos={sorted(map(to_label, board.obstacles))} "
            f"turnos={response['turns_remaining']} tiempo={response['time_remaining']}s"
        )
    if not explains_readings(boards):
        print("AVISO: las lecturas no encajan con saltos de caballo hacia Hope.")
    target = choose_target(predict(boards[-1]), confirm)
    if target is None:
        print("Ataque cancelado. El intento sigue abierto hasta que expire el reloj.")
        return None
    attack = {"action": "attack", "attack_position": {"x": COLUMNS[target[0]], "y": target[1]}}
    response = client.post(TURN_PATH, attack)
    print("respuesta:", response)
    return response
