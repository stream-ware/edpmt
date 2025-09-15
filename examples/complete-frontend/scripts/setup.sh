#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"
PROJECTS_DIR="${PROJECTS_DIR:-projects}"
LOG_DIR="${LOG_DIR:-logs}"

echo "🏗️  Setting up directories and example projects..."
mkdir -p "$LOG_DIR"
mkdir -p "$PROJECTS_DIR"
echo "📁 Created directories: $LOG_DIR, $PROJECTS_DIR"

"$PYTHON_BIN" - <<'PY'
import json, os
projects = [
    {
        'name': 'LED Blink',
        'description': 'Simple LED blinking pattern',
        'blocks': [
            {'type': 'start', 'position': {'x': 50, 'y': 50}, 'params': {}},
            {'type': 'loop', 'position': {'x': 200, 'y': 50}, 'params': {'count': 10}},
            {'type': 'gpio-output', 'position': {'x': 350, 'y': 50}, 'params': {'pin': 18, 'value': '1'}},
            {'type': 'delay', 'position': {'x': 500, 'y': 50}, 'params': {'duration': 500}},
            {'type': 'gpio-output', 'position': {'x': 650, 'y': 50}, 'params': {'pin': 18, 'value': '0'}},
            {'type': 'delay', 'position': {'x': 800, 'y': 50}, 'params': {'duration': 500}},
        ],
        'version': '1.0',
    },
    {
        'name': 'Button Monitor',
        'description': 'Monitor button presses and control LED',
        'blocks': [
            {'type': 'start', 'position': {'x': 50, 'y': 50}, 'params': {}},
            {'type': 'gpio-input', 'position': {'x': 200, 'y': 50}, 'params': {'pin': 2, 'mode': 'pull-up'}},
            {'type': 'condition', 'position': {'x': 350, 'y': 50}, 'params': {'operator': '==', 'value': '0'}},
            {'type': 'gpio-output', 'position': {'x': 500, 'y': 30}, 'params': {'pin': 18, 'value': '1'}},
            {'type': 'gpio-output', 'position': {'x': 500, 'y': 90}, 'params': {'pin': 18, 'value': '0'}},
        ],
        'version': '1.0',
    },
    {
        'name': 'Traffic Light',
        'description': 'Three-LED traffic light sequence',
        'blocks': [
            {'type': 'start', 'position': {'x': 50, 'y': 50}, 'params': {}},
            {'type': 'loop', 'position': {'x': 200, 'y': 50}, 'params': {'infinite': True}},
            {'type': 'gpio-output', 'position': {'x': 350, 'y': 30}, 'params': {'pin': 18, 'value': '1'}},
            {'type': 'delay', 'position': {'x': 500, 'y': 30}, 'params': {'duration': 3000}},
            {'type': 'gpio-output', 'position': {'x': 650, 'y': 30}, 'params': {'pin': 18, 'value': '0'}},
            {'type': 'gpio-output', 'position': {'x': 350, 'y': 70}, 'params': {'pin': 19, 'value': '1'}},
            {'type': 'delay', 'position': {'x': 500, 'y': 70}, 'params': {'duration': 1000}},
            {'type': 'gpio-output', 'position': {'x': 650, 'y': 70}, 'params': {'pin': 19, 'value': '0'}},
            {'type': 'gpio-output', 'position': {'x': 350, 'y': 110}, 'params': {'pin': 20, 'value': '1'}},
            {'type': 'delay', 'position': {'x': 500, 'y': 110}, 'params': {'duration': 3000}},
            {'type': 'gpio-output', 'position': {'x': 650, 'y': 110}, 'params': {'pin': 20, 'value': '0'}},
        ],
        'version': '1.0',
    },
]
proj_dir = os.environ.get('PROJECTS_DIR', 'projects')
os.makedirs(proj_dir, exist_ok=True)
for p in projects:
    fn = f"{p['name'].replace(' ', '_').lower()}.json"
    with open(os.path.join(proj_dir, fn), 'w') as fh:
        json.dump(p, fh, indent=2)
print('✅ Setup completed - example projects created')
PY
