# VERIFY — fresh unauthenticated public clone — commit C execution target; commit D records

This file records **actual** evidence from a fresh unauthenticated clone.
Commit **C** was the execution target; this commit **D** only records the transcript.
Do not claim D verified itself. D is documentation-only.

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
git diff --exit-code -- RESULTS.md results_rows.csv results_rows.json
git status --porcelain
```

## Transcript of prior A verification (retained for history)

A = 8425160e6c351f2c2f98cda6cc68dbe4e61f827f was matched and executed with 36/36 and 19/19.

## Actual transcript for C (captured 2026-09-17T00:12 UTC from clone HEAD = C)

```
Cloning into '/tmp/hn-verify'...
CLONE_HEAD=a80785c88d04e1849fa310a2e860fa46d1a2e1f1
COMMIT_C=a80785c88d04e1849fa310a2e860fa46d1a2e1f1 → MATCH ✓
origin  https://github.com/necat101/hn-dns-ttl-serve-stale-boundary-lab.git (fetch/push)
Python 3.12.3
compile: OK
evaluator: 36/36 PASS (c01..c36 all PASS; c31 AA=0 insufficient, c32 AA=0 insufficient, c33 AA=1 refresh, c34 TTL60 valid not-rec, c35 TTL0 invalid, c36 TTL30 valid+rec)
run_lab: 36/36 PASS (elapsed 0.001s)
tests: 19/19 passed (each derives AA-bit + TTL validity from rcode+AA+ttl facts)
run.sh: 19/19 passed — All checks passed.
git diff --exit-code -- RESULTS.md results_rows.csv results_rows.json → exit 0 — EVIDENCE BYTE-STABLE ✓
git status --porcelain → (empty) — clean
git rev-parse HEAD = a80785c88d04e1849fa310a2e860fa46d1a2e1f1
git remote -v = https://github.com/necat101/hn-dns-ttl-serve-stale-boundary-lab.git
```

Required condition **met**: rerunning the lab leaves every tracked generated evidence file unchanged.

Prior clones showed `M RESULTS.md` (timestamp drift); after C the line reads `Generated: deterministic — seed 42, cases 36, evaluator stable (no wall-clock)` and the diff is zero.

## Tested implementation revision

```
C = a80785c88d04e1849fa310a2e860fa46d1a2e1f1
```

This file is commit **D** (documentation-only), which records the transcript.
**C, not D, was the execution target.** No evaluator/fixtures/results changed in D.

## Actions

Workflow `.github/workflows/verify.yml` — D's run is inspected separately via GitHub API.
Do not reuse B's run 35164827792 as evidence for D; D's status is reported from its own run.
