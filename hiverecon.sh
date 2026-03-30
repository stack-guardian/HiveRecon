#!/bin/bash
# HiveRecon wrapper script
# Usage: ./hiverecon.sh scan -t example.com

VENV_PYTHON="/home/vibhxr/hiverecon/venv/bin/python"
PROJECT_DIR="/home/vibhxr/hiverecon"

cd "$PROJECT_DIR"
exec "$VENV_PYTHON" -m hiverecon "$@"
