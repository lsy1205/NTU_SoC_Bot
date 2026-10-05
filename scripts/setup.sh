#!/usr/bin/env bash
# Install/update the project environment without replacing local credentials.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$project_root"
if ! command -v conda >/dev/null 2>&1; then
    echo "conda is required. Install Miniconda/Anaconda, then run this script again." >&2
    exit 1
fi
if ! conda run -n SoC python --version >/dev/null 2>&1; then
    conda create -n SoC python=3.13.7 -y
fi
conda run --no-capture-output -n SoC python -m pip install -r "$project_root/requirements.txt"
if [[ ! -e .env ]]; then
    (umask 077; set -o noclobber; cat > .env <<'ENV'
URL="https://soc.ee.ntu.edu.tw/www/"
EMAIL=""
PASSWORD=""
ENV
    )
    echo "Created .env. Fill in EMAIL and PASSWORD before running."
else
    echo "Existing .env preserved."
fi
echo "Setup complete. Next: edit config.json and run ./scripts/test_all.sh"
