import os

import requests


def _load_env(path=".env"):
    if not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _parse_body(response):
    """JSON si se puede; si no, el estado HTTP y el texto crudo para poder diagnosticar."""
    try:
        return response.json()
    except ValueError:
        return f"[HTTP {response.status_code}] {response.text!r}"


class ApiClient:
    def __init__(self):
        _load_env()
        self.base_url = os.environ.get("BASE_URL", "https://makers-challenge.altscore.ai")
        self.headers = {"API-KEY": os.environ.get("API_KEY", "")}

    def get(self, path, params=None):
        response = requests.get(
            self.base_url + path, headers=self.headers, params=params, timeout=10
        )
        return _parse_body(response)

    def post(self, path, body):
        response = requests.post(self.base_url + path, headers=self.headers, json=body, timeout=10)
        return _parse_body(response)
