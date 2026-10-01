"""S1E7 - Nave a la deriva (150 puntos).

Año 2315: estás en una nave a la deriva y un robot de reparación no tripulado se acerca. El robot
identifica y repara sistemas averiados con llamadas HTTP, así que hay que simular una llamada de
auxilio exponiendo una API.

La API debe cumplir:
    GET  /status      -> {"damaged_system": "<uno de los sistemas>"}
    GET  /repair-bay  -> HTML con <div class="anchor-point"> cuyo contenido es el código único del
                         sistema averiado informado por /status:
                           navigation NAV-01 | communications COM-02 | life_support LIFE-03 |
                           engines ENG-04 | deflector_shield SHLD-05
    POST /teapot      -> HTTP 418 (I'm a teapot)

Ejemplo de /repair-bay para "engines":
    <!DOCTYPE html>
    <html>
    <head>
        <title>Repair</title>
    </head>
    <body>
    <div class="anchor-point">ENG-04</div>
    </body>
    </html>

Reglas de entrega: Python, TypeScript o Go; la URL debe ser accesible desde el exterior; tras
registrarla hay solo 3 intentos y 5 minutos para que el robot encuentre la nave.
    [POST] /v1/s1/e7/solution -> body {"base_url": "https://tu-api"}

Razonamiento: /status y /repair-bay tienen que coincidir, así que el servidor recuerda el último
sistema elegido. Antes de registrar la URL (que consume un intento) se prueba la API desde afuera
con un autocheck: `python run.py e7-drifting-ship --url https://tu-api --dry-run`.
Servidor local: `uvicorn missions.e7_drifting_ship:app --port 8000`.

URL desplegada: https://altscore-challenge-arla.onrender.com
    GET  https://altscore-challenge-arla.onrender.com/status
    GET  https://altscore-challenge-arla.onrender.com/repair-bay
    POST https://altscore-challenge-arla.onrender.com/teapot
(Si Render la durmió por inactividad, la primera llamada tarda de 30 a 60 s en despertarla.)

Resultado: desplegada en Render (plan gratis, desde GitHub con render.yaml); el robot completó las
3 comprobaciones al primer intento: {"first_check_complete": true, "second_check_complete": true,
"third_check_complete": true}.
"""

import random
import re

import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from missions.e9_phase_change import router as phase_change_router

SOLUTION_PATH = "/v1/s1/e7/solution"
SYSTEM_CODES = {
    "navigation": "NAV-01",
    "communications": "COM-02",
    "life_support": "LIFE-03",
    "engines": "ENG-04",
    "deflector_shield": "SHLD-05",
}
ANCHOR_PATTERN = re.compile(r'<div class="anchor-point">([^<]*)</div>')
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Repair</title>
</head>
<body>
<div class="anchor-point">{code}</div>
</body>
</html>
"""

app = FastAPI()
app.include_router(phase_change_router)  # ruta del ejercicio 9, misma API desplegada
state = {"damaged_system": random.choice(list(SYSTEM_CODES))}


@app.get("/status")
def status():
    state["damaged_system"] = random.choice(list(SYSTEM_CODES))
    return {"damaged_system": state["damaged_system"]}


@app.get("/repair-bay", response_class=HTMLResponse)
def repair_bay():
    return HTML_TEMPLATE.format(code=SYSTEM_CODES[state["damaged_system"]])


@app.post("/teapot")
def teapot():
    return JSONResponse({"detail": "I'm a teapot"}, status_code=418)


def check_deployment(base_url, timeout=10):
    """Simula al robot contra una URL real y devuelve la lista de problemas (vacía si todo ok)."""
    base_url = base_url.rstrip("/")
    problems = []
    try:
        response = requests.get(f"{base_url}/status", timeout=timeout)
        system = response.json().get("damaged_system")
        if response.status_code != 200 or system not in SYSTEM_CODES:
            problems.append(f"/status devolvió {response.status_code} {response.text!r}")
            return problems
        print(f"  GET /status -> {system}")

        response = requests.get(f"{base_url}/repair-bay", timeout=timeout)
        match = ANCHOR_PATTERN.search(response.text)
        found = match.group(1) if match else None
        print(f"  GET /repair-bay -> anchor-point={found!r} (esperado {SYSTEM_CODES[system]!r})")
        if response.status_code != 200 or found != SYSTEM_CODES[system]:
            problems.append(f"/repair-bay no coincide con el sistema {system}")

        response = requests.post(f"{base_url}/teapot", timeout=timeout)
        print(f"  POST /teapot -> {response.status_code}")
        if response.status_code != 418:
            problems.append(f"/teapot devolvió {response.status_code} en vez de 418")
    except (requests.RequestException, ValueError) as error:
        problems.append(f"no se pudo consultar la API: {error}")
    return problems


def solve(client, dry_run=False, url=None):
    if not url:
        raise ValueError("Falta la URL pública de tu API: usa --url https://tu-api")
    print(f"autocheck de {url}:")
    problems = check_deployment(url)
    if problems:
        raise RuntimeError("La API no pasa el autocheck: " + "; ".join(problems))
    print("autocheck OK")
    if dry_run:
        print("DRY-RUN: no se registra la URL (registrarla consume 1 de los 3 intentos)")
        return None
    response = client.post(SOLUTION_PATH, {"base_url": url.rstrip("/")})
    print("respuesta:", response)
    return response
