# VERIFY — fresh unauthenticated clone

Public clone without credentials (no `file://`):

```
git clone https://github.com/necat101/hn-dns-ttl-serve-stale-boundary-lab.git /tmp/hn-verify
cd /tmp/hn-verify
```

Expected:

```
python3 -m py_compile generate_cases.py evaluate.py run_lab.py tests/test_lab.py
python3 generate_cases.py       # 30 cases
python3 evaluate.py             # 30/30 PASS
python3 run_lab.py              # 30/30 PASS, writes RESULTS.md
python3 tests/test_lab.py       # 13/13 passed
bash run.sh                     # same as above bundled
```

Fresh-clone transcript recorded after publish (see publisher logs). Tested revision: `<commit>` (filled after push).
