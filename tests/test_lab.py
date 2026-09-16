#!/usr/bin/env python3
"""
tests/test_lab.py — independent tests must derive expected from facts, not trust fixture labels
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import evaluate

cases = json.loads(pathlib.Path("cases.json").read_text() if pathlib.Path("cases.json").exists() else pathlib.Path(__file__).parent.parent.joinpath("cases.json").read_text())["cases"] if False else None
# load from lab root
import pathlib as pl
data = json.loads((pl.Path(__file__).parent.parent / "cases.json").read_text())
cases = data["cases"]

def test_positive_inside_ttl_fresh():
    c = next(x for x in cases if x["case_id"]=="c01_positive_inside_ttl")
    d = evaluate.classify(c)
    assert d["may_serve_from_cache"] is True
    assert d["serve_stale_allowed"] is False
    assert d["must_not_serve_stale"] is False

def test_early_evict_allowed_is_upper_bound():
    c = next(x for x in cases if x["case_id"]=="c03_early_evict_before_expiry")
    d = evaluate.classify(c)
    assert d["may_evict_early"] is True
    assert d["ttl_upper_bound"] is True
    # derive independently: elapsed 100 < 3600 => fresh, so evict allowed
    assert d["derived_expired"] is False

def test_expired_reachable_must_not_serve_stale():
    c = next(x for x in cases if x["case_id"]=="c05_expired_authority_reachable")
    d = evaluate.classify(c)
    # independent derivation: expired True, reachable + RCODE 0 => not failure => no stale
    assert d["derived_expired"] is True
    assert d["derived_failure_to_refresh"] is False
    assert d["serve_stale_allowed"] is False
    assert d["must_not_serve_stale"] is True

def test_stale_allowed_only_on_failure():
    c = next(x for x in cases if x["case_id"]=="c07_stale_8767_authority_unreachable")
    d = evaluate.classify(c)
    assert d["derived_expired"] is True
    assert d["derived_failure_to_refresh"] is True
    assert d["serve_stale_allowed"] is True
    assert d["stale_ttl_must_be_positive"] is True
    assert d["stale_response_ttl"] == 30
    # serving stale does not make it fresh: may_serve_from_cache stays False
    assert d["may_serve_from_cache"] is False

def test_servfail_is_failure():
    c = next(x for x in cases if x["case_id"]=="c08_stale_8767_servfail_treated_as_failure")
    d = evaluate.classify(c)
    assert d["derived_failure_to_refresh"] is True
    assert d["serve_stale_allowed"] is True

def test_no_rd_no_stale():
    c = next(x for x in cases if x["case_id"]=="c11_expired_no_rd_flag")
    d = evaluate.classify(c)
    assert d["rd_flag"] is False
    assert d["serve_stale_allowed"] is False
    assert d["must_not_serve_stale"] is True

def test_ttl_zero_never_cached():
    c = next(x for x in cases if x["case_id"]=="c13_ttl_zero_not_cached")
    d = evaluate.classify(c)
    assert d["ttl_zero_no_cache"] is True
    assert d["may_serve_from_cache"] is False
    assert d["serve_stale_allowed"] is False

def test_rrset_effective_is_min():
    c = next(x for x in cases if x["case_id"]=="c15_rrset_differing_ttls")
    d = evaluate.classify(c)
    assert d["rrset_ttls_differ"] is True
    assert d["rrset_effective_ttl"] == 300  # min(300,400,500)

def test_negative_ttl_is_soa_derived():
    c = next(x for x in cases if x["case_id"]=="c18_negative_nxdomain_soa_minimum_smaller")
    d = evaluate.classify(c)
    # independent: min(3600,300)=300
    assert min(c["soa_ttl"], c["soa_minimum"]) == 300
    assert d["derived_governing_ttl"] == 300
    assert d["derived_expired"] is False

def test_clamp_large_ttl():
    c = next(x for x in cases if x["case_id"]=="c23_clamp_large_ttl")
    d = evaluate.classify(c)
    assert d["clamped"] is True
    assert d["derived_effective_ttl"] == 604800
    assert c["received_ttl"] > c["implementation_max_ttl"]

def test_max_stale_boundary():
    c_ok = next(x for x in cases if x["case_id"]=="c09_stale_8767_within_max_stale_boundary")
    c_over = next(x for x in cases if x["case_id"]=="c10_stale_beyond_max_stale")
    assert evaluate.classify(c_ok)["serve_stale_allowed"] is True
    assert evaluate.classify(c_over)["serve_stale_allowed"] is False

def test_exact_expiry_is_expired():
    c = next(x for x in cases if x["case_id"]=="c30_exact_ttl_boundary")
    d = evaluate.classify(c)
    assert d["derived_expired"] is True
    assert d["may_serve_from_cache"] is False

def test_all_cases_pass_evaluator():
    fails = []
    for c in cases:
        chk = evaluate.check_case(c)
        if not chk["ok"]:
            fails.append((c["case_id"], chk["mismatches"]))
    assert fails == [], f"evaluator mismatches: {fails}"

if __name__ == "__main__":
    # simple runner without pytest
    tests = [v for k,v in globals().items() if k.startswith("test_")]
    ok=0; fail=0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            ok+=1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
            fail+=1
        except Exception as e:
            print(f"ERROR {t.__name__}: {e}")
            fail+=1
    print(f"\n{ok}/{ok+fail} passed")
    sys.exit(0 if fail==0 else 1)
