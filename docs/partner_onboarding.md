# Onboarding an integration partner

How to mint OAuth2 credentials for a partner venue and turn them into a working
`.env` for this sample TMS. This is the machine-to-machine
(client-credentials) path — see the
[OAuth2 Integration Guide](oauth2_integration_guide.md) for the full picture.

## 1. Mint a client (PTM admin)

Run `create_oauth_client` on the PTM host, scoped to the partner's venue code.
On the integration host that is:

```bash
docker compose exec django-asgi python manage.py create_oauth_client \
  --org <VENUE_CODE> \
  --name "<Partner Name>" \
  --scopes "tournament.read,tournament.write,player.read"
```

It prints `client_id` and `client_secret`. **The secret is shown once** — there
is no way to retrieve it later, so capture it now and re-mint if it's lost.

## 2. Build the partner's `.env`

Map the command output to `.env` fields (start from
[`.env.example`](../.env.example)):

| `.env` field        | Where it comes from                                              |
| ------------------- | --------------------------------------------------------------- |
| `PTM_BASE_URL`      | The PTM host the client was minted on (e.g. the integration server). |
| `PTM_CLIENT_ID`     | `client_id` from the command output.                            |
| `PTM_CLIENT_SECRET` | `client_secret` from the command output.                        |
| `PTM_SCOPE`         | The granted scopes, **space-separated** (the token request expects spaces, not commas). |
| `PTM_VENUE_CODE`    | The `--org` venue code — required to create tournaments.        |

Example (placeholders — never commit real secrets; `.env` is gitignored):

```dotenv
PTM_BASE_URL=https://<ptm-host>
PTM_CLIENT_ID=<client_id>
PTM_CLIENT_SECRET=<client_secret>
PTM_SCOPE=tournament.read tournament.write player.read
PTM_VENUE_CODE=<VENUE_CODE>
PORT=8095
```

## 3. Hand it over securely

- Share the `.env` (or just the secret) over a secure channel, not plaintext
  email/chat.
- Each client is bound to exactly one venue; the tournaments list is scoped to
  it via an `organization_id` filter resolved from `whoami`.
