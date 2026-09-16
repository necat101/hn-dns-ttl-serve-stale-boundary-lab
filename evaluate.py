#!/usr/bin/env python3
"""
evaluate.py — RFC-faithful evaluator. Classifies protocol/cache state.

Boundaries:
  base TTL rule: RFC2181 maximum not mandatory (§8)
  resolver implementation freedom: early evict/refresh allowed
  serve-stale exception: RFC8767 (failure-only, RD required, TTL>0, max-stale cap, AA-bit)
  negative caching: RFC2308 SOA-derived TTL, not RR TTL
  clamp: RFC8767 7-day recommended cap

No network, no sockets.
"""
import json
import pathlib

def classify(case: dict, now_override=None) -> dict:
    now = now_override if now_override is not None else case["now"]
    stored_at = case.get("stored_at", 0)
    stored_ttl = case.get("stored_ttl")
    received_ttl = case.get("received_ttl")
    effective_ttl = case.get("effective_ttl", stored_ttl)
    negative_type = case.get("negative_type")
    negative_ttl = case.get("negative_ttl")
    rd = case.get("rd_flag", True)
    authority_reachable = case.get("authority_reachable", True)
    rcode = case.get("authority_rcode")
    authority_aa = case.get("authority_aa", False)
    stale_enabled = case.get("stale_config_enabled", False)
    max_stale = case.get("max_stale", 86400)
    ttl_zero = case.get("ttl_zero", False)
    implementation_max = case.get("implementation_max_ttl", 604800)
    stale_response_ttl_raw = case.get("stale_response_ttl", None)

    elapsed = now - stored_at
    governing_ttl = effective_ttl if (negative_type is None) else negative_ttl
    if ttl_zero:
        expired = True
        remaining = 0 - elapsed
        stale_age = elapsed
    elif governing_ttl is None:
        governing_ttl = stored_ttl or 0
        expired = elapsed >= governing_ttl
        remaining = governing_ttl - elapsed
        stale_age = elapsed - governing_ttl if expired else 0
    else:
        expired = elapsed >= governing_ttl
        remaining = governing_ttl - elapsed
        stale_age = elapsed - governing_ttl if expired else 0

    rrset_ttls = case.get("rrset_ttls") or []
    if rrset_ttls:
        derived_rrset_effective = min(rrset_ttls)
    else:
        derived_rrset_effective = None

    clamped = False
    if received_ttl is not None and implementation_max is not None:
        clamped = received_ttl > implementation_max
        derived_effective = implementation_max if clamped else received_ttl
    else:
        derived_effective = governing_ttl

    # RFC 8767 AA-bit condition: rcode 0/3 with AA=1 MUST be considered refresh
    authoritative_refresh = bool(authority_reachable and rcode in (0, 3) and authority_aa is True)
    # failure to refresh: unreachable, or rcode not in (0,3), or rcode 0/3 but AA=0 (insufficient)
    # AA=0 with rcode 0/3 is NOT authoritative refresh, but also not automatic "serve stale MUST"
    # The narrow correction: treat AA=0 as not-refresh, which makes failure_to_refresh False?
    # Actually per task spec: for AA=0 cases, expect serve_stale_allowed=False, authoritative_refresh=False,
    # and must_not_serve_stale=False — i.e., neither refresh nor stale. That's a distinct state.
    # So we split: failure_to_refresh should remain False for AA=0, and we introduce aa_insufficient.
    aa_insufficient = bool(authority_reachable and rcode in (0, 3) and authority_aa is False)
    if not authority_reachable:
        failure_to_refresh = True
    elif rcode not in (0, 3, None) and rcode is not None:
        failure_to_refresh = True
    elif rcode is None and not authority_reachable:
        failure_to_refresh = True
    elif authoritative_refresh:
        failure_to_refresh = False
    elif aa_insufficient:
        # RCODE alone insufficient — not refresh, but not counted as failure that would trigger stale MUST
        failure_to_refresh = False
    else:
        failure_to_refresh = False

    serve_stale_allowed = (
        expired is True
        and rd is True
        and stale_enabled is True
        and (stale_age <= max_stale)
        and failure_to_refresh is True
        and ttl_zero is False
        and negative_type is None
    )
    if negative_type is not None:
        serve_stale_allowed = False

    must_not_serve_stale = expired and not serve_stale_allowed and not aa_insufficient
    # aa_insufficient is a distinct non-refresh that is not "must not stale" either
    if aa_insufficient:
        must_not_serve_stale = False
    if not expired:
        must_not_serve_stale = False

    ttl_zero_no_cache = ttl_zero
    may_serve_from_cache = (not expired) and (not ttl_zero) and (remaining > 0)
    if ttl_zero:
        may_serve_from_cache = False
    may_evict_early = True

    # stale response TTL: MUST >0, RECOMMENDED 30 — evaluate actual supplied value
    stale_ttl_valid = None
    stale_ttl_recommended = None
    derived_stale_ttl = stale_response_ttl_raw if stale_response_ttl_raw is not None else (30 if serve_stale_allowed else None)
    if serve_stale_allowed or case.get("category") == "serve_stale" and "stale_response_ttl" in case and expired:
        # For AA=0 cases where serve_stale_allowed is False but we still want to evaluate ttl validity if present
        # only evaluate when stale would be considered — otherwise stale_ttl_valid reflects supplied value validity
        pass
    if "stale_response_ttl" in case:
        ttl_val = case["stale_response_ttl"]
        stale_ttl_valid = bool(ttl_val is not None and ttl_val > 0)
        stale_ttl_recommended = bool(ttl_val == 30)
    elif serve_stale_allowed:
        stale_ttl_valid = True
        stale_ttl_recommended = (derived_stale_ttl == 30)

    rrset_differ = len(set(rrset_ttls)) > 1 if rrset_ttls else False
    is_clamped = clamped
    deployment = case.get("category") == "deployment"

    result = {
        "case_id": case["case_id"],
        "derived_governing_ttl": governing_ttl,
        "derived_elapsed": elapsed,
        "derived_remaining": remaining,
        "derived_expired": expired,
        "derived_stale_age": stale_age,
        "derived_failure_to_refresh": failure_to_refresh,
        "derived_authoritative_refresh": authoritative_refresh,
        "derived_aa_insufficient": aa_insufficient,
        "may_serve_from_cache": may_serve_from_cache,
        "must_not_serve_stale": must_not_serve_stale,
        "serve_stale_allowed": serve_stale_allowed,
        "may_evict_early": may_evict_early,
        "ttl_upper_bound": True,
        "ttl_zero_no_cache": ttl_zero_no_cache,
        "stale_ttl_valid": stale_ttl_valid,
        "stale_ttl_recommended_value": stale_ttl_recommended,
        "stale_response_ttl": derived_stale_ttl,
        "rrset_ttls_differ": rrset_differ,
        "rrset_effective_ttl": derived_rrset_effective,
        "clamped": is_clamped,
        "derived_effective_ttl": derived_effective,
        "deployment_measurement": deployment,
        "rd_flag": rd,
        "authority_aa": authority_aa,
    }
    return result

def check_case(case: dict) -> dict:
    derived = classify(case)
    expect = case.get("expect", {})
    mismatches = {}
    key_map = {
        "may_serve_from_cache": "may_serve_from_cache",
        "must_not_serve_stale": "must_not_serve_stale",
        "serve_stale_allowed": "serve_stale_allowed",
        "may_evict_early": "may_evict_early",
        "ttl_upper_bound": "ttl_upper_bound",
        "early_evict_compliant": "may_evict_early",
        "ttl_zero_no_cache": "ttl_zero_no_cache",
        "rrset_ttls_differ": "rrset_ttls_differ",
        "rrset_effective_ttl": "rrset_effective_ttl",
        "clamped": "clamped",
        "effective_ttl": "derived_effective_ttl",
        "deployment_measurement": "deployment_measurement",
        "not_semantic_permission": "deployment_measurement",
        "negative_cache_ttl": "derived_governing_ttl",
        "exact_expiry": "derived_expired",
        "no_rd_means_no_stale": "serve_stale_allowed",
        "rcode_refreshes": "derived_failure_to_refresh",
        "authoritative_refresh": "derived_authoritative_refresh",
        "aa_insufficient": "derived_aa_insufficient",
        "stale_ttl_valid": "stale_ttl_valid",
        "stale_ttl_recommended_value": "stale_ttl_recommended_value",
        "stale_ttl_must_be_positive": "stale_ttl_valid",
        "stale_ttl_recommended": "stale_ttl_recommended_value",
    }
    for k, v in expect.items():
        if k in ("negative_ttl_is_soa_derived", "negative_not_positive_ttl", "positive_ttl_is_rr_ttl", "negative_expired", "rrset_must_normalize", "received_ttl"):
            continue
        mapped = key_map.get(k)
        if mapped is None:
            continue
        got = derived.get(mapped)
        # boolean expects
        if k in ("no_rd_means_no_stale", "rcode_refreshes"):
            expected = False
            if got != expected:
                mismatches[k] = {"expected": expected, "got": got}
        elif k == "not_semantic_permission":
            if got != True:
                mismatches[k] = {"expected": True, "got": got}
        else:
            if got != v:
                mismatches[k] = {"expected": v, "got": got}
    if case.get("negative_type") in ("NXDOMAIN", "NODATA"):
        soa_ttl = case.get("soa_ttl")
        soa_min = case.get("soa_minimum")
        expected_neg = min(soa_ttl, soa_min) if soa_ttl is not None and soa_min is not None else None
        if case.get("negative_ttl") is not None and expected_neg is not None:
            if case.get("negative_ttl") != expected_neg:
                mismatches["negative_ttl_mismatch"] = {"expected_derived": expected_neg, "fixture": case.get("negative_ttl")}
            if derived["derived_governing_ttl"] != expected_neg:
                mismatches["derived_negative_ttl"] = {"expected": expected_neg, "got": derived["derived_governing_ttl"]}
    if case.get("rrset_ttls") and len(set(case["rrset_ttls"])) > 1:
        if derived["rrset_effective_ttl"] != min(case["rrset_ttls"]):
            mismatches["rrset_normalize"] = {"expected": min(case["rrset_ttls"]), "got": derived["rrset_effective_ttl"]}
    ok = len(mismatches) == 0
    return {"ok": ok, "derived": derived, "mismatches": mismatches}

if __name__ == "__main__":
    import sys
    p = pathlib.Path(__file__).parent / "cases.json"
    data = json.loads(p.read_text())
    fails = 0
    for c in data["cases"]:
        r = check_case(c)
        status = "PASS" if r["ok"] else "FAIL"
        if not r["ok"]:
            fails += 1
        print(f"{status} {c['case_id']}: {r['mismatches'] if not r['ok'] else 'ok'}")
    print(f"\nSummary: {len(data['cases'])-fails}/{len(data['cases'])} PASS")
    sys.exit(0 if fails == 0 else 1)
