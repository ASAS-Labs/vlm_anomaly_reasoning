# Extension video validation app

Human review of the generated taxonomy-extension clips: one row per clip with the inline video,
the scenario, the expected ego action, the automatic-check badges (optical-flow probe, inverse
dynamics, combined verdict) and VALID / INVALID buttons. Same mechanics as
`data/taxonomy_validation/` (shared password, validator name kept in the browser, live updates
over a WebSocket, last write wins, CSV export, per-view "Move Validated").

```bash
uv run --group taxonomy python data/extension_validation/server.py    # http://127.0.0.1:8766
sudo tailscale funnel --bg --https=8443 8766                          # https://<machine>.<tailnet>.ts.net:8443/
tailscale funnel status
```
Env: `EXTVAL_PASSWORD` (default `anomaly_paper`), `EXTVAL_PORT` (8766), `EXTVAL_VIDS`
(default `data/datasets/extension_vids`, must hold `validation.json` and the clips).

Feed the decisions back: `uv run python data/cosmos3/extension_validate.py human` (then `publish`).
