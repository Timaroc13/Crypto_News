## ADDED Requirements

### Requirement: Persist parse inputs and outputs
The system SHALL support persisting parse requests and parse responses for later analysis.

#### Scenario: Parse is persisted
- **WHEN** persistence is enabled
- **AND** the client submits `POST /parse`
- **THEN** the system stores a record containing the request, response, and timestamps

### Requirement: Feedback endpoint
The system SHALL provide an endpoint to accept user corrections.

The system SHOULD expose `POST /feedback` that accepts:
- a `parse_id` or caller-provided `input_id`
- optional raw `text` (recommended when using `input_id` without `parse_id`, to enable export)
- optional corrected fields (`event_type`, `event_subtype`, `jurisdiction`, `assets`, `entities`, etc.)
- optional notes

#### Scenario: Submit feedback
- **WHEN** the client submits valid feedback
- **THEN** the API returns HTTP 200
- **AND** the system persists the feedback record

#### Scenario: Submit feedback with input_id and inline text
- **WHEN** the client submits feedback with `input_id` and `text` (without `parse_id`)
- **THEN** the API returns HTTP 200
- **AND** the system persists the feedback record
- **AND** exports MAY include the feedback as an eval case

### Requirement: Export feedback as JSONL
The system SHALL provide a way to export stored feedback into JSONL suitable for the existing eval harness.

#### Scenario: Export produces eval-compatible JSONL
- **WHEN** an operator runs the export tool
- **THEN** the output is one JSON object per line
- **AND** each object contains an `id`, `text`, and `expected` block compatible with `scripts/run_eval.py`

### Requirement: Security and privacy controls
The system SHALL provide controls for retention and access.

#### Scenario: Authentication required
- **WHEN** feedback persistence is enabled in a shared deployment
- **THEN** the API requires authentication for `POST /feedback`

#### Scenario: Retention policy enforced
- **WHEN** a retention period is configured
- **THEN** records older than the retention period are deleted or excluded from export
