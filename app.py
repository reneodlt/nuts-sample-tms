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


@app.get("/tournaments", response_class=HTMLResponse)
def tournaments(request: Request):
    tournaments, error = [], None
    try:
        resp = client.request("GET", "/api/tournaments/")
        if resp.status_code == 200:
            data = resp.json()
            tournaments = data.get("results", data) if isinstance(data, dict) else data
        else:
            error = f"{resp.status_code}: {resp.text}"
    except Exception as exc:
        error = str(exc)
    return templates.TemplateResponse("tournaments.html", {
        "request": request, "tournaments": tournaments, "error": error,
    })


@app.get("/tournaments/new", response_class=HTMLResponse)
def new_tournament_form(request: Request):
    return templates.TemplateResponse("new_tournament.html", {"request": request, "result": None})


@app.post("/tournaments/new", response_class=HTMLResponse)
def create_tournament(request: Request, name: str = Form(...)):
    result = {}
    try:
        resp = client.request("POST", "/api/tournaments/", json={"name": name})
        result = {"status": resp.status_code, "body": resp.text}
    except Exception as exc:
        result = {"status": "error", "body": str(exc)}
    return templates.TemplateResponse("new_tournament.html", {"request": request, "result": result})
