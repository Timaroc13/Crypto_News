## MODIFIED Requirements

### Requirement: Parse endpoint
The system SHALL expose `POST /parse` which accepts user-provided text and returns exactly one schema-valid event object.

#### Scenario: Successful parse (v2)
- **WHEN** the client submits a valid JSON body containing a non-empty `text` string
- **THEN** the API returns HTTP 200
- **AND** the response matches the v2 response schema
- **AND** the response includes `schema_version = "v2"` and `model_version`

### Requirement: Event taxonomy (primary)
The system SHALL return exactly one `event_type` per request from the v2 MECE taxonomy.

#### Scenario: Classified into a v2 category
- **WHEN** the input text maps to a known v2 category
- **THEN** the response contains `event_type` set to one of the documented v2 enum values

### Requirement: Crypto-related catch-all
The system SHALL use `event_type = "MISC_OTHER"` for crypto-related inputs that do not map to any other v2 category.

#### Scenario: Crypto-related but no specific v2 match
- **WHEN** the input is crypto-related
- **AND** no specific v2 category can be inferred
- **THEN** the response contains `event_type = "MISC_OTHER"`

### Requirement: Non-crypto / unknown behavior
The system SHALL use `event_type = "UNKNOWN"` for non-crypto inputs or inputs that cannot be classified.

#### Scenario: Non-crypto or unclassifiable
- **WHEN** the input is not crypto-related OR cannot be classified
- **THEN** the response contains `event_type = "UNKNOWN"`

### Requirement: Event subtype
The system SHALL support an optional `event_subtype` field in the response.

`event_subtype` is an implementation-defined string intended to provide finer-grained categorization while keeping `event_type` as the stable primary classification.

#### Scenario: Subtype omitted when unknown
- **WHEN** the system cannot confidently infer a subtype
- **THEN** the response contains `event_subtype = null`

### Requirement: Legacy v1 mapping
The system SHALL include a best-effort legacy mapping to the v1 taxonomy via a nullable `v1_event_type` field.

#### Scenario: v1 mapping provided
- **WHEN** the system classifies an input into a v2 `event_type`
- **THEN** the response includes `v1_event_type` (which MAY be `null`)
