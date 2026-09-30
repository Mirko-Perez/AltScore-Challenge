"""S1E1 - La Sonda Silenciosa (100 puntos).

Misión: mapear un sistema solar recién descubierto y determinar la velocidad orbital
instantánea de un planeta potencialmente habitable.

Desafío: la interferencia cósmica hace que el escáner de largo alcance falle casi siempre
(siempre responde HTTP 200, incluso cuando el escaneo no es exitoso).

Cuando el escáner funciona devuelve:
    distance: distancia recorrida por el planeta en su órbita (unidades astronómicas).
    time: tiempo transcurrido durante la observación (horas).

Objetivo: calcular la velocidad orbital hasta el número entero más cercano (UA/h).

Recursos:
    [GET]  /v1/s1/e1/resources/measurement  -> {"distance": str, "time": str}
    [POST] /v1/s1/e1/solution               -> body {"speed": int}, responde {"result": str}

Resultado: velocidad 405, la API respondió {"result": "correct"}.
"""

import re
import time
from collections import Counter

MEASUREMENT_PATH = "/v1/s1/e1/resources/measurement"
SOLUTION_PATH = "/v1/s1/e1/solution"
REQUIRED_MATCHES = 3
MAX_ATTEMPTS = 1000
RETRY_DELAY_S = 0.3
PROGRESS_EVERY = 10


def parse_number(text):
    """First number in the text, or None if there is none (failed reading)."""
    if not isinstance(text, str):
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def compute_speed(distance, time_h):
    return round(distance / time_h)


def is_valid_reading(raw):
    distance = parse_number(raw.get("distance"))
    time_h = parse_number(raw.get("time"))
    return distance is not None and time_h is not None and time_h > 0


def collect_confirmed_speed(
    client,
    required_matches=REQUIRED_MATCHES,
    max_attempts=MAX_ATTEMPTS,
    delay_s=RETRY_DELAY_S,
):
    """Lee hasta que `required_matches` lecturas válidas den la misma velocidad.

    Devuelve (velocidad, aciertos, fallidas).
    """
    speeds = Counter()
    hits = 0
    for attempt in range(1, max_attempts + 1):
        raw = client.get(MEASUREMENT_PATH)
        if is_valid_reading(raw):
            hits += 1
            speed = compute_speed(parse_number(raw["distance"]), parse_number(raw["time"]))
            speeds[speed] += 1
            print(
                f"intento {attempt}/{max_attempts}: distance={raw['distance']!r} "
                f"time={raw['time']!r} -> velocidad={speed} ({speeds[speed]}/{required_matches})",
                flush=True,
            )
            if speeds[speed] >= required_matches:
                return speed, hits, attempt - hits
        elif attempt % PROGRESS_EVERY == 0:
            print(f"intento {attempt}/{max_attempts}: aciertos={hits}", flush=True)
        if attempt < max_attempts:
            time.sleep(delay_s)
    raise RuntimeError(
        f"Sin {required_matches} lecturas iguales tras {max_attempts} intentos "
        f"(aciertos={hits}, velocidades={dict(speeds)})"
    )


def print_summary(hits, failures):
    print("\n| Lecturas | Cantidad |")
    print("|----------|----------|")
    print(f"| Aciertos | {hits:>8} |")
    print(f"| Fallidas | {failures:>8} |")


def solve(client, dry_run=False):
    speed, hits, failures = collect_confirmed_speed(client)
    print(f"velocidad confirmada={speed}")
    if not dry_run:
        print("respuesta:", client.post(SOLUTION_PATH, {"speed": speed}))
    print_summary(hits, failures)
    return speed
