#!/usr/bin/env bash
# Compatible installer entry point; safe both when executed and sourced.
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    bash "$(dirname -- "${BASH_SOURCE[0]}")/scripts/setup.sh" || return $?
    source "$(dirname -- "${BASH_SOURCE[0]}")/scripts/env.sh"
else
    exec bash "$(dirname -- "${BASH_SOURCE[0]}")/scripts/setup.sh" "$@"
fi
