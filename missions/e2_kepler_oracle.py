"""S1E2 - El Enigma Cósmico de Kepler-452b (100 puntos).

Año 3042: navegante del CSS Hawking, debes contactar al Oráculo de Kepler-452b. Para ser digno
de su sabiduría tienes que resolver su acertijo.

La prueba: una interfaz holográfica muestra la nebulosa estelar "Lyra". Por cada estrella se
obtiene su "resonancia" y sus coordenadas. Hay que calcular la "resonancia promedio" de las
estrellas de la nebulosa.

Pistas:
    - La interfaz navega en "saltos estelares": 3 estrellas por salto (página).
    - "La resonancia de cada estrella se construye sobre la anterior, pero el Oráculo te presenta
      las estrellas en un orden cósmico propio."
    - "Los secretos del cosmos no solo están en los datos visibles, sino también en los susurros
      ocultos en los encabezados de las respuestas."
    - "La paciencia es una virtud, pero la documentación es una herramienta."

Recursos:
    [GET]  /v1/s1/e2/resources/stars?page=N  -> [{"id", "resonance", "position": {x, y, z}}]
           (header x-total-count = cantidad total de estrellas)
    [POST] /v1/s1/e2/solution                -> body {"average_resonance": int}

Notas: la documentación (/openapi.json) muestra parámetros `page`, `sort-by` y `sort-direction`.
El promedio no depende del orden, solo hay que recorrer todas las páginas.

Resultado: 100 estrellas, promedio exacto 388.5. La API validó 388 (truncado), no 389.
"""

import time

STARS_PATH = "/v1/s1/e2/resources/stars"
SOLUTION_PATH = "/v1/s1/e2/solution"
MAX_PAGES = 200
PAGE_DELAY_S = 0.2


def fetch_all_stars(client, max_pages=MAX_PAGES, delay_s=PAGE_DELAY_S):
    """Recorre las páginas hasta que una viene vacía. Devuelve las estrellas sin repetir por id."""
    stars = {}
    for page in range(1, max_pages + 1):
        batch = client.get(STARS_PATH, params={"page": page})
        if not isinstance(batch, list):
            raise RuntimeError(f"Respuesta inesperada en la página {page}: {batch}")
        if not batch:
            break
        for star in batch:
            stars[star["id"]] = star
        time.sleep(delay_s)
    return list(stars.values())


def compute_average_resonance(stars):
    """Promedio de resonancia truncado al entero (388.5 -> 388, como lo valida la API)."""
    if not stars:
        raise ValueError("No hay estrellas para promediar")
    total = sum(star["resonance"] for star in stars)
    return total // len(stars)


def print_summary(stars):
    print("\n| Estrellas | Suma resonancia | Promedio exacto |")
    print("|-----------|-----------------|-----------------|")
    total = sum(star["resonance"] for star in stars)
    print(f"| {len(stars):>9} | {total:>15} | {total / len(stars):>15.2f} |")


def solve(client, dry_run=False):
    stars = fetch_all_stars(client)
    average = compute_average_resonance(stars)
    print_summary(stars)
    print(f"resonancia promedio (entero)={average}")
    if not dry_run:
        print("respuesta:", client.post(SOLUTION_PATH, {"average_resonance": average}))
    return average
