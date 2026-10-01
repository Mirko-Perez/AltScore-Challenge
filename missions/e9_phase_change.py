"""S1E9 - Nave a la deriva, parte 2: datos corruptos, el cambio de fase y un cuaderno garabateado
(300 puntos).

El robot reparador detecta datos corruptos de la curva de saturación y cambio de fase P-v del
fluido hidráulico. Hará 10 peticiones a /phase-change-diagram para reconstruir el archivo.

    [GET] /phase-change-diagram?pressure=10      (presión en megapascales)
      -> {"specific_volume_liquid": 0.0035, "specific_volume_vapor": 0.0035}
    [POST] /v1/s1/e9/solution -> body {"base_url": "https://tu-api"}

Reglas de entrega: Python, TypeScript o Go; la URL debe ser accesible desde el exterior; tras
registrarla hay 3 intentos y 5 minutos para que el robot repare el sistema.

El dibujo del cuaderno (diagrama P-v, presión en MPa contra volumen específico en m^3/kg):
    - Punto crítico: Pc = 10 MPa, Tc = 500 °C, vc = 0.0035 m^3/kg.
    - Línea de líquido saturado (izquierda) y de vapor saturado (derecha): rectas que se unen en
      el punto crítico.
    - Isoterma de 30 °C: cruza el líquido en (v = 0.00105, P = 0.05 MPa) y el vapor en
      (v = 30.00, P = 0.05 MPa).
    - Nota: "Repair robot will probe only T > 30°C!" -> solo se consultan presiones entre
      0.05 MPa (30 °C) y 10 MPa (punto crítico).

Razonamiento: cada línea es una recta y queda definida por dos puntos (su extremo a 30 °C y el
punto crítico). Dada una presión P, el volumen se interpola linealmente:
    v(P) = vc + (v30 - vc) * (Pc - P) / (Pc - P30)
Anclada en el punto crítico, a P = 10 MPa da exactamente 0.0035 para ambas líneas.
Presiones fuera de [0.05, 10] MPa se rechazan con 422.

Esta ruta se monta en la misma API del ejercicio 7 (missions.e7_drifting_ship:app), que es la
que está desplegada en Render. Autocheck: `python run.py e9-phase-change --url https://tu-api
--dry-run`.
"""

import random

import requests
from fastapi import APIRouter, Query

SOLUTION_PATH = "/v1/s1/e9/solution"
PRESSURE_CRITICAL = 10.0  # MPa
PRESSURE_30C = 0.05  # MPa, presión de saturación a 30 °C
VOLUME_CRITICAL = 0.0035  # m^3/kg
VOLUME_LIQUID_30C = 0.00105  # m^3/kg
VOLUME_VAPOR_30C = 30.00  # m^3/kg
DECIMALS = 10
CHECKS = 10

router = APIRouter()


def interpolate_volume(pressure, volume_at_30c):
    """Recta entre el punto de 30 °C y el punto crítico, anclada en el punto crítico."""
    fraction = (PRESSURE_CRITICAL - pressure) / (PRESSURE_CRITICAL - PRESSURE_30C)
    return VOLUME_CRITICAL + (volume_at_30c - VOLUME_CRITICAL) * fraction


def saturation_volumes(pressure):
    """Volúmenes específicos de líquido y vapor saturados a `pressure` (MPa)."""
    if not PRESSURE_30C <= pressure <= PRESSURE_CRITICAL:
        raise ValueError(f"La presión debe estar entre {PRESSURE_30C} y {PRESSURE_CRITICAL} MPa")
    return {
        "specific_volume_liquid": round(interpolate_volume(pressure, VOLUME_LIQUID_30C), DECIMALS),
        "specific_volume_vapor": round(interpolate_volume(pressure, VOLUME_VAPOR_30C), DECIMALS),
    }


@router.get("/phase-change-diagram")
def phase_change_diagram(pressure: float = Query(..., ge=PRESSURE_30C, le=PRESSURE_CRITICAL)):
    return saturation_volumes(pressure)


def check_deployment(base_url, timeout=10, checks=CHECKS):
    """Simula al robot (varias presiones válidas) y devuelve la lista de problemas."""
    base_url = base_url.rstrip("/")
    pressures = [PRESSURE_CRITICAL, PRESSURE_30C] + [
        round(random.uniform(PRESSURE_30C, PRESSURE_CRITICAL), 3) for _ in range(checks - 2)
    ]
    problems = []
    try:
        for pressure in pressures:
            response = requests.get(
                f"{base_url}/phase-change-diagram", params={"pressure": pressure}, timeout=timeout
            )
            expected = saturation_volumes(pressure)
            ok = response.status_code == 200 and response.json() == expected
            print(f"  GET ?pressure={pressure} -> {response.status_code} {response.text.strip()}")
            if not ok:
                problems.append(f"pressure={pressure}: {response.status_code} {response.text!r}")
        out_of_range = requests.get(
            f"{base_url}/phase-change-diagram", params={"pressure": 11}, timeout=timeout
        )
        print(f"  GET ?pressure=11 (fuera de rango) -> {out_of_range.status_code}")
        if out_of_range.status_code != 422:
            problems.append(f"pressure=11 debía dar 422 y dio {out_of_range.status_code}")
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
