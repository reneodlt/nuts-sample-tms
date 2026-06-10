"""
Minimal, dependency-light OAuth2 client_credentials client for the PTM API.

This is the reference implementation a partner TMS copies. It fetches a token
with HTTP Basic auth, caches it until shortly before expiry, and transparently
re-authenticates once on a 401.
"""
import time
import httpx


class PTMClient:
    def __init__(self, base_url, client_id, client_secret, scope, timeout=10.0):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.timeout = timeout
        self._token = None
        self._expires_at = 0.0

    def _fetch_token(self):
        resp = httpx.post(
            f"{self.base_url}/oauth/token/",
            data={"grant_type": "client_credentials", "scope": self.scope},
            auth=(self.client_id, self.client_secret),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        self._token = payload["access_token"]
        self._expires_at = time.monotonic() + float(payload.get("expires_in", 3600)) - 30
        return self._token

    def _bearer(self):
        if not self._token or time.monotonic() >= self._expires_at:
            self._fetch_token()
        return self._token

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {self._bearer()}"
        resp = httpx.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        if resp.status_code == 401:
            self._token = None
            headers["Authorization"] = f"Bearer {self._bearer()}"
            resp = httpx.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        return resp

    def token_info(self):
        if not self._token:
            return {"token": None, "expires_in": 0}
        return {
            "token": self._token[:12] + "…",
            "expires_in": max(0, int(self._expires_at - time.monotonic())),
        }
