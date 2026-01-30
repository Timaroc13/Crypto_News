## ADDED Requirements

### Requirement: Jurisdiction basis and confidence
The system SHALL include optional fields that describe how `jurisdiction` was determined.

- `jurisdiction_basis` SHALL be one of: `explicit`, `implied`, `none`.
- `jurisdiction_confidence` SHALL be a float in $[0, 1]$.

#### Scenario: Explicit jurisdiction
- **WHEN** the input contains an explicit jurisdiction signal (e.g., a country/region name or a jurisdiction-specific regulator)
- **THEN** the response contains `jurisdiction_basis = "explicit"`
- **AND** `jurisdiction_confidence >= 0.8`

#### Scenario: Implied jurisdiction
- **WHEN** the input contains an implied jurisdiction signal (e.g., institution/regulator context that implies a region)
- **THEN** the response contains `jurisdiction_basis = "implied"`
- **AND** `jurisdiction_confidence` reflects the strength of the implication

#### Scenario: No jurisdiction signal
- **WHEN** the input contains no jurisdiction signal
- **THEN** the response contains `jurisdiction_basis = "none"`
- **AND** the response MAY still set `jurisdiction = "GLOBAL"`
- **AND** `jurisdiction_confidence <= 0.4`
