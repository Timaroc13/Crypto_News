## ADDED Requirements

### Requirement: URL parse endpoint
The system SHALL support a URL-based parsing endpoint.

The system SHOULD expose `POST /parse_url` that accepts a JSON body containing:
- `url` (string, absolute URL)
- `deterministic` (boolean, optional)
- optional metadata fields used for traceability

#### Scenario: Successful URL parse
- **WHEN** the client submits a valid request with a fetchable URL
- **THEN** the API fetches the document
- **AND** extracts text content
- **AND** returns HTTP 200 with the same v2 response schema as `POST /parse`

### Requirement: URL fetching security
The system SHALL apply SSRF defenses and resource limits.

#### Scenario: Block private network access
- **WHEN** `url` resolves to a private, loopback, or link-local IP
- **THEN** the API returns HTTP 400
- **AND** the response matches the error schema

#### Scenario: Enforce maximum fetch size
- **WHEN** the fetched response exceeds the maximum allowed bytes
- **THEN** the API returns HTTP 413
- **AND** the response matches the error schema

#### Scenario: Enforce timeouts
- **WHEN** the remote server does not respond within the configured timeout
- **THEN** the API returns HTTP 504
- **AND** the response matches the error schema

#### Scenario: Unsupported content type
- **WHEN** the fetched document is not supported for text extraction
- **THEN** the API returns HTTP 415
- **AND** the response matches the error schema
