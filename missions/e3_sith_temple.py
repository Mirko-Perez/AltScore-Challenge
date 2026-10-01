"""S1E3 - La Búsqueda del Templo Sith Perdido (100 puntos).

Año Galáctico 34 DBY: la Resistencia interceptó un fragmento de un holocrón Sith con la clave
para localizar un templo Sith perdido. Hay que encontrar el único planeta con equilibrio en la
Fuerza.

Índice de Balance de la Fuerza (IBF) de un planeta, entre -1 (todo Lado Oscuro) y 1 (todo Lado
Luminoso); 0 es equilibrio:

    IBF = (personajes del Lado Luminoso - personajes del Lado Oscuro) / total de personajes

Pistas:
    - Los datos de personajes y planetas salen de SWAPI (https://swapi.dev/api).
    - SWAPI no dice el lado de la Fuerza de cada personaje: se le consulta al oráculo, cuyas
      respuestas vienen codificadas (Base64).

Recursos:
    [GET]  /v1/s1/e3/resources/oracle-rolodex?name=<personaje> -> {"oracle_notes": str (base64)}
    [POST] /v1/s1/e3/solution                                   -> body {"planet": str}

Este módulo arma la "foto" de los datos (data/e3_holocron.json) para consultar las APIs una
sola vez (`python -m missions.e3_sith_temple`) y calcula el IBF de cada planeta sobre esa foto.
Los planetas sin habitantes se excluyen: el total sería 0 y el IBF no está definido.
"""

import base64
import binascii
import json
import re
import time
from pathlib import Path

from api_client import get_json_with_retries

SWAPI_PEOPLE_URL = "https://swapi.dev/api/people/"
SWAPI_PLANETS_URL = "https://swapi.dev/api/planets/"
ORACLE_PATH = "/v1/s1/e3/resources/oracle-rolodex"
SOLUTION_PATH = "/v1/s1/e3/solution"
DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "e3_holocron.json"
REQUEST_DELAY_S = 0.2
SIDE_PATTERN = re.compile(r"belongs to the (Light|Dark) Side", re.IGNORECASE)


def decode_oracle_notes(encoded):
    """Decodifica el Base64 del oráculo; si no es Base64 válido devuelve el texto tal cual."""
    try:
        return base64.b64decode(encoded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return encoded


def classify_side(notes):
    """'light', 'dark' o 'unknown' según la frase 'belongs to the ___ Side'."""
    match = SIDE_PATTERN.search(notes or "")
    return match.group(1).lower() if match else "unknown"


def fetch_swapi_pages(url, delay_s=REQUEST_DELAY_S):
    """Sigue el campo `next` de SWAPI y devuelve todos los resultados."""
    results = []
    while url:
        payload = get_json_with_retries(url)
        results += payload["results"]
        url = payload["next"]
        time.sleep(delay_s)
    return results


def build_dataset(client, delay_s=REQUEST_DELAY_S):
    people = fetch_swapi_pages(SWAPI_PEOPLE_URL, delay_s)
    planets = fetch_swapi_pages(SWAPI_PLANETS_URL, delay_s)
    planet_name_by_url = {planet["url"]: planet["name"] for planet in planets}
    person_name_by_url = {person["url"]: person["name"] for person in people}

    dataset_people = []
    for index, person in enumerate(people, start=1):
        notes = decode_oracle_notes(
            client.get(ORACLE_PATH, params={"name": person["name"]})["oracle_notes"]
        )
        dataset_people.append(
            {
                "name": person["name"],
                "homeworld": planet_name_by_url.get(person["homeworld"]),
                "side": classify_side(notes),
                "oracle_notes": notes,
            }
        )
        print(f"oráculo {index}/{len(people)}: {person['name']} -> {dataset_people[-1]['side']}")
        time.sleep(delay_s)

    dataset_planets = [
        {
            "name": planet["name"],
            "population": planet["population"],
            "residents": [
                person_name_by_url[url] for url in planet["residents"] if url in person_name_by_url
            ],
        }
        for planet in planets
    ]
    return {"planets": dataset_planets, "people": dataset_people}


def save_dataset(dataset, path=DATASET_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_dataset(path=DATASET_PATH):
    return json.loads(path.read_text(encoding="utf-8"))


def compute_force_balance(dataset):
    """IBF por planeta: [{planet, light, dark, total, ibf}], sin planetas sin habitantes."""
    side_by_person = {person["name"]: person["side"] for person in dataset["people"]}
    balances = []
    for planet in dataset["planets"]:
        residents = planet["residents"]
        if not residents:
            continue
        light = sum(1 for name in residents if side_by_person[name] == "light")
        dark = sum(1 for name in residents if side_by_person[name] == "dark")
        balances.append(
            {
                "planet": planet["name"],
                "light": light,
                "dark": dark,
                "total": len(residents),
                "ibf": (light - dark) / len(residents),
            }
        )
    return balances


def find_balanced_planets(balances):
    """Planetas con equilibrio exacto: mismos personajes luminosos que oscuros."""
    return [balance for balance in balances if balance["light"] == balance["dark"]]


def print_balance_table(balances):
    print("\n| Planeta | Luz | Oscuro | Total | IBF |")
    print("|---------|-----|--------|-------|-----|")
    for b in sorted(balances, key=lambda b: abs(b["ibf"])):
        print(f"| {b['planet']} | {b['light']} | {b['dark']} | {b['total']} | {b['ibf']:+.2f} |")


def solve(client, dry_run=False):
    if not DATASET_PATH.exists():
        print("no existe la foto de datos, consultando SWAPI y el oráculo...")
        save_dataset(build_dataset(client))
    balances = compute_force_balance(load_dataset())
    print_balance_table(balances)
    balanced = find_balanced_planets(balances)
    if len(balanced) != 1:
        raise RuntimeError(f"Se esperaba un único planeta en equilibrio y hay {len(balanced)}")
    planet = balanced[0]["planet"]
    print(f"\nplaneta en equilibrio={planet}")
    if not dry_run:
        print("respuesta:", client.post(SOLUTION_PATH, {"planet": planet}))
    return planet


def print_dataset_summary(dataset):
    sides = {"light": 0, "dark": 0, "unknown": 0}
    for person in dataset["people"]:
        sides[person["side"]] += 1
    print("\n| Dato                  | Cantidad |")
    print("|-----------------------|----------|")
    print(f"| Planetas              | {len(dataset['planets']):>8} |")
    print(f"| Personajes            | {len(dataset['people']):>8} |")
    print(f"| Lado Luminoso         | {sides['light']:>8} |")
    print(f"| Lado Oscuro           | {sides['dark']:>8} |")
    print(f"| Sin lado identificado | {sides['unknown']:>8} |")


if __name__ == "__main__":
    from api_client import ApiClient

    data = build_dataset(ApiClient())
    save_dataset(data)
    print(f"\nguardado en {DATASET_PATH}")
    print_dataset_summary(data)
