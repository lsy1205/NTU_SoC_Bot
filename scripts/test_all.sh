#!/usr/bin/env bash
# Read-only checks. Never invoke legacy Bot.action or either submission flag.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$project_root"
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: ./scripts/test_all.sh"
    echo "HTTP and early-login Selenium: live login and activity queries (--now)."
    echo "Legacy: offline imports, configuration, and initialization check only."
    echo "Runs sequentially, saves logs, continues after failures; never registers."
    exit 0
fi
if [[ $# -ne 0 ]]; then
    echo "No arguments accepted. This script only performs read-only checks." >&2
    exit 2
fi
if [[ -n "${PYTHON:-}" ]]; then
    python_cmd=("$PYTHON")
elif [[ "${CONDA_DEFAULT_ENV:-}" == "SoC" ]]; then
    python_cmd=(python)
elif command -v conda >/dev/null 2>&1; then
    python_cmd=(conda run --no-capture-output -n SoC python)
else
    python_cmd=(python)
fi
export PYTHON
PYTHON="$("${python_cmd[@]}" -c 'import sys; print(sys.executable)')"
mkdir -p runs
log_dir="$(mktemp -d "$project_root/runs/check_all_$(date +%Y%m%d_%H%M%S)_XXXXXX")"
failures=0
trap 'echo "Checks interrupted. Logs: $log_dir"; exit 130' INT TERM
run_check() {
    local name="$1"
    shift
    echo "=== $name ==="
    if "$@" 2>&1 | tee "$log_dir/$name.log"; then
        echo "$name: PASS" | tee -a "$log_dir/results.txt"
    else
        local status=$?
        if [[ "$status" == 130 || "$status" == 143 ]]; then
            exit "$status"
        fi
        echo "$name: FAIL (exit $status)" | tee -a "$log_dir/results.txt"
        failures=$((failures + 1))
    fi
}

echo "Read-only checks; no registration requests will be sent."
echo "Legacy is checked offline; this does not validate legacy website login or submission."
run_check legacy_offline "$PYTHON" -u - <<'PY'
import contextlib
import io
from unittest.mock import patch

try:
    from src import Bot, register
    cfg = register.load_config('config.json')
    for key in ('NumBots', 'Headless', 'WaitTimeout', 'Time', 'Event', 'Dietary'):
        if key not in cfg:
            raise ValueError('Missing configuration')
    # Keep account details out of output; no real credentials or browser are used.
    with patch.object(Bot.Bot, 'load_info', return_value={
            'EMAIL': 'offline-check', 'PASSWORD': 'offline-check',
            'URL': 'https://soc.ee.ntu.edu.tw/www/'}), contextlib.redirect_stdout(io.StringIO()):
        bot = Bot.Bot(headless=cfg['Headless'], wait=cfg['WaitTimeout'])
    if bot.event != cfg['Event'] or bot.dietary != cfg['Dietary'] or bot.driver is not None:
        raise ValueError('Legacy configuration mismatch')
    print('Legacy imports, shared configuration, and initialization: PASS')
    print('Event:', cfg['Event'])
except Exception as exc:
    print('Legacy check failed:', type(exc).__name__)
    if isinstance(exc, ModuleNotFoundError):
        print('Missing module:', exc.name)
    raise SystemExit(1)
PY
run_check http "$project_root/scripts/run_http.sh" --now
run_check selenium "$project_root/scripts/run_selenium.sh" --now
echo "=== Summary ==="
cat "$log_dir/results.txt"
echo "Saved check logs: $log_dir"
echo "Live observation records: ./scripts/report.sh"
if [[ "$failures" -gt 0 ]]; then
    exit 1
fi
