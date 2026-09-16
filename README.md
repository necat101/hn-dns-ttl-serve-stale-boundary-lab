# hn-dns-ttl-serve-stale-boundary-lab

Deterministic Python-stdlib + shell lab that enforces the DNS TTL boundary:

**TTL upper bound ≠ mandatory cache residency ≠ ordinary expired use ≠ RFC 8767 serve-stale ≠ negative-cache TTL**

Testing the claim: *“An authoritative TTL is a required cache lifetime: resolvers should keep an RR until that exact time, must discard it immediately afterward, and serving an expired RR is always noncompliant.”* — **FALSE.**

## One-sentence verdicts

- **TTL vs retention:** RFC 2181 TTL is a **maximum** time to live, not a mandatory residency; resolvers may evict or refresh earlier without violating the protocol.
- **Serve-stale:** RFC 8767 permits serving expired data **only** as a failure-mode exception (RD=1, authority unrefreshable, within max-stale, response TTL >0) — it does not turn expired data into ordinary fresh cache data.

## What this lab is / is not

- **Is:** A local correctness lab classifying *protocol/cache state* (fresh vs expired vs stale-eligible) from synthetic facts. No network, no DNS.
- **Is not:** A certifier of any real resolver implementation, not a performance benchmark, not a DNS client.

## Hacker News thread access

The Hacker News tool (Hacker News Firebase API CLI) was used to read HN item **49468083** *before* writing this README. Claims below are derived from actual API output, not invented.

- Thread: https://news.ycombinator.com/item?id=49468083
- Title: *Saving 100 terabytes of memory by optimizing 1.1.1.1's DNS cache*
- Linked article: https://blog.cloudflare.com/dns-cache-memory-optimization-1111/
- Evidence: `hn_thread_evidence.md`, `hn_comments_sanitized.txt`, `hn_nodes_sanitized.json`
- Date accessed: 2026-09-16
- Nodes retrieved: 19
- Store: 250B cache entries, ~100 TB fleet memory saving (p99 9.3→5.3 GB per instance)

## Base TTL rule (RFC 2181)

RFC 2181 §8: *“The TTL specifies a maximum time to live, not a mandatory time to live.”* The authoritative TTL is an **upper bound** on how long an RR MAY be cached before the source MUST again be consulted. It does not require retention until expiry. A resolver that discards or refreshes earlier is compliant; one that treats expiry as optional ordinary use is not.

- Synthetic verification: `c01`/`c02` (inside TTL → `may_serve=true`), `c30` (exact expiry → expired), evaluator derives `expired = elapsed >= governing_ttl` independently.

## Resolver implementation freedom

- No floor on refetching unexpired data — only efficiency concern (ButlerianJihad #49470257 corollary). `c03` (evict at 100s of 3600s) and `c04` (refresh 86400 at 3600s) both `PASS`: `may_evict_early=true`, `ttl_upper_bound=true`.
- Implementation MAY clamp a received TTL to a configured maximum (RFC 8767 recommends 7 days = 604800s). `c23` (2^31−1→604800 clamped), `c24` (1M→604800), `c25` (300 unchanged).

## Serve-stale exception (RFC 8767)

RFC 8767 amends TTL to allow retention **beyond** expiry and serving stale **only when the data cannot be authoritatively refreshed**. Key constraints encoded in `evaluate.py` (derived, not trusted):

1. Record **expired** (`elapsed >= TTL`)
2. Query has **RD=1** (recursive desired); RD=0 → referral, not stale (c11)
3. `stale_config_enabled=true` and `stale_age <= max_stale` (c09 within 1–3 day window, c10 beyond ⇒ purged)
4. **Authoritative refresh requires RCODE 0/3 + AA=1** (RFC 8767 §4). Reachable `NOERROR AA=1` (c05) and `NXDOMAIN AA=1` (c33) establish refresh; reachable `NOERROR AA=0` (c31) or `NXDOMAIN AA=0` (c32) — RCODE alone is insufficient, not authoritative refresh, and the lab does not turn that into a stale-MUST.
5. **Failure to refresh**: authority unreachable *or* RCODE not in {0,3} (e.g., SERVFAIL) — stale may be used (c07/c08) provided AA-bit rule above does not claim refresh.
6. **Stale response TTL: MUST >0, RECOMMENDED 30** — distinct outputs `stale_ttl_valid` (>0) and `stale_ttl_recommended_value` (==30). TTL 30 (c36) valid+recommended, TTL 60 (c34) valid but not recommended, TTL 0 (c35) invalid.
7. TTL 0 records are **never cached** (`c13`/`c14`: transaction-only, no stale)

Result: `c07`/`c08`/`c09`/`c34`/`c36` `serve_stale_allowed=true`; `c05`/`c06`/`c27`/`c33` refresh blocks stale; `c31`/`c32` AA-insufficient blocks stale without claiming refresh; `c26` (feature disabled) blocked; stale does **not** imply `may_serve_from_cache=true` — the two flags are distinct.

## Negative caching (RFC 2308)

Negative cache lifetime (NXDOMAIN/NODATA) is **not** the positive RR TTL. It is derived from the SOA: `min(SOA TTL, SOA MINIMUM)`.

- `c18`: SOA 3600, MINIMUM 300 → 300
- `c19`: SOA 300, MINIMUM 3600 → 300
- `c20` (NODATA): 900/300 → 300
- `c22`: 600/600 → 600
- `c21`: expired negative (400 > 300) → must refetch, same upper-bound logic
- `c28` documents that positive TTL comes from RR TTL, not SOA — the boundary marker.

## Cloudflare deployment behavior

From https://blog.cloudflare.com/dns-cache-memory-optimization-1111/ (Big Pineapple, the platform behind 1.1.1.1): five Rust layout changes (Vec→Box<[T]>, single list+u16 offsets, dropping identical owner, boxing large enum variants → wire-format buffer) cut per-entry from 953→420 bytes (56%), insert +43%, lookup −19%; production p99 9.3→5.3 GB; ~100 TB fleet saving measured during May 18–July 6 2026 rollout.

**Boundary:** This is a *deployment measurement* (how Cloudflare packs 250B entries in RAM), **not** permission to redefine TTL semantics. `c29` marks `deployment_measurement=true`, `not_semantic_permission=true`.

## HN inference — claims checked

Only comments **actually retrieved** via Firebase API are cited. IDs link to `https://news.ycombinator.com/item?id=<id>`.

| # | Proposition (as phrased in thread) | Comment | Verdict against RFCs |
|---|---|---|---|
| 1 | A resolver can generate its own longer TTL at scale and avoid refreshes | 49469807 *pbhjpbhj*: “You can probably generate your own TTL, at scale, and avoid many DNS requests.” | **Noncompliant** if extending beyond authoritative TTL for ordinary cache hits. TTL is an upper bound *from the authority*; a resolver may cache **less** (shorter TTL / early evict) but may not invent a longer TTL for normal service. Extending is only permissible under RFC 8767 stale conditions (failure + cap + RD + TTL>0). |
| 2 | Owners control TTL and stale serving is inherently wrong / tampering | 49470326 *fc417fc802*: “Why would anyone want to use a DNS resolver that tampered with records on a large scale? The TTL is intentionally set by the originator…” | **Partially true, partially false.** Owners *do* control the authoritative TTL, and ordinary extension *is* tampering. But RFC 8767 *explicitly* permits stale as a bounded resiliency exception — not ordinary use — so “always wrong” is false. |
| 3 | RFC 8767 explicitly permits stale records | 49470257 *ButlerianJihad*: “Actually that is not true. The IETF has expanded the definition of ‘TTL’ and explicitly permits resolvers to serve ‘stale’ RRs…” + link to RFC 8767 | **True**, with scope. Serves as standards-track amendment to RFCs 1034/1035/2181; but only under failure conditions and with TTL>0 rewrite. |
| 4 | Serve-stale applies only when authoritative refresh is failing | 49470297 *seiferteric*: “That's only when the authoritative server cant be reached though” | **True** (with nuance). RFC 8767 §4–5: failure = unreachable *or* non-NoError/NXDomain RCODEs (e.g., SERVFAIL). Success (NoError/NXDomain + AA) refreshes and stale must not be used — verified `c05`/`c27` blocked, `c07`/`c08` allowed. |
| 5 | TTL is an upper bound, so earlier refresh is allowed | 49470406 *otterley*: “TTL is an *upper bound* on how long it can be cached. Caches are free to consult more frequently but not less frequently…” | **True**. Directly RFC 2181 §8; evaluator encodes `may_evict_early=true` for all cases; `c03`/`c04` exercise it. |
| 6 | IETF requirements are merely optional advice | 49473714 *inigyou*: “The IETF isn't the internet police. You don't have to follow its advice.” | **False as compliance claim.** Operationally you *can* ignore IETF, but the lab defines compliance *relative to* RFC 2181/8767/2308. Within that frame, TTL upper bound and stale conditions are normative (MUST/SHOULD). The evaluator reports protocol state, not legal enforcement. |

If a proposition were not present in retrieved evidence, it would not be listed — the table above uses only the six actually retrieved.

## Coverage map (36 synthetic cases, all TTL types + states)

| Case | Category | What it proves |
|---|---|---|
| c01 c02 | positive inside TTL | Fresh cache hit allowed |
| c03 c04 | impl freedom | Early evict/refresh before expiry is compliant |
| c05 c06 | expired, auth reachable | Ordinary stale **must not** be served |
| c07 c08 c09 c34 c36 | serve-stale (failure) | Stale **allowed** only on unreachable / SERVFAIL / within max-stale; TTL 30 valid+recommended, 60 valid, 0 invalid |
| c10 | serve-stale | Beyond max-stale ⇒ purged, not served |
| c11 c12 | RD flag | RD=0 expired ⇒ no stale (referral); fresh RD=0 still ok |
| c13 c14 | TTL 0 | Transaction-only, never cached, no stale |
| c15 c16 c17 | RRset | Differing TTLs ⇒ effective is min (RFC2181 §5.2) |
| c18 c19 c20 c21 c22 | negative | SOA-derived TTL = min(TTL, MINIMUM); not RR TTL; expired negative must refetch |
| c23 c24 c25 | clamp | Large TTL clamped to 7-day cap; small not clamped |
| c26 c27 c33 | stale guards | Disabled config / NoError+NXDOMAIN AA=1 refresh ⇒ no stale |
| c31 c32 | AA-bit | RCODE 0/3 AA=0 insufficient — not refresh, not stale-MUST |
| c34 c35 c36 | stale TTL | MUST >0 vs RECOMMENDED 30: 60 valid, 0 invalid, 30 both |
| c28 | boundary marker | Positive TTL is RR TTL, not SOA |
| c29 | deployment | 100TB = measurement, not semantic permission |
| c30 | exact boundary | elapsed==TTL ⇒ expired |

## Run it

```bash
python3 -m py_compile generate_cases.py evaluate.py run_lab.py tests/test_lab.py
python3 generate_cases.py
python3 evaluate.py
python3 run_lab.py
python3 tests/test_lab.py        # independent tests derive expected from facts
# or
python3 -m pytest tests/test_lab.py -v
bash run.sh
```

## Recorded results (actual run)

```
PASS 36/36 evaluator — Python 3.12.3
PASS 19/19 independent tests — each derives AA + TTL validity from facts, not fixture labels
```

See `RESULTS.md`, `results_rows.csv`, `results_rows.json`.

## What this lab does NOT do

- No live DNS queries, sockets, dig, or external packages
- No resolver certification — classifies protocol state, not implementation correctness
- No fabricated performance numbers — Cloudflare numbers are cited from the article as deployment measurements
- No claim of global DNS wins — scoped to the 30 synthetic cases

## References

- RFC 2181 §8, §5.2 (TTL upper bound, RRset TTL rules): https://www.rfc-editor.org/rfc/rfc2181.txt
- RFC 8767 (serve-stale): https://www.rfc-editor.org/rfc/rfc8767.txt
- RFC 2308 (negative caching): https://www.rfc-editor.org/rfc/rfc2308.txt
- Cloudflare: https://blog.cloudflare.com/dns-cache-memory-optimization-1111/
- HN item 49468083: https://news.ycombinator.com/item?id=49468083
- Evidence: `hn_thread_evidence.md`, `hn_comments_sanitized.txt`, `hn_nodes_sanitized.json`

## Repo

https://github.com/necat101/hn-dns-ttl-serve-stale-boundary-lab
