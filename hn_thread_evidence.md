# HN Thread Evidence — 49468083

Thread: https://news.ycombinator.com/item?id=49468083
Title: Saving 100 terabytes of memory by optimizing 1.1.1.1's DNS cache
Linked article: https://blog.cloudflare.com/dns-cache-memory-optimization-1111/
Accessed via: Hacker News Firebase API (`https://hacker-news.firebaseio.com/v0/item/{id}.json`)
Date accessed: 2026-09-16
Nodes retrieved: 19

Full sanitized dump: `hn_comments_sanitized.txt`
Raw nodes JSON: `hn_nodes_sanitized.json`

## Story metadata (from API)
- id: 49468083
- score: 925
- descendants: 286
- kids (top-level, first 10): [49470370, 49468431, 49468667, 49469283, 49474335, 49474452, 49473466, 49472612, 49470365, 49470006]

## Comments actually retrieved and used in claims table

All excerpts below are verbatim from the Firebase API (HTML-unescaped, truncated for evidence). They are the ONLY comments used to populate the README “HN claims checked” table — no invented comments.

### 49469807 — pbhjpbhj
> >that is only good for the period of the TTL of the record.<p>Not really, TTLs are often short, but IPs might not change for years.<p>You can probably generate your own TTL, at scale, and avoid many DNS requests.

### 49470326 — fc417fc802
> Why would anyone want to use a DNS resolver that tampered with records on a large scale? The TTL is intentionally set by the originator of the record.<p>Or alternatively, if you don't tamper why would I want to use a service that serves stale data?

### 49470124 — otterley
> In DNS, the owner of each record has full control over its TTL. Intermediary DNS servers are required to honor them and are not permitted to replace TTLs with their own.

### 49470257 — ButlerianJihad
> Actually that is not true. The IETF has expanded the definition of “TTL” and explicitly permits resolvers to serve “stale” RRs beyond their expiration time.<p><a href="https://www.rfc-editor.org/info/rfc8767/" rel="nofollow">https://www.rfc-editor.org/info/rfc8767/</a><p>As a corollary, there is obviously no floor on refetching unexpired RRs, of course, except for efficiency concerns.

### 49470297 — seiferteric
> That's only when the authoritative server cant be reached though

### 49470290 — pbhjpbhj
> You are obliged to pass on the TTL, you're not obliged to cache according to it.<p>At least in my country (UK) I know of no law relating to DNS caching.<p>Why throwaway perfectly good data every few minutes that is only modified every couple of years, just so someone can move their domain quickly when they eventually wish to? It is my contention that a [caching] DNS service can do far better. Trusting user (domain owner) input blindly is not for me.

### 49470406 — otterley (reply)
> It's not some sort of public law with public enforcement, but it is in the RFCs that govern the protocol.<p>I should be a bit clearer here; the TTL is an <i>upper bound</i> on how long it can be cached. Caches are free to consult more frequently but not less frequently. That said, out of respect for upstream cache operators and authoritative servers, most DNS caches honor TTLs as best they can.

### 49473714 — inigyou
> The IETF isn't the internet police. You don't have to follow its advice.

## Notes
- The thread is about Cloudflare's Big Pineapple DNS cache memory optimization (250B entries, 100TB fleet saving). The DNS-TTL subthread is under mannyv → seiferteric → pbhjpbhj.
- Excerpts retrieved via Firebase API before README was written, as required.
- No live DNS queries were made. Evidence files are local copies of API responses.
