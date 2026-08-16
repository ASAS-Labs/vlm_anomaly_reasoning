#!/usr/bin/env bash
# Vast.ai instance lifecycle for experiment sessions: reuse instead of re-download.
#
#   vast_instance.sh get [LABEL]     reuse the recorded instance if alive (start it
#                                    if stopped, cancel the destroy watchdog), else
#                                    create a new one; prints "ID HOST PORT" when ready
#   vast_instance.sh finish          stop (NOT destroy) the recorded instance and arm
#                                    a 1-hour watchdog that destroys it if unused
#   vast_instance.sh destroy         destroy immediately and clear state
#   vast_instance.sh status          show recorded instance state
#
# Rationale: stopping keeps the 33GB model + dataset on disk at storage-only cost
# (~$0.02/hr for 120GB) so the next session skips ~10 min of downloads. Caveats:
# a stopped instance's GPU may be rented out, so `start` can fail -> we fall back
# to creating a new instance; the watchdog is a local background sleep, so it dies
# if this machine powers off (the instance then persists at storage cost until
# manually destroyed).

set -u
VAST="${VAST:-/home/daniel/miniforge3/bin/vastai}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${REPO_ROOT}/tmp"
STATE="${STATE_DIR}/vast_instance.json"
WATCHDOG_PID="${STATE_DIR}/vast_watchdog.pid"
TEMPLATE_HASH="${TEMPLATE_HASH:-d7ef9ac4f6c0f9ab7809005962874d96}"   # Cosmos3_vLLM
DISK="${DISK:-120}"
OFFER_QUERY="${OFFER_QUERY:-gpu_name=H200 num_gpus=1 rentable=true disk_space>150 inet_down>1000}"

mkdir -p "$STATE_DIR"

_iid() { [ -f "$STATE" ] && python3 -c "import json;print(json.load(open('$STATE')).get('id',''))" 2>/dev/null || true; }

_instance_status() {  # -> running | stopped | gone
  local iid="$1"
  $VAST show instance "$iid" --raw 2>/dev/null | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("gone"); raise SystemExit
if not d or d.get("id") is None:
    print("gone")
else:
    s = d.get("actual_status") or ""
    print("running" if s == "running" else ("stopped" if s in ("stopped", "exited", "created") else s or "stopped"))
' || echo gone
}

_kill_watchdog() {
  if [ -f "$WATCHDOG_PID" ]; then
    kill "$(cat "$WATCHDOG_PID")" 2>/dev/null || true
    rm -f "$WATCHDOG_PID"
  fi
}

_wait_running_and_print() {
  local iid="$1"
  for _ in $(seq 1 40); do
    local st; st="$(_instance_status "$iid")"
    [ "$st" = "running" ] && break
    sleep 15
  done
  [ "$(_instance_status "$iid")" != "running" ] && { echo "ERROR: instance $iid not running" >&2; return 1; }
  local url; url="$($VAST ssh-url "$iid" 2>/dev/null | tail -1)"
  # ssh://root@HOST:PORT
  local hostport="${url#ssh://root@}"
  echo "$iid ${hostport%%:*} ${hostport##*:}"
}

cmd_get() {
  local label="${1:-cosmos3-session}"
  local iid; iid="$(_iid)"
  if [ -n "$iid" ]; then
    case "$(_instance_status "$iid")" in
      running)
        _kill_watchdog
        echo "reusing running instance $iid" >&2
        _wait_running_and_print "$iid"; return $? ;;
      stopped)
        _kill_watchdog
        echo "restarting stopped instance $iid" >&2
        if $VAST start instance "$iid" >/dev/null 2>&1; then
          if _wait_running_and_print "$iid"; then return 0; fi
        fi
        echo "restart failed (GPU likely taken); destroying and creating fresh" >&2
        $VAST destroy instance "$iid" >/dev/null 2>&1 || true
        rm -f "$STATE" ;;
      *)
        echo "recorded instance $iid is gone; creating fresh" >&2
        rm -f "$STATE" ;;
    esac
  fi
  local offer
  offer="$($VAST search offers "$OFFER_QUERY" -o 'dph+' 2>/dev/null | sed -n 2p | awk '{print $1}')"
  [ -z "$offer" ] && { echo "ERROR: no offer found" >&2; return 1; }
  local out; out="$($VAST create instance "$offer" --template_hash "$TEMPLATE_HASH" --disk "$DISK" --label "$label" 2>&1)"
  local newid; newid="$(printf '%s' "$out" | python3 -c "import sys,re;m=re.search(r\"'new_contract': (\d+)\",sys.stdin.read());print(m.group(1) if m else '')")"
  [ -z "$newid" ] && { echo "ERROR: create failed: $out" >&2; return 1; }
  printf '{"id": %s, "label": "%s"}\n' "$newid" "$label" > "$STATE"
  echo "created instance $newid" >&2
  _wait_running_and_print "$newid"
}

cmd_finish() {
  local iid; iid="$(_iid)"
  [ -z "$iid" ] && { echo "no recorded instance" >&2; return 0; }
  $VAST stop instance "$iid" >/dev/null 2>&1 && echo "stopped $iid (storage-only billing)" >&2
  _kill_watchdog
  setsid nohup bash -c "sleep 3600; $VAST destroy instance $iid; rm -f '$STATE' '$WATCHDOG_PID'" \
    > /dev/null 2>&1 < /dev/null &
  echo $! > "$WATCHDOG_PID"
  echo "watchdog armed: $iid will be destroyed in 1h unless reused" >&2
}

cmd_destroy() {
  local iid; iid="$(_iid)"
  _kill_watchdog
  [ -n "$iid" ] && $VAST destroy instance "$iid" 2>&1 | head -1
  rm -f "$STATE"
}

cmd_status() {
  local iid; iid="$(_iid)"
  [ -z "$iid" ] && { echo "no recorded instance"; return 0; }
  echo "instance $iid: $(_instance_status "$iid")"
  [ -f "$WATCHDOG_PID" ] && kill -0 "$(cat "$WATCHDOG_PID")" 2>/dev/null && echo "watchdog: armed"
}

case "${1:-}" in
  get) shift; cmd_get "$@";;
  finish) cmd_finish;;
  destroy) cmd_destroy;;
  status) cmd_status;;
  *) echo "usage: vast_instance.sh {get [label]|finish|destroy|status}" >&2; exit 1;;
esac
