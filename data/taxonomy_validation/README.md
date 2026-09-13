# Taxonomy human-validation app

Shared, real-time web table for validating the semantic-anomaly taxonomy
(`anomaly definition framework/semantic_anomaly_taxonomy_framework.docx`).

- **Extension rows (#13–112)**: each row shows its REAL/SYNTHETIC marker and source; validators press
  **VALID** (green) or **INVALID** (red). Undecided rows stay neutral. **Move Validated** moves every
  decided row to a Validated section at the bottom (per browser view; a reload shows the full list).
- **Original 12 rows (#1–12)**: no marker in the source; validators press **REAL** or **SYNTHETIC**.
- Every decision stores value, validator name (asked once, kept in the browser) and UTC timestamp;
  last write wins. All open pages update live over a WebSocket.
- Access: shared password (`anomaly_paper`; override with env `TAXVAL_PASSWORD`).

## Files
| File | Role |
|---|---|
| `import_docx.py` | docx -> `taxonomy.json` (stdlib only; re-run if the docx changes) |
| `taxonomy.json` | 112 rows: id, section, category, six framework fields, tag, source_note, source_url |
| `server.py` | Starlette + uvicorn; SQLite `decisions.sqlite` (gitignored); WebSocket broadcast |
| `index.html`, `login.html` | the page and the password form |

## Run
```bash
uv run python data/taxonomy_validation/import_docx.py          # only when the docx changes
uv run --group taxonomy python data/taxonomy_validation/server.py   # http://127.0.0.1:8765
```
Export results any time: click **Export CSV** on the page, or
`curl -c cj -d password=anomaly_paper http://127.0.0.1:8765/login && curl -b cj http://127.0.0.1:8765/export.csv -o results.csv`.

## Expose publicly (Tailscale Funnel, free on the personal plan)
One-time setup in WSL (needs sudo and a browser login):
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl enable --now tailscaled     # if the TUN device fails: sudo tailscaled --tun=userspace-networking &
sudo tailscale up                          # open the printed URL and approve this machine
```
In the admin console (https://login.tailscale.com/admin): DNS -> enable MagicDNS and HTTPS certificates;
Access controls -> add `"nodeAttrs": [{"target": ["autogroup:member"], "attr": ["funnel"]}]`
(the first `tailscale funnel` command prints the exact link if anything is missing). Then:
```bash
sudo tailscale funnel --bg 8765
tailscale funnel status                    # public https://<machine>.<tailnet>.ts.net/
sudo tailscale funnel --bg off             # to stop
```
Fallback (already installed, random URL that changes on restart):
```bash
cloudflared tunnel --url http://localhost:8765
```
