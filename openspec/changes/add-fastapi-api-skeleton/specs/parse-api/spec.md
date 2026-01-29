# Capability: Parse API (v1)

## ADDED Requirements

### Requirement: Parse endpoint
The system SHALL expose `POST /parse` which accepts user-provided text and returns exactly one schema-valid event object.

#### Scenario: Successful parse
- **WHEN** the client submits a valid JSON body containing a non-empty `text` string
- **THEN** the API returns HTTP 200
- **AND** the response matches the v1 response schema
- **AND** the response includes `schema_version` and `model_version`

### Requirement: No-match behavior
The system SHALL return `event_type = "UNKNOWN"` when the input does not map to any canonical v1 event type.

#### Scenario: No match
- **WHEN** the input text contains no clear v1 event
- **THEN** the API returns HTTP 200
- **AND** the response contains `event_type = "UNKNOWN"`

### Requirement: Input constraints
The system SHALL reject requests that exceed the maximum supported `text` size.

#### Scenario: Payload too large
- **WHEN** `text` exceeds the configured maximum length
- **THEN** the API returns HTTP 413
- **AND** the response matches the error schema

### Requirement: Error schema
The system SHALL return typed error responses with a stable JSON shape.

#### Scenario: Invalid semantics
- **WHEN** the request JSON is well-formed but `text` is missing or empty
- **THEN** the API returns HTTP 422
- **AND** the response matches the error schema
