import argparse

from api_client import ApiClient
from missions import silent_probe

MISSIONS = {"silent-probe": silent_probe.solve}

parser = argparse.ArgumentParser()
parser.add_argument("mission", choices=MISSIONS)
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()
MISSIONS[args.mission](ApiClient(), dry_run=args.dry_run)
