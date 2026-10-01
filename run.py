import argparse

from api_client import ApiClient
from missions import (
    e1_silent_probe,
    e2_kepler_oracle,
    e3_sith_temple,
    e4_elven_forge,
    e5_valiant_defense,
)

MISSIONS = {
    "e1-silent-probe": e1_silent_probe.solve,
    "e2-kepler-oracle": e2_kepler_oracle.solve,
    "e3-sith-temple": e3_sith_temple.solve,
    "e4-elven-forge": e4_elven_forge.solve,
    "e5-valiant-defense": e5_valiant_defense.solve,
}

parser = argparse.ArgumentParser()
parser.add_argument("mission", choices=MISSIONS)
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--resume", action="store_true", help="solo e5: no llama a start")
args = parser.parse_args()
extra = {"resume": True} if args.resume else {}
MISSIONS[args.mission](ApiClient(), dry_run=args.dry_run, **extra)
