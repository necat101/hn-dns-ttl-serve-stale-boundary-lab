# RESULTS — hn-dns-ttl-serve-stale-boundary-lab

## Run info
- Python: 3.12.3
- Platform: Linux-7.0.0-1011-aws-x86_64-with-glibc2.39
- Cases: 30
- Methods: 1 evaluator (RFC2181/8767/2308 boundary classifier)
- Elapsed: 0.001s
- Pass: 30 / 30
- Fail: 0

## Commands
```
python3 -m py_compile generate_cases.py evaluate.py run_lab.py tests/test_lab.py
python3 generate_cases.py
python3 evaluate.py
python3 run_lab.py
python3 -m pytest tests/test_lab.py -v
# or
python3 tests/test_lab.py
bash run.sh
```

## Boundary summary (each derived independently from facts, not fixture labels)
- Base TTL rule (RFC2181 upper bound): TTL is maximum, not mandatory — early evict/refresh allowed. Verified: c03, c04 PASS.
- Resolver implementation freedom: no floor on refetching unexpired. Verified.
- Serve-stale exception (RFC8767): only with RD=1, expired, failure to refresh, stale_enabled, within max-stale, TTL>0 in response. Verified: c07/c08/c09 allowed; c05/c10/c11/c26 blocked.
- Negative caching (RFC2308): TTL = min(SOA TTL, MINIMUM), not RR TTL. Verified: c18 c19 c20 c22.
- Clamp (RFC8767 cap 7d): large received TTLs capped to 604800. Verified: c23 c24.
- TTL 0: not cached, transaction-only. Verified: c13 c14.
- RRset differing TTLs (RFC2181 §5.2): effective is min. Verified: c15.
- Cloudflare deployment behavior: 100TB is fleet measurement, not TTL semantics permission. Verified: c29.
- HN inference rows checked separately (see README).

## Detailed rows
See results_rows.csv / results_rows.json

## Artifacts
- cases.json — 30 synthetic cases (seed 42)
- results_rows.csv / results_rows.json
- HN evidence: hn_thread_evidence.md, hn_comments_sanitized.txt, hn_nodes_sanitized.json

## Reproducibility
Deterministic, no network, no external packages. Synthetic cases only.

Generated: 2026-09-16T23:44:14Z
