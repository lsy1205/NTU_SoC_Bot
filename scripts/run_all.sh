#!/usr/bin/env bash
# Launch all three real registration methods in separate tmux windows.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
session_name="soc-all"
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: ./scripts/run_all.sh"
    echo "Start HTTP, early-login Selenium, and legacy Bot.py in tmux session soc-all."
    echo "All methods perform REAL scheduled registration using config.json."
    echo "Legacy uses NumBots; the two new methods each submit at most once."
    echo "Each window closes when its process exits; the session closes after the last one."
    exit 0
fi
if [[ $# -ne 0 ]]; then
    echo "Unsupported arguments. Use --help for usage." >&2
    exit 2
fi
command -v tmux >/dev/null || { echo "tmux is required." >&2; exit 1; }
if tmux has-session -t "=$session_name" 2>/dev/null; then
    echo "Session $session_name already exists; no new runners started."
    echo "Inspect it with: tmux attach -t $session_name"
    exit 1
fi

# Resolve once so each pane uses the same interpreter, even in an old tmux server.
if [[ -n "${PYTHON:-}" ]]; then
    python_cmd=("$PYTHON")
elif [[ "${CONDA_DEFAULT_ENV:-}" == "SoC" ]]; then
    python_cmd=(python)
elif command -v conda >/dev/null 2>&1; then
    python_cmd=(conda run --no-capture-output -n SoC python)
else
    python_cmd=(python)
fi
interpreter="$("${python_cmd[@]}" -c 'import sys; print(sys.executable)')"
cd -- "$project_root"

# The legacy bot starts immediately for past dates. Validate before launching ANY pane.
"$interpreter" - <<'PY'
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

cfg = json.loads(Path('config.json').read_text(encoding='utf-8'))
for key in ('Time', 'Event', 'Dietary', 'NumBots', 'Headless', 'WaitTimeout'):
    if key not in cfg:
        raise SystemExit('Missing config setting: ' + key)
target = datetime.strptime(cfg['Time'], '%Y-%m-%d %H:%M:%S')
zone = ZoneInfo(cfg.get('Timezone', 'Asia/Taipei'))
if target.replace(tzinfo=zone) <= datetime.now(zone) or target <= datetime.now():
    raise SystemExit('Opening time is in the past. Update config.json before starting all methods.')
if target.astimezone().utcoffset() != target.replace(tzinfo=zone).utcoffset():
    raise SystemExit('Legacy uses local time. Match the system time zone to config Timezone first.')
if not Path('.env').is_file():
    raise SystemExit('Missing .env file. Configure credentials first.')
print('Event:', cfg['Event'])
print('Opening:', cfg['Time'], str(zone))
print('Starting all methods for REAL registration. Legacy NumBots:', cfg['NumBots'])
PY

# Create every window before launching runners, so a fast exit cannot remove
# the session while other windows are still being created.
created=false
cleanup() {
    if [[ "$created" == true ]]; then
        tmux kill-session -t "=$session_name" 2>/dev/null || true
    fi
}
trap cleanup ERR
http_pane="$(tmux new-session -d -P -F '#{pane_id}' -s "$session_name" -n http -c "$project_root")"
created=true
selenium_pane="$(tmux new-window -d -P -F '#{pane_id}' -t "$session_name:" -n selenium -c "$project_root")"
legacy_pane="$(tmux new-window -d -P -F '#{pane_id}' -t "$session_name:" -n legacy -c "$project_root")"
for pane in "$http_pane" "$selenium_pane" "$legacy_pane"; do
    tmux set-option -w -t "$pane" remain-on-exit off
done
tmux respawn-pane -k -t "$http_pane" env "PYTHON=$interpreter" "$project_root/scripts/run_http.sh"
tmux respawn-pane -k -t "$selenium_pane" env "PYTHON=$interpreter" "$project_root/scripts/run_selenium.sh"
tmux respawn-pane -k -t "$legacy_pane" env "PYTHON=$interpreter" "$project_root/scripts/run_legacy.sh"
trap - ERR
echo "Started tmux session $session_name with windows: http, selenium, legacy."
echo "Windows close automatically when their processes exit; the last exit closes the session."
echo "Attach: tmux attach -t $session_name"
echo "Inside tmux: tmux switch-client -t $session_name"
echo "Stop all three: tmux kill-session -t $session_name"
echo "View saved new-runner results: ./scripts/report.sh"
