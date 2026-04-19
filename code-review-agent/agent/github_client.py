import os
import time

import httpx
import jwt
from dotenv import load_dotenv
from github import Auth, Github

load_dotenv()


def _clear_broken_local_proxies() -> None:
    """Unset placeholder localhost proxy values that break outbound GitHub calls."""
    proxy_keys = [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "GIT_HTTP_PROXY",
        "GIT_HTTPS_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ]
    for key in proxy_keys:
        value = os.environ.get(key, "")
        if "127.0.0.1:9" in value or "localhost:9" in value:
            os.environ.pop(key, None)


def _read_private_key() -> str:
    key_path = os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH", "")
    if key_path and os.path.exists(key_path):
        with open(key_path, encoding="utf-8") as handle:
            return handle.read()
    return os.environ.get("GITHUB_APP_PRIVATE_KEY", "")


def get_github_client() -> Github:
    """Authenticate as a GitHub App installation or fall back to public GitHub."""
    _clear_broken_local_proxies()
    app_id = os.environ["GITHUB_APP_ID"]
    private_key = _read_private_key()
    if not private_key:
        return Github()

    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 540, "iss": app_id}
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    with httpx.Client(timeout=30.0, trust_env=False) as client:
        resp = client.get("https://api.github.com/app/installations", headers=headers)
        resp.raise_for_status()
        installations = resp.json()
        if not installations:
            return Github()

        installation_id = installations[0]["id"]
        token_resp = client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=headers,
        )
        token_resp.raise_for_status()
        token = token_resp.json()["token"]

    return Github(auth=Auth.Token(token))
