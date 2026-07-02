# Capability: Market Category — crypto subtypes + noise exclusion

## ADDED Requirements

### Requirement: Crypto subtype tagging
Markets classified `crypto` SHALL be stored with a subtype category: `crypto-price` when the question is a price-threshold pattern (dip to / reach / above / below / hit a dollar level, or "price of X on <date>"), otherwise `crypto-event` (sales, airdrops, listings, hacks, all-time highs, and other event markets — the insider-thesis cases). The `crypto` entry in a scan allow-list SHALL match both subtypes.

#### Scenario: Price market
- **WHEN** the question is "Will Bitcoin dip to $57,500 in June?"
- **THEN** the stored category is `crypto-price`

#### Scenario: Event market
- **WHEN** the question is "Over $25M committed to the Laso Finance public sale?"
- **THEN** the stored category is `crypto-event`

#### Scenario: Breakdown separates subtypes
- **WHEN** both subtypes have resolved markets
- **THEN** the dashboard category breakdown reports `crypto-price` and `crypto-event` as separate rows

### Requirement: Noise-market exclusion
Markets whose question matches an "Up or Down" pattern SHALL be excluded from scans at fetch time — they are coin-flip momentum markets with no information content.

#### Scenario: Up-or-down excluded
- **WHEN** the candidate pool contains "Bitcoin Up or Down - July 1, 9AM ET"
- **THEN** it is not analyzed or stored
