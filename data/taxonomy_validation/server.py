"""Collaborative human-validation table for the semantic-anomaly taxonomy.

Run: uv run --group taxonomy python data/taxonomy_validation/server.py
Password: env TAXVAL_PASSWORD (default 'anomaly_paper').
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
PASSWORD = os.environ.get("TAXVAL_PASSWORD", "anomaly_paper")
SECRET_FILE = HERE / ".secret"
if not SECRET_FILE.exists():
    SECRET_FILE.write_text(secrets.token_hex(32))
SECRET = SECRET_FILE.read_text().strip()

TAXONOMY = json.loads((HERE / "taxonomy.json").read_text())
ROWS = {r["id"]: r for r in TAXONOMY["rows"]}
KIND_FOR_SECTION = {"seed": "provenance", "extension": "validity"}
VALUES_FOR_KIND = {"validity": {"VALID", "INVALID"}, "provenance": {"REAL", "SYNTHETIC"}}

DB = sqlite3.connect(HERE / "decisions.sqlite", check_same_thread=False)
DB.execute("PRAGMA journal_mode=WAL")
DB.execute(
    """CREATE TABLE IF NOT EXISTS decisions (
         row_id INTEGER NOT NULL,
         kind TEXT NOT NULL CHECK (kind IN ('validity','provenance')),
         value TEXT NOT NULL CHECK (value IN ('VALID','INVALID','REAL','SYNTHETIC')),
         validator TEXT NOT NULL,
         ts TEXT NOT NULL,
         PRIMARY KEY (row_id, kind))"""
)
DB.commit()

CLIENTS: set[WebSocket] = set()


def authed(conn) -> bool:
    return conn.session.get("auth") is True


def all_decisions() -> dict[str, dict]:
    cur = DB.execute("SELECT row_id, kind, value, validator, ts FROM decisions")
    return {
        str(row_id): {"kind": kind, "value": value, "validator": validator, "ts": ts}
        for row_id, kind, value, validator, ts in cur
    }


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
    return JSONResponse({"rows": TAXONOMY["rows"], "decisions": all_decisions()})


async def decide(request: Request) -> Response:
    if not authed(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    try:
        body = await request.json()
        row_id = int(body["row_id"])
        value = str(body["value"])
        validator = str(body.get("validator", "")).strip()[:64]
    except (ValueError, KeyError, TypeError):
        return JSONResponse({"error": "bad request"}, status_code=400)
    row = ROWS.get(row_id)
    if row is None:
        return JSONResponse({"error": "unknown row"}, status_code=400)
    kind = KIND_FOR_SECTION[row["section"]]
    if value not in VALUES_FOR_KIND[kind]:
        return JSONResponse({"error": f"value not allowed for {kind}"}, status_code=400)
    if not validator:
        return JSONResponse({"error": "validator name required"}, status_code=400)
    ts = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    DB.execute(
        """INSERT INTO decisions (row_id, kind, value, validator, ts) VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(row_id, kind) DO UPDATE SET
             value=excluded.value, validator=excluded.validator, ts=excluded.ts""",
        (row_id, kind, value, validator, ts),
    )
    DB.commit()
    record = {"row_id": row_id, "kind": kind, "value": value, "validator": validator, "ts": ts}
    msg = {"type": "decision", **record}
    for ws in list(CLIENTS):
        try:
            await ws.send_json(msg)
        except Exception:
            CLIENTS.discard(ws)
    return JSONResponse(record)


async def export_csv(request: Request) -> Response:
    if not authed(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    decisions = all_decisions()
    buf = io.StringIO()
    fields = [
        "id", "section", "category", "object", "nominal_context", "ood_context",
        "normal_action", "anomalous_action", "example", "tag", "source_note", "source_url",
        "decision_kind", "decision_value", "validator", "ts",
    ]
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for row in TAXONOMY["rows"]:
        d = decisions.get(str(row["id"]), {})
        writer.writerow({
            **{k: row.get(k) for k in fields[:12]},
            "decision_kind": d.get("kind"), "decision_value": d.get("value"),
            "validator": d.get("validator"), "ts": d.get("ts"),
        })
    return Response(
        buf.getvalue().encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="taxonomy_validation.csv"'},
    )


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
        Route("/decide", decide, methods=["POST"]),
        Route("/export.csv", export_csv),
        WebSocketRoute("/ws", ws_endpoint),
    ],
    middleware=[Middleware(SessionMiddleware, secret_key=SECRET, max_age=30 * 24 * 3600)],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("TAXVAL_PORT", "8765")))
