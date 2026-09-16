#!/usr/bin/env python3
"""
run_lab.py — deterministic runner for hn-dns-ttl-serve-stale-boundary-lab
No network, no DNS, stdlib only.
"""
import json, csv, pathlib, platform, time, sys, subprocess
import evaluate

cases_path = pathlib.Path("cases.json")
data = json.loads(cases_path.read_text())
cases = data["cases"]

rows = []
pass_n = fail_n = 0
start = time.perf_counter()

for c in cases:
    chk = evaluate.check_case(c)
    derived = chk["derived"]
    row = {
        "case_id": c["case_id"],
        "category": c["category"],
        "expired": derived["derived_expired"],
        "remaining": derived["derived_remaining"],
        "may_serve_from_cache": derived["may_serve_from_cache"],
        "must_not_serve_stale": derived["must_not_serve_stale"],
        "serve_stale_allowed": derived["serve_stale_allowed"],
        "may_evict_early": derived["may_evict_early"],
        "ttl_upper_bound": derived["ttl_upper_bound"],
        "ttl_zero_no_cache": derived["ttl_zero_no_cache"],
        "stale_response_ttl": derived["stale_response_ttl"],
        "rrset_ttls_differ": derived["rrset_ttls_differ"],
        "rrset_effective_ttl": derived["rrset_effective_ttl"],
        "clamped": derived["clamped"],
        "derived_effective_ttl": derived["derived_effective_ttl"],
        "governing_ttl": derived["derived_governing_ttl"],
        "failure_to_refresh": derived["derived_failure_to_refresh"],
        "ok": chk["ok"],
        "mismatches": json.dumps(chk["mismatches"]) if chk["mismatches"] else "",
    }
    rows.append(row)
    if chk["ok"]:
        pass_n += 1
    else:
        fail_n += 1

elapsed = time.perf_counter() - start

# write artifacts
pathlib.Path("results_rows.json").write_text(json.dumps(rows, indent=2))
with open("results_rows.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

# RESULTS.md
pyver = platform.python_version()
plat = platform.platform()
results_md = f"""# RESULTS — hn-dns-ttl-serve-stale-boundary-lab

## Run info
- Python: {pyver}
- Platform: {plat}
- Cases: {len(cases)}
- Methods: 1 evaluator (RFC2181/8767/2308 boundary classifier)
- Elapsed: {elapsed:.3f}s
- Pass: {pass_n} / {len(cases)}
- Fail: {fail_n}

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
- cases.json — {len(cases)} synthetic cases (seed 42)
- results_rows.csv / results_rows.json
- HN evidence: hn_thread_evidence.md, hn_comments_sanitized.txt, hn_nodes_sanitized.json

## Reproducibility
Deterministic, no network, no external packages. Synthetic cases only.

Generated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
"""
pathlib.Path("RESULTS.md").write_text(results_md)

# Also print
print(f"PASS {pass_n}/{len(cases)} FAIL {fail_n} elapsed {elapsed:.3f}s")
for r in rows:
    status = "PASS" if r["ok"] else "FAIL"
    print(f"{status} {r['case_id']} expired={r['expired']} may_serve={r['may_serve_from_cache']} stale={r['serve_stale_allowed']} must_not={r['must_not_serve_stale']}")

sys.exit(0 if fail_n==0 else 1)
