"""S1E4 - La Búsqueda de la Forja Élfica Olvidada (100 puntos).

Año 3018 de la Tercera Edad: la Tierra Media está al borde de la guerra y el Anillo Único fue
encontrado. Una forja élfica oculta, usada una vez para fabricar armas capaces de resistir a
Sauron, guarda la entrada tras una puerta de piedra con runas. Hay que descifrar el poema y
descubrir las credenciales ocultas (usuario y contraseña) para entrar.

El poema:
    The Keeper of Secrets, Elven Lore, / Guards the door to ancient war.
    A name in whispers, subtly veiled, / The key to forge the fading light.

    A password cloaked in shadows deep, / Where truth and trust in darkness sleep.
    Reveal the word, but tread with care, / For only those who dare to stare.

    Through webs of spells and runes that guard, / The path to wisdom, worn and hard.
    The quest is yours, the way is paved, / By username in light engraved.

    Password bound by hidden might, / Shift the veil, and find the light.

En la puerta aparecen dos campos:
    Usuario:    ???Not all those who wander
    Contraseña: are lost   (el campo estaba oculto; se reveló cambiando el input a tipo texto)

Recursos:
    [POST] /v1/s1/e4/solution -> body {"username": str, "password": str}

Razonamiento: las dos mitades forman la frase de Tolkien "Not all those who wander are lost".
Los "???" son el velo del usuario y no forman parte de él; la contraseña es "are lost".
"""

SOLUTION_PATH = "/v1/s1/e4/solution"
USERNAME = "Not all those who wander"
PASSWORD = "are lost"


def build_credentials():
    return {"username": USERNAME, "password": PASSWORD}


def solve(client, dry_run=False):
    credentials = build_credentials()
    print(f"usuario={credentials['username']!r} contraseña={credentials['password']!r}")
    if not dry_run:
        print("respuesta:", client.post(SOLUTION_PATH, credentials))
    return credentials
