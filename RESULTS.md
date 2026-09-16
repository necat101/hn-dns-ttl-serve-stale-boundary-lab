# RESULTS — hn-dns-ttl-serve-stale-boundary-lab

## Run info
- Python: 3.12.3
- Platform: Linux-7.0.0-1011-aws-x86_64-with-glibc2.39
- Cases: 36
- Methods: 1 evaluator (RFC2181/8767/2308 boundary classifier, AA-bit aware, TTL >0 vs 30 split)
- Elapsed: 0.001s
- Pass: 36 / 36
- Fail: 0

## Commands
```
python3 -m py_compile generate_cases.py evaluate.py run_lab.py tests/test_lab.py
python3 generate_cases.py
python3 evaluate.py
python3 run_lab.py
python3 tests/test_lab.py
bash run.sh
```

## Boundary summary (each derived independently from facts, not fixture labels)
- Base TTL rule (RFC2181 upper bound): early evict/refresh allowed. Verified: c03, c04 PASS.
- AA-bit refresh (RFC8767): RCODE 0/3 alone insufficient — AA=1 required for authoritative refresh. Verified: c05 AA=1 refresh; c31 c32 AA=0 insufficient.
- Serve-stale exception (RFC8767): only with RD=1, expired, failure to refresh, stale_enabled, within max-stale. Allowed c07 c08 c09 c34 c36; blocked c05 c10 c11 c26 c27 c31 c32.
- Stale response TTL: MUST >0, RECOMMENDED 30 — distinct. Valid: 30 (c36) and 60 (c34); invalid: 0 (c35).
- Negative caching (RFC2308): min(SOA TTL, MINIMUM). Verified c18 c19 c20 c22.
- Clamp (7d): verified c23 c24.
- TTL 0: not cached. Verified c13 c14.
- RRset min: verified c15.

## Detailed rows
See results_rows.csv / results_rows.json

Generated: 2026-09-16T23:59:22Z
