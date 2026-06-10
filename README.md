# NUTS Sample TMS — PTM OAuth2 reference client

A minimal Tournament Management System that integrates with
[The Networked Ultimate Timing System (NUTS)](https://poker.reneo.io) over OAuth2
**Client Credentials** (machine-to-machine; no user, no Hanko login). Copy
`ptm_client.py` as the starting point for a real integration.

## How it works

1. The TMS exchanges its `client_id` + `client_secret` for a scoped bearer token
   at `POST /oauth/token/` (HTTP Basic auth).
2. It calls the PTM API with `Authorization: Bearer <token>`.
3. The token is bound to one PTM Organization; everything stays org-scoped.

## Setup

1. **Mint a client on the PTM side** (a PTM administrator runs this from the
   PTM repo root):
   ```bash
   python manage.py create_oauth_client \
     --org <VENUE_CODE> \
     --name "Acme TMS" \
     --scopes tournament.read,tournament.write
   ```
   Copy the printed `client_id` and `client_secret` (shown once).

2. **Configure this app:**
   ```bash
   cp .env.example .env
   # paste client_id / client_secret into .env
   # set PTM_VENUE_CODE to the venue your client is bound to
   pip install -r requirements.txt
   ```

3. **Run it:**
   ```bash
   ./run.sh
   # open http://localhost:8095
   ```

## What to look at

- **Status page** — fetches a token and calls `/api/oauth/whoami/`, showing the
  resolved organization, auth method, and granted scopes.
- **Tournaments** — `GET /api/tournaments/` (needs `tournament.read`), with
  clock buttons per row: start / pause / resume / advance_level / complete,
  each a `POST /api/tournaments/{id}/{action}/` (needs `tournament.write`).
- **New tournament** — `POST /api/tournaments/` with `venue_code` and an inline
  blind structure (needs `tournament.write`).

### Seeing scope enforcement

Scope restriction is enforced at **token issuance**: mint a read-only client
(`--scopes tournament.read`) and watch it get refused a write-scoped token —

```bash
curl -u "$CLIENT_ID:$CLIENT_SECRET" -d grant_type=client_credentials \
  -d scope="tournament.write" https://poker.reneo.io/oauth/token/
# -> {"error":"invalid_scope"}
```

> ⚠️ Note: per-endpoint scope checks on `/api/*` are a planned enhancement — a
> read-only token is not yet refused (`403`) at the write endpoint itself. Today
> the API authorizes by organization, and `allowed_scopes` is the real boundary.
> See the [Integration Guide](docs/oauth2_integration_guide.md#9-error-handling)
> for the full picture.

## Learn more

See the full **[OAuth2 Integration Guide](docs/oauth2_integration_guide.md)**
(concepts, sequence + architecture diagrams, endpoint reference, troubleshooting).

## Files

- `ptm_client.py` — the reusable OAuth2 client (token fetch, cache, re-auth). **Copy this.**
- `app.py` — FastAPI UI glue.
- `config.py` — env-based config.
