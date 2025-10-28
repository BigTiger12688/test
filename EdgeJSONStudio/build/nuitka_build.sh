#!/usr/bin/env bash
# 使用 Nuitka 打包 EdgeJSON Studio
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_DIR="$SCRIPT_DIR/.."
python -m nuitka \
  --standalone \
  --enable-plugin=pyside6 \
  --include-data-dir="$PROJECT_DIR/qml"=qml \
  --include-data-dir="$PROJECT_DIR/assets"=assets \
  --include-data-dir="$PROJECT_DIR/i18n"=i18n \
  --include-data-dir="$PROJECT_DIR/sample_data"=sample_data \
  --onefile \
  --lto=yes \
  --remove-output \
  --output-dir="$SCRIPT_DIR/dist" \
  "$PROJECT_DIR/main.py"
