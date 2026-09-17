# VERIFY — fresh unauthenticated public clone — commit A execution target

This file records **actual** evidence from a fresh unauthenticated clone.
It does **not** claim to verify itself. Commit **A** was the execution target;
this commit **B** only records the transcript.

## How to reproduce (public, no credentials, no file://)

```
git clone https://github.com/necat101/hn-dns-ttl-serve-stale-boundary-lab.git /tmp/hn-verify
cd /tmp/hn-verify
git rev-parse HEAD
git remote -v
python3 --version
python3 -m py_compile generate_cases.py evaluate.py run_lab.py tests/test_lab.py
python3 evaluate.py
python3 run_lab.py
python3 tests/test_lab.py
bash run.sh
git status --porcelain
git diff --stat
```

## Actual transcript (captured 2026-09-17T00:00 UTC from clone HEAD = A)

```
Cloning into '/tmp/hn-verify2'...
HEAD=8425160e6c351f2c2f98cda6cc68dbe4e61f827f
COMMIT_A=8425160e6c351f2c2f98cda6cc68dbe4e61f827f → MATCH ✓
Python 3.12.3
origin  https://github.com/necat101/hn-dns-ttl-serve-stale-boundary-lab.git (fetch)
origin  https://github.com/necat101/hn-dns-ttl-serve-stale-boundary-lab.git (push)
8425160e6c351f2c2f98cda6cc68dbe4e61f827f
compile: OK
evaluator: 36/36 PASS
  PASS c01 ... c30 (see RESULTS.md)
  PASS c31_noerror_aa0_no_refresh — AA=0 insufficient (not refresh, not stale-MUST)
  PASS c32_nxdomain_aa0_no_refresh — AA=0 insufficient
  PASS c33_nxdomain_aa1_refresh — AA=1 refresh
  PASS c34_stale_ttl_60_valid_not_recommended — TTL 60 valid, not recommended
  PASS c35_stale_ttl_zero_invalid — TTL 0 invalid (MUST >0 violated)
  PASS c36_stale_ttl_30_recommended — TTL 30 valid+recommended
run_lab: 36/36 PASS
tests: 19/19 passed (each derives AA-bit + TTL validity from rcode+AA+ttl facts)
run.sh: 19/19 passed — All checks passed.
git rev-parse HEAD = 8425160e6c351f2c2f98cda6cc68dbe4e61f827f
git remote -v = https://github.com/necat101/hn-dns-ttl-serve-stale-boundary-lab.git
git status --porcelain = M RESULTS.md (single timestamp line)
git diff RESULTS.md: Generated: 2026-09-16T23:59:22Z → 2026-09-17T00:00:23Z (1 line)
```

Full row-level outputs in `results_rows.csv` / `results_rows.json`. No live DNS queries, no sockets.

## Tested implementation revision

```
A = 8425160e6c351f2c2f98cda6cc68dbe4e61f827f
```
This file is commit **B** (documentation-only), which records the transcript.
**A, not B, was the execution target.** Do not claim B verifies itself.

## Rerun diff honesty

Rerunning the lab in the fresh clone changed only the `Generated:` timestamp line in `RESULTS.md`
(1 insertion, 1 deletion). No changes to `results_rows.csv` / `results_rows.json` / `cases.json` /
`evaluate.py` / `tests/test_lab.py`. The tree is not claimed clean — the timestamp drift is reported above.

## Actions

Workflow `.github/workflows/verify.yml` — see commit B status via GitHub Actions API.
Previous run for A (8425160) was `completed success`. B's status is reported separately (not reused).
