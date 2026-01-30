# Capability: Parse API (v1)

## MODIFIED Requirements

### Requirement: Parse endpoint
The system SHALL expose `POST /parse` which accepts user-provided text and returns exactly one schema-valid event object.

#### Scenario: Successful parse includes subtype when available
- **WHEN** the client submits a valid JSON body containing a non-empty `text` string
- **THEN** the API returns HTTP 200
- **AND** the response matches the v1 response schema
- **AND** the response includes `schema_version` and `model_version`
- **AND** the response MAY include `event_subtype` to provide finer-grained labeling

## ADDED Requirements

### Requirement: Event subtype
The system SHALL support an optional `event_subtype` field in the v1 response.

`event_subtype` is an implementation-defined string intended to provide finer-grained categorization while keeping `event_type` as the stable primary classification.

#### Scenario: Subtype omitted when unknown
- **WHEN** the system cannot confidently infer a subtype
- **THEN** the response contains `event_subtype = null` (or the field is omitted)

#### Scenario: Catch-all subtype for crypto-related unknowns
- **WHEN** the input is crypto-related but does not map to any canonical v1 `event_type`
- **THEN** the response contains `event_type = "UNKNOWN"`
- **AND** the response MAY set `event_subtype = "misc"`

#### Scenario: Subtype does not contradict event_type
- **WHEN** the system returns a subtype
- **THEN** the subtype MUST be consistent with the returned `event_type`
- **AND** the system MUST NOT change the v1 `event_type` enum or existing mapping behavior
