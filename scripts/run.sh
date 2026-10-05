#!/usr/bin/env bash
# Shared launcher. Foreground execution is intentional for tmux and Ctrl+C.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$project_root"
mode="${1:?Missing mode}"
shift
case "$mode" in
    http|early-selenium)
        explicit_action=false
        for arg in "$@"; do
            case "$arg" in
                --now|--submit|--submit-once|--help|-h) explicit_action=true ;;
            esac
        done
        if [[ "$explicit_action" == false ]]; then
            set -- "$@" --submit
        fi
        set -- src/register.py "$mode" "$@"
        ;;
    report) set -- src/register.py report "$@" ;;
    legacy)
        if [[ "$#" -ne 0 ]]; then
            echo "Legacy Bot.py does not support command arguments; edit config.json instead." >&2
            exit 2
        fi
        set -- src/Bot.py
        ;;
    *) echo "Unknown mode: $mode" >&2; exit 2 ;;
esac
if [[ -n "${PYTHON:-}" ]]; then
    exec "$PYTHON" -u "$@"
elif [[ "${CONDA_DEFAULT_ENV:-}" == "SoC" ]]; then
    exec python -u "$@"
elif command -v conda >/dev/null 2>&1; then
    exec conda run --no-capture-output -n SoC python -u "$@"
else
    # Also supports an already activated Python virtual environment.
    exec python -u "$@"
fi
