"""Collaborative human review of the taxonomy-extension videos (mirrors data/taxonomy_validation).

Run: uv run --group taxonomy python data/extension_validation/server.py      # port EXTVAL_PORT (8766)
Env: EXTVAL_PASSWORD (default 'anomaly_paper'), EXTVAL_VIDS (default data/datasets/extension_vids;
     must contain validation.json and the clips).
"""

from __future__ import annotations

import csv
import datetime as dt
import hmac
import io
import json
import os
import secrets
import sqlite3
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
VIDS = Path(os.environ.get("EXTVAL_VIDS", REPO / "data" / "datasets" / "extension_vids")).resolve()
PASSWORD = os.environ.get("EXTVAL_PASSWORD", "anomaly_paper")
SECRET_FILE = HERE / ".secret"
if not SECRET_FILE.exists():
    SECRET_FILE.write_text(secrets.token_hex(32))
SECRET = SECRET_FILE.read_text().strip()

ROW_KEYS = ("taxonomy_id", "k", "polarity", "label", "category", "object", "ood_context", "prompt_sentence",
            "expectation", "flow", "id", "automatic", "installed_seed")


def load_rows() -> list[dict]:
    clips = json.loads((VIDS / "validation.json").read_text())["clips"]
    rows = [{"rel_path": rel, **{k: c.get(k) for k in ROW_KEYS}} for rel, c in clips.items()]
    return sorted(rows, key=lambda r: (r["k"], r["polarity"] != "positive"))


ROWS = load_rows()
REL_SET = {r["rel_path"] for r in ROWS}

DB = sqlite3.connect(HERE / "decisions.sqlite", check_same_thread=False)
DB.execute("PRAGMA journal_mode=WAL")
DB.execute(
    """CREATE TABLE IF NOT EXISTS decisions (
         rel_path TEXT PRIMARY KEY,
         value TEXT NOT NULL CHECK (value IN ('VALID','INVALID')),
         validator TEXT NOT NULL,
         ts TEXT NOT NULL)"""
)
DB.commit()
CLIENTS: set[WebSocket] = set()


def authed(conn) -> bool:
    return conn.session.get("auth") is True


def all_decisions() -> dict[str, dict]:
    return {rel: {"value": v, "validator": who, "ts": ts}
            for rel, v, who, ts in DB.execute("SELECT rel_path, value, validator, ts FROM decisions")}


async def login_page(request: Request) -> Response:
    return FileResponse(HERE / "login.html")


async def login_submit(request: Request) -> Response:
    form = await request.form()
    if hmac.compare_digest(str(form.get("password", "")), PASSWORD):
        request.session["auth"] = True
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/login?error=1", status_code=303)


async def index(request: Request) -> Response:
    if not authed(request):
        return RedirectResponse("/login", status_code=303)
    return FileResponse(HERE / "index.html")


async def state(request: Request) -> Response:
    if not authed(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return JSONResponse({"rows": ROWS, "decisions": all_decisions()})


async def media(request: Request) -> Response:
    if not authed(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    rel = request.path_params["rel"]
    path = (VIDS / rel).resolve()
    if rel not in REL_SET or not path.is_relative_to(VIDS) or not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="video/mp4")


async def decide(request: Request) -> Response:
    if not authed(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    try:
        body = await request.json()
        rel, value = str(body["rel_path"]), str(body["value"])
        validator = str(body.get("validator", "")).strip()[:64]
    except (ValueError, KeyError, TypeError):
        return JSONResponse({"error": "bad request"}, status_code=400)
    if rel not in REL_SET:
        return JSONResponse({"error": "unknown clip"}, status_code=400)
    if value not in ("VALID", "INVALID"):
        return JSONResponse({"error": "value must be VALID or INVALID"}, status_code=400)
    if not validator:
        return JSONResponse({"error": "validator name required"}, status_code=400)
    ts = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    DB.execute("""INSERT INTO decisions (rel_path, value, validator, ts) VALUES (?, ?, ?, ?)
                  ON CONFLICT(rel_path) DO UPDATE SET value=excluded.value, validator=excluded.validator, ts=excluded.ts""",
               (rel, value, validator, ts))
    DB.commit()
    record = {"rel_path": rel, "value": value, "validator": validator, "ts": ts}
    for ws in list(CLIENTS):
        try:
            await ws.send_json({"type": "decision", **record})
        except Exception:
            CLIENTS.discard(ws)
    return JSONResponse(record)


async def export_csv(request: Request) -> Response:
    if not authed(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    dec = all_decisions()
    buf = io.StringIO()
    fields = ["rel_path", "taxonomy_id", "k", "polarity", "label", "category", "object", "ood_context",
              "prompt_sentence", "expectation_class", "flow_end_state", "flow_prompt_video", "id_agree",
              "automatic", "installed_seed", "human_value", "validator", "ts"]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for r in ROWS:
        d = dec.get(r["rel_path"], {})
        w.writerow({**{k: r.get(k) for k in fields[:9]}, "expectation_class": (r["expectation"] or {}).get("class"),
                    "flow_end_state": (r["flow"] or {}).get("end_state"), "flow_prompt_video": (r["flow"] or {}).get("prompt_video"),
                    "id_agree": (r["id"] or {}).get("agree"), "automatic": r["automatic"], "installed_seed": r["installed_seed"],
                    "human_value": d.get("value"), "validator": d.get("validator"), "ts": d.get("ts")})
    return Response(buf.getvalue().encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="extension_video_validation.csv"'})


async def ws_endpoint(ws: WebSocket) -> None:
    if not authed(ws):
        await ws.close(code=1008)
        return
    await ws.accept()
    CLIENTS.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        CLIENTS.discard(ws)


app = Starlette(
    routes=[
        Route("/login", login_page, methods=["GET"]),
        Route("/login", login_submit, methods=["POST"]),
        Route("/", index),
        Route("/state", state),
        Route("/media/{rel:path}", media),
        Route("/decide", decide, methods=["POST"]),
        Route("/export.csv", export_csv),
        WebSocketRoute("/ws", ws_endpoint),
    ],
    middleware=[Middleware(SessionMiddleware, secret_key=SECRET, max_age=30 * 24 * 3600)],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("EXTVAL_PORT", "8766")))
