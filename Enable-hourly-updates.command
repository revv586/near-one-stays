#!/bin/bash
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then echo 'ต้องติดตั้ง Python 3 ก่อน'; exit 1; fi
python3 scripts/install_launchagent.py
