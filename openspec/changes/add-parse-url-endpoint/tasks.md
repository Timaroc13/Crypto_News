## 1. Specification
- [ ] 1.1 Define URL-parse endpoint contract in `parse-api` delta spec
- [ ] 1.2 Define security and limits requirements (SSRF, timeouts, max size, allow/deny lists)

## 2. Implementation
- [ ] 2.1 Add new endpoint (recommended: `POST /parse_url`) accepting `{url, deterministic, source_name?, source_published_at?}`
- [ ] 2.2 Implement safe fetcher (deny private ranges, redirects policy, timeouts, size limits)
- [ ] 2.3 Implement HTML-to-text extraction and normalization
- [ ] 2.4 Reuse existing parse pipeline to produce the same v2 response schema

## 3. Validation
- [ ] 3.1 Add tests for SSRF denials + timeouts + size limit + non-HTML responses
- [ ] 3.2 Run `pytest` and strict eval
