## Context
We want to accept URLs as input and parse the resulting article content using the same v2 parsing pipeline.

This expands the threat surface (network egress + HTML parsing) beyond the current text-only API.

## Goals / Non-Goals
- Goals:
  - Provide a simple URL-based parse workflow for users.
  - Keep `POST /parse` behavior unchanged.
  - Prevent SSRF and resource exhaustion.
  - Keep behavior deterministic given the fetched content.
- Non-Goals:
  - Crawling, feed ingestion, or multi-hop aggregation.
  - Circumventing paywalls or authentication.
  - Perfect article extraction for every website (best-effort).

## Decisions
### Decision: Add `POST /parse_url` (new endpoint)
- Rationale: avoids breaking `POST /parse` contract and keeps text-only clients stable.

### Decision: Use safe fetch rules with explicit limits
**Fetch policy (recommended defaults):**
- Allow schemes: `https` and `http` (prefer https)
- Deny all other schemes (`file:`, `ftp:`, `gopher:`, etc.)
- DNS resolution: resolve host and validate all resolved IPs
- Deny IP ranges:
  - Loopback: `127.0.0.0/8`, `::1`
  - Private: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
  - Link-local: `169.254.0.0/16`, `fe80::/10`
  - Reserved/multicast (as feasible)
- Redirects:
  - Max redirects: 3
  - Re-validate destination URL and destination IP on every redirect
- Timeouts:
  - Connect timeout: 3s
  - Read timeout: 8s
  - Total deadline: 12s
- Size limits:
  - Max bytes read: 2 MiB (hard stop)

### Decision: Content-type gating + extraction
- Accept `text/html` and `text/plain`.
- For HTML:
  - Strip scripts/styles
  - Prefer `<article>` if present
  - Fallback to visible text extraction
- For plain text:
  - Use as-is.

### Decision: Determinism boundary
- Deterministic output for `POST /parse_url` is defined as: deterministic given the fetched bytes.
- If remote content changes, output may change. We should store/return `fetched_at` and optionally a `content_hash` in logs (future work).

## Risks / Trade-offs
- Some sites block bots or require JS rendering; we will not use a headless browser initially.
- SSRF risk must be treated as critical; deny-by-default policies may reduce URL coverage.

## Error Mapping
- Private IP / blocked host: HTTP 400
- Timeout: HTTP 504
- Too large: HTTP 413
- Unsupported content-type: HTTP 415
- Fetch error (5xx from remote, DNS failure): HTTP 502

## Migration Plan
- Add endpoint behind a feature flag/environment variable initially (optional).
- Roll out gradually; monitor error rates and fetch timeouts.

## Open Questions
- Do we require API key auth before enabling `POST /parse_url` in Cloud Run?
- Should we allow only a curated allowlist of domains initially?
