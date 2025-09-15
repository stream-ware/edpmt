#!/usr/bin/env bash
set -euo pipefail

HTTP_PORT="${HTTP_PORT:-8085}"

echo "🔎 Checking port availability..."
if ss -ltn | awk '{print $4}' | grep -q ":${HTTP_PORT}$"; then
  echo "🔴 Port ${HTTP_PORT} is already in use"
  exit 1
else
  echo "🟢 Port ${HTTP_PORT} is free"
fi
