import argparse

from api_client import ApiClient
from missions import e1_silent_probe, e2_kepler_oracle

MISSIONS = {
    "e1-silent-probe": e1_silent_probe.solve,
    "e2-kepler-oracle": e2_kepler_oracle.solve,
}

parser = argparse.ArgumentParser()
parser.add_argument("mission", choices=MISSIONS)
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()
MISSIONS[args.mission](ApiClient(), dry_run=args.dry_run)
