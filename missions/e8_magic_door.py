"""S1E8 - El Hechizo de la Puerta Mágica (150 puntos).

En la biblioteca de Altwarts los fundadores escondieron un conocimiento protegido por "El
Encantamiento de la Puerta Mágica". Cada pista acerca a la solución final.

Pistas:
    1. El Reloj de los Segundos: solo en el primer segundo se encuentra la llave de la primera
       puerta.
    2. Acción y reacción: las palabras ocultas están en las consecuencias (la respuesta), no en
       el hechizo.
    3. N puertas alineadas, cada una desbloqueada por una palabra; hay que avanzar en orden y en
       el momento adecuado.
    4. Cada puerta lleva a la siguiente, pero la respuesta es el camino mismo. Usar "Revelio"
       para ver lo oculto.

Recursos:
    [POST] /v1/s1/e8/actions/door -> abre una puerta (no siempre devuelve 200; los errores dan
                                     pistas)
    [POST] /v1/s1/e8/solution     -> body {"hidden_message": str}

Razonamiento (descubierto leyendo los errores):
    - Sin nada, la puerta responde 403 "Siempre es bueno un atajo, pero no en este caso".
    - Funciona con el encabezado `Revelio: true` llamando en el SEGUNDO 00 del minuto (la
      "primera pista"); en cualquier otro segundo vuelve a dar 403.
    - Cada respuesta trae una cookie `gryffindor` con una palabra en Base64 (la "reacción"). La
      siguiente llamada la devuelve (con una sesión de requests va sola) y abre la próxima puerta.
    - Son 26 puertas con palabra; la 27ª dice "Has llegado al final" y no trae cookie nueva.
    - El mensaje oculto es el camino: las palabras en orden, separadas por espacios.

Resultado (la API respondió {"result": "correct"}, sin punto final en la frase):
"Altwarts revela cómo la magia surge mediante perseverancia, precisión y esmero al
enfrentar desafíos. Cada detalle importa; auténtica destreza se refleja con dedicación para
mejorar continuamente".
"""

import base64
import time

import requests

DOOR_PATH = "/v1/s1/e8/actions/door"
SOLUTION_PATH = "/v1/s1/e8/solution"
COOKIE_NAME = "gryffindor"
SPELL_HEADER = {"Revelio": "true"}
FINAL_MARKER = "Has llegado al final"
MAX_DOORS = 100
DOOR_DELAY_S = 0.3
FIRST_SECOND_MARGIN_S = 0.05


def decode_cookie(value):
    """Decodifica la palabra en Base64 de la cookie (con o sin comillas y sin relleno '=')."""
    encoded = value.strip('"')
    return base64.b64decode(encoded + "=" * (-len(encoded) % 4)).decode("utf-8")


def wait_for_second_zero(now=time.time, sleep=time.sleep):
    """Espera al segundo 00 del próximo minuto (la puerta 1 solo abre en el primer segundo)."""
    seconds = now() % 60
    if seconds >= 0.5:
        wait = 60 - seconds + FIRST_SECOND_MARGIN_S
        print(f"esperando {wait:.1f}s hasta el segundo 00...")
        sleep(wait)


def open_doors(session, url, delay_s=DOOR_DELAY_S, max_doors=MAX_DOORS):
    """Recorre las puertas en orden y devuelve las palabras recogidas."""
    words = []
    for door in range(1, max_doors + 1):
        response = session.post(url, timeout=15)
        if response.status_code != 200:
            raise RuntimeError(
                f"La puerta {door} respondió {response.status_code}: {response.text.strip()}"
            )
        if FINAL_MARKER in response.text:
            print(f"puerta {door}: {response.text.strip()}")
            return words
        cookie = response.cookies.get(COOKIE_NAME)
        if cookie is None:
            raise RuntimeError(f"La puerta {door} no trajo la cookie {COOKIE_NAME}")
        words.append(decode_cookie(cookie))
        print(f"puerta {door:>2}: {words[-1]}")
        time.sleep(delay_s)
    raise RuntimeError(f"No se llegó al final tras {max_doors} puertas")


def build_message(words):
    return " ".join(words)


def solve(client, dry_run=False):
    session = requests.Session()
    session.headers.update({**client.headers, **SPELL_HEADER})
    wait_for_second_zero()
    words = open_doors(session, client.base_url + DOOR_PATH)
    message = build_message(words)
    print(f"\n{len(words)} palabras\nmensaje oculto: {message}")
    if not dry_run:
        print("respuesta:", client.post(SOLUTION_PATH, {"hidden_message": message}))
    return message
