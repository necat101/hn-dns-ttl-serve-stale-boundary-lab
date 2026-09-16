#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile generate_cases.py evaluate.py run_lab.py tests/test_lab.py
python3 generate_cases.py
python3 evaluate.py
python3 run_lab.py
python3 tests/test_lab.py
echo "All checks passed."
