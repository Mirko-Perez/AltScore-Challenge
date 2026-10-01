"""S1E6 - La Infiltración en Ciudad Prisma: un desafío para los maestros de datos (100 puntos).

Año 3036: Ciudad Prisma, cerrada durante décadas, esconde un artefacto legendario. Sus guardianes
piden demostrar dominio de los datos de todos los Pokémon.

Misión: calcular la altura promedio de todos los tipos de Pokémon, siguiendo el orden alfabético,
y enviar el valor con una precisión de 3 decimales.

Recursos:
    PokéAPI: https://pokeapi.co/api/v2
        GET /type/{tipo}      -> lista de Pokémon del tipo
        GET /pokemon/{id}     -> altura (`height`, en decímetros)
    [POST] /v1/s1/e6/solution -> body {"heights": {"bug": float, ..., "water": float}}
                                 (18 tipos, de "bug" a "water")

Decisiones: el promedio de cada tipo usa todos los Pokémon que lista PokéAPI para ese tipo
(incluye formas alternativas); un Pokémon de dos tipos cuenta en ambos; la altura se envía tal
como la entrega PokéAPI (decímetros, sin convertir). Se redondea una sola vez, al final.
Los datos se descargan una vez a data/e6_pokemon_heights.json:
`python -m missions.e6_prisma_city`.

Resultado: 1351 Pokémon distintos (los mismos que lista /pokemon/); la API validó los promedios
en decímetros, sin convertir a metros: {"result": "correct"}.
"""

import json
import time
from pathlib import Path

from api_client import get_json_with_retries

POKEAPI_URL = "https://pokeapi.co/api/v2"
SOLUTION_PATH = "/v1/s1/e6/solution"
DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "e6_pokemon_heights.json"
REQUEST_DELAY_S = 0.1
PROGRESS_EVERY = 100
DECIMALS = 3
TYPES = (
    "bug",
    "dark",
    "dragon",
    "electric",
    "fairy",
    "fighting",
    "fire",
    "flying",
    "ghost",
    "grass",
    "ground",
    "ice",
    "normal",
    "poison",
    "psychic",
    "rock",
    "steel",
    "water",
)


def build_dataset(delay_s=REQUEST_DELAY_S):
    """Descarga los Pokémon de cada tipo y la altura de cada Pokémon distinto, una sola vez."""
    members = {}
    urls = {}
    for type_name in TYPES:
        payload = get_json_with_retries(f"{POKEAPI_URL}/type/{type_name}")
        members[type_name] = sorted(entry["pokemon"]["name"] for entry in payload["pokemon"])
        urls.update(
            {entry["pokemon"]["name"]: entry["pokemon"]["url"] for entry in payload["pokemon"]}
        )
        print(f"tipo {type_name}: {len(members[type_name])} pokémon")
        time.sleep(delay_s)

    heights = {}
    for index, (name, url) in enumerate(sorted(urls.items()), start=1):
        heights[name] = get_json_with_retries(url)["height"]
        if index % PROGRESS_EVERY == 0 or index == len(urls):
            print(f"altura {index}/{len(urls)}: {name} = {heights[name]}", flush=True)
        time.sleep(delay_s)
    return {"types": members, "heights": heights}


def save_dataset(dataset, path=DATASET_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataset, indent=2) + "\n", encoding="utf-8")


def load_dataset(path=DATASET_PATH):
    return json.loads(path.read_text(encoding="utf-8"))


def compute_average_heights(dataset):
    """{tipo: altura promedio redondeada a 3 decimales}, con los tipos en orden alfabético."""
    averages = {}
    for type_name in sorted(dataset["types"]):
        names = dataset["types"][type_name]
        if not names:
            raise ValueError(f"El tipo {type_name} no tiene Pokémon")
        averages[type_name] = round(
            sum(dataset["heights"][n] for n in names) / len(names), DECIMALS
        )
    return averages


def print_averages_table(dataset, averages):
    print("\n| Tipo     | Pokémon | Altura promedio |")
    print("|----------|---------|-----------------|")
    for type_name, average in averages.items():
        print(f"| {type_name:<8} | {len(dataset['types'][type_name]):>7} | {average:>15.3f} |")


def solve(client, dry_run=False):
    if not DATASET_PATH.exists():
        print("no existe la foto de datos, consultando PokéAPI...")
        save_dataset(build_dataset(), DATASET_PATH)
    dataset = load_dataset(DATASET_PATH)
    averages = compute_average_heights(dataset)
    print_averages_table(dataset, averages)
    if not dry_run:
        print("respuesta:", client.post(SOLUTION_PATH, {"heights": averages}))
    return averages


if __name__ == "__main__":
    data = build_dataset()
    save_dataset(data)
    print(f"\nguardado en {DATASET_PATH} ({len(data['heights'])} pokémon distintos)")
