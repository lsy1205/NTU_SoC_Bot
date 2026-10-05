#!/usr/bin/env bash
# Source this file to activate SoC in the current terminal.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "Use: source scripts/env.sh" >&2
    exit 1
fi
_soc_activate() {
    local conda_root
    if ! command -v conda >/dev/null 2>&1; then
        echo "conda is required. Install it before activating SoC." >&2
        return 1
    fi
    conda_root="$(conda info --base)" || return
    source "$conda_root/etc/profile.d/conda.sh" || return
    conda activate SoC
}
if _soc_activate; then
    unset -f _soc_activate
else
    unset -f _soc_activate
    return 1
fi
