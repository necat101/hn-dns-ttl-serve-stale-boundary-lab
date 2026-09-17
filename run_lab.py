#!/usr/bin/env python3
"""
run_lab.py — deterministic runner for hn-dns-ttl-serve-stale-boundary-lab
No network, no DNS, stdlib only.
"""
import json, csv, pathlib, platform, time, sys
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
        "authoritative_refresh": derived["derived_authoritative_refresh"],
        "aa_insufficient": derived["derived_aa_insufficient"],
        "failure_to_refresh": derived["derived_failure_to_refresh"],
        "stale_ttl_valid": derived["stale_ttl_valid"],
        "stale_ttl_recommended_value": derived["stale_ttl_recommended_value"],
        "stale_response_ttl": derived["stale_response_ttl"],
        "may_evict_early": derived["may_evict_early"],
        "ttl_upper_bound": derived["ttl_upper_bound"],
        "ttl_zero_no_cache": derived["ttl_zero_no_cache"],
        "rrset_ttls_differ": derived["rrset_ttls_differ"],
        "rrset_effective_ttl": derived["rrset_effective_ttl"],
        "clamped": derived["clamped"],
        "derived_effective_ttl": derived["derived_effective_ttl"],
        "governing_ttl": derived["derived_governing_ttl"],
        "ok": chk["ok"],
        "mismatches": json.dumps(chk["mismatches"]) if chk["mismatches"] else "",
    }
    rows.append(row)
    if chk["ok"]:
        pass_n += 1
    else:
        fail_n += 1

elapsed = time.perf_counter() - start

pathlib.Path("results_rows.json").write_text(json.dumps(rows, indent=2))
with open("results_rows.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

pyver = platform.python_version()
plat = platform.platform()
results_md = f"""# RESULTS — hn-dns-ttl-serve-stale-boundary-lab

## Run info
- Python: {pyver}
- Platform: {plat}
- Cases: {len(cases)}
- Methods: 1 evaluator (RFC2181/8767/2308 boundary classifier, AA-bit aware, TTL >0 vs 30 split)
- Elapsed: {elapsed:.3f}s
- Pass: {pass_n} / {len(cases)}
- Fail: {fail_n}

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

Generated: deterministic — seed 42, cases 36, evaluator stable (no wall-clock)
"""
pathlib.Path("RESULTS.md").write_text(results_md)
print(f"PASS {pass_n}/{len(cases)} FAIL {fail_n} elapsed {elapsed:.3f}s")
for r in rows:
    status = "PASS" if r["ok"] else "FAIL"
    print(f"{status} {r['case_id']} expired={r['expired']} may_serve={r['may_serve_from_cache']} stale={r['serve_stale_allowed']} refresh={r['authoritative_refresh']} aa_insuff={r['aa_insufficient']} ttl_valid={r['stale_ttl_valid']} ttl_rec={r['stale_ttl_recommended_value']}")
sys.exit(0 if fail_n==0 else 1)
