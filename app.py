"""
Sample TMS — a reference partner integration against the PTM OAuth2 API.

Run: ./run.sh  (after setting .env from .env.example)
"""
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pathlib

from config import config
from ptm_client import PTMClient

BASE_DIR = pathlib.Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Sample TMS")
client = PTMClient(
    config.PTM_BASE_URL, config.PTM_CLIENT_ID, config.PTM_CLIENT_SECRET, config.PTM_SCOPE,
)

# Clock / lifecycle actions exposed on the tournaments page. Each maps to
# POST /api/tournaments/{id}/{action}/ and needs tournament.write.
LIFECYCLE_ACTIONS = ("start", "pause", "resume", "advance_level", "complete")

# A tournament needs a blind structure before it can start. The demo creates
# a tiny one inline; a real TMS would send its own or use
# POST /api/tournaments/{id}/levels/generate/ with {"save": true}.
DEMO_LEVELS = [
    {"level_number": 1, "small_blind": 25, "big_blind": 50, "ante": 0, "duration_minutes": 15},
    {"level_number": 2, "small_blind": 50, "big_blind": 100, "ante": 0, "duration_minutes": 15},
    {"level_number": 3, "small_blind": 100, "big_blind": 200, "ante": 25, "duration_minutes": 15},
]


_organization_id_cache = None


def _organization_id():
    """This client's organization_id, resolved once from whoami and cached.

    The tournaments list endpoint isn't filtered to the token's organization
    server-side yet (see the integration guide, "List-endpoint org scoping"),
    so the demo scopes the list itself by passing this as an explicit filter.
    """
    global _organization_id_cache
    if _organization_id_cache is None:
        resp = client.request("GET", "/api/oauth/whoami/")
        resp.raise_for_status()
        _organization_id_cache = resp.json().get("organization_id")
    return _organization_id_cache


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    whoami, error = None, None
    try:
        resp = client.request("GET", "/api/oauth/whoami/")
        if resp.status_code == 200:
            whoami = resp.json()
        else:
            error = f"whoami returned {resp.status_code}: {resp.text}"
    except Exception as exc:
        error = str(exc)
    return templates.TemplateResponse("home.html", {
        "request": request, "config": config,
        "token": client.token_info(), "whoami": whoami, "error": error,
    })


def _tournaments_page(request: Request, action_result=None):
    tournaments, error = [], None
    try:
        org_id = _organization_id()
        if not org_id:
            raise RuntimeError(
                "whoami returned no organization_id — this client isn't bound "
                "to an org; re-provision it (see Troubleshooting in the guide)."
            )
        # Scope the list to this client's own venue. Without the filter the
        # endpoint may return tournaments beyond our organization.
        resp = client.request("GET", "/api/tournaments/",
                              params={"organization_id": org_id})
        if resp.status_code == 200:
            data = resp.json()
            tournaments = data.get("results", data) if isinstance(data, dict) else data
        else:
            error = f"{resp.status_code}: {resp.text}"
    except Exception as exc:
        error = str(exc)
    return templates.TemplateResponse("tournaments.html", {
        "request": request, "tournaments": tournaments, "error": error,
        "action_result": action_result, "actions": LIFECYCLE_ACTIONS,
        "venue_code": config.PTM_VENUE_CODE,
    })


@app.get("/tournaments", response_class=HTMLResponse)
def tournaments(request: Request):
    return _tournaments_page(request)


@app.post("/tournaments/{tournament_id}/{action}", response_class=HTMLResponse)
def tournament_action(request: Request, tournament_id: str, action: str):
    """Drive the tournament clock: start / pause / resume / advance_level / complete."""
    if action not in LIFECYCLE_ACTIONS:
        return _tournaments_page(request, {"action": action, "status": 400,
                                           "body": "unknown action"})
    try:
        resp = client.request(
            "POST", f"/api/tournaments/{tournament_id}/{action}/",
            json={"reason": f"Sample TMS {action}"},
        )
        result = {"action": action, "status": resp.status_code, "body": resp.text}
    except Exception as exc:
        result = {"action": action, "status": "error", "body": str(exc)}
    return _tournaments_page(request, result)


@app.get("/tournaments/new", response_class=HTMLResponse)
def new_tournament_form(request: Request):
    return templates.TemplateResponse("new_tournament.html", {
        "request": request, "result": None, "config": config,
    })


@app.post("/tournaments/new", response_class=HTMLResponse)
def create_tournament(request: Request, name: str = Form(...)):
    if not config.PTM_VENUE_CODE:
        result = {"status": "error",
                  "body": "PTM_VENUE_CODE is not set — add it to .env (the API "
                          "requires organization_id or venue_code on create)."}
    else:
        try:
            resp = client.request("POST", "/api/tournaments/", json={
                "name": name,
                "venue_code": config.PTM_VENUE_CODE,
                "levels": DEMO_LEVELS,
            })
            result = {"status": resp.status_code, "body": resp.text}
        except Exception as exc:
            result = {"status": "error", "body": str(exc)}
    return templates.TemplateResponse("new_tournament.html", {
        "request": request, "result": result, "config": config,
    })
