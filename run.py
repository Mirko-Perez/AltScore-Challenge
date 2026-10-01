import argparse

from api_client import ApiClient
from missions import (
    e1_silent_probe,
    e2_kepler_oracle,
    e3_sith_temple,
    e4_elven_forge,
    e5_valiant_defense,
    e6_prisma_city,
    e7_drifting_ship,
    e8_magic_door,
    e9_phase_change,
)

MISSIONS = {
    "e1-silent-probe": e1_silent_probe.solve,
    "e2-kepler-oracle": e2_kepler_oracle.solve,
    "e3-sith-temple": e3_sith_temple.solve,
    "e4-elven-forge": e4_elven_forge.solve,
    "e5-valiant-defense": e5_valiant_defense.solve,
    "e6-prisma-city": e6_prisma_city.solve,
    "e7-drifting-ship": e7_drifting_ship.solve,
    "e8-magic-door": e8_magic_door.solve,
    "e9-phase-change": e9_phase_change.solve,
}

parser = argparse.ArgumentParser()
parser.add_argument("mission", choices=MISSIONS)
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--url", help="solo e7 y e9: URL pública de tu API")
parser.add_argument("--resume", action="store_true", help="solo e5: no llama a start")
args = parser.parse_args()
extra = {"resume": True} if args.resume else {}
if args.url:
    extra["url"] = args.url
MISSIONS[args.mission](ApiClient(), dry_run=args.dry_run, **extra)
