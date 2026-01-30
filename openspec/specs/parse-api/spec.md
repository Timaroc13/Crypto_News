# Capability: Parse API (v2)

## Purpose
Provide a low-cost, stateless HTTP API that converts crypto-news text into a stable v2 structured event response.

## Requirements

### Requirement: Parse endpoint
The system SHALL expose `POST /parse` which accepts user-provided text and returns exactly one schema-valid event object.

#### Scenario: Successful parse
- **WHEN** the client submits a valid JSON body containing a non-empty `text` string
- **THEN** the API returns HTTP 200
- **AND** the response matches the v2 response schema
- **AND** the response includes `schema_version = "v2"` and `model_version`
- **AND** the response includes `event_subtype` (nullable) for optional finer-grained labeling
- **AND** the response includes `v1_event_type` (nullable) for optional legacy mapping

### Requirement: Event subtype
The system SHALL support an optional `event_subtype` field in the v2 response.

`event_subtype` is an implementation-defined string intended to provide finer-grained categorization while keeping `event_type` as the stable primary classification.

#### Scenario: Subtype omitted when unknown
- **WHEN** the system cannot confidently infer a subtype
- **THEN** the response contains `event_subtype = null`

#### Scenario: Catch-all subtype for crypto-related unknowns
- **WHEN** the input is crypto-related but does not map to any specific v2 `event_type`
- **THEN** the response contains `event_type = "MISC_OTHER"`
- **AND** the response MAY set `event_subtype = "misc"`

### Requirement: Single primary event
The system SHALL return exactly one `event_type` per request.

#### Scenario: Multi-event input
- **WHEN** the input contains multiple candidate events
- **THEN** the API selects a single primary event using the documented selection rules
- **AND** all other events are ignored

### Requirement: No-match behavior
The system SHALL return a schema-valid response even when the input does not map to a specific v2 `event_type`.

#### Scenario: Non-crypto input
- **WHEN** the input text is not crypto-related
- **THEN** the API returns HTTP 200
- **AND** the response contains `event_type = "UNKNOWN"`

#### Scenario: Crypto-related but uncategorized
- **WHEN** the input text is crypto-related
- **AND** no specific v2 category can be inferred
- **THEN** the API returns HTTP 200
- **AND** the response contains `event_type = "MISC_OTHER"`

### Requirement: Input constraints
The system SHALL enforce a maximum supported `text` size and reject oversized inputs.

#### Scenario: Payload too large
- **WHEN** `text` exceeds the configured maximum length
- **THEN** the API returns HTTP 413
- **AND** the response matches the error schema

### Requirement: Error schema
The system SHALL return typed error responses with a stable JSON shape.

#### Scenario: Invalid JSON
- **WHEN** the request body is not valid JSON
- **THEN** the API returns HTTP 400
- **AND** the response matches the error schema

#### Scenario: Unsupported content type
- **WHEN** the request `Content-Type` is not JSON
- **THEN** the API returns HTTP 415
- **AND** the response matches the error schema

#### Scenario: Invalid semantics
- **WHEN** the request JSON is well-formed but `text` is missing or empty
- **THEN** the API returns HTTP 422
- **AND** the response matches the error schema
