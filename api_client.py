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


class ApiClient:
    def __init__(self):
        _load_env()
        self.base_url = os.environ.get("BASE_URL", "https://makers-challenge.altscore.ai")
        self.headers = {"API-KEY": os.environ.get("API_KEY", "")}

    def get(self, path):
        response = requests.get(self.base_url + path, headers=self.headers, timeout=10)
        return response.json()

    def post(self, path, body):
        response = requests.post(self.base_url + path, headers=self.headers, json=body, timeout=10)
        return response.json()
