# Change: Update `event_type` taxonomy to MECE (v2)

## Why
The current v1 `event_type` enum is intentionally narrow (ETF_*, enforcement, hacks, etc.) and forces many real-world crypto news items into `UNKNOWN`. We want a more complete, MECE primary taxonomy while keeping `event_subtype` as the refinement field.

## What Changes
- **BREAKING**: Replace the response `event_type` enum with the MECE taxonomy (v2).
- Add `event_type = "MISC_OTHER"` as a crypto-related catch-all bucket.
- Keep `event_type = "UNKNOWN"` for non-crypto or truly unclassifiable inputs.
- Keep `event_subtype` as an optional refinement consistent with `event_type`.
- Add optional `v1_event_type` in responses to aid migration/debugging.

## Proposed MECE `event_type` values (v2)
The v2 primary taxonomy uses the MECE heading buckets (with explicit fallbacks):

- `REGULATORY_ACTION_ENFORCEMENT`
- `LEGISLATION_POLICY_DEVELOPMENT`
- `GOVERNMENT_CENTRAL_BANK_INITIATIVES`

- `INSTITUTIONAL_ADOPTION_STRATEGY`
- `CAPITAL_MARKETS_ACTIVITY`
- `FUNDING_INVESTMENT_MA`
- `MARKET_STRUCTURE_LIQUIDITY_SHIFTS`

- `COMPANY_FINANCIAL_PERFORMANCE`
- `CORPORATE_GOVERNANCE_LEADERSHIP_CHANGES`
- `BUSINESS_MODEL_STRATEGIC_PIVOT`

- `PROTOCOL_UPGRADES_NETWORK_CHANGES`
- `NEW_PROTOCOL_PRODUCT_LAUNCHES`
- `INTEROPERABILITY_INFRA_DEVELOPMENTS`
- `SECURITY_INCIDENTS_EXPLOITS`

- `TOKEN_ECONOMICS_SUPPLY_EVENTS`
- `STABLECOINS_MONETARY_MECHANICS`
- `YIELD_RATES_RETURN_DYNAMICS`

- `RWA_DEVELOPMENTS`
- `PAYMENTS_COMMERCE_CONSUMER_ADOPTION`
- `ECOSYSTEM_PARTNERSHIPS_INTEGRATIONS`

- `MISC_OTHER`
- `UNKNOWN`

## Impact
- Affected specs: `parse-api`
- Affected code:
  - `src/crypto_news_parser/models.py` (enum + response schema)
  - `src/crypto_news_parser/parser.py` (classification + subtype logic)
  - `tests/` (expectations)
  - `README.md` (API examples)
- Deployment: Cloud Run redeploy required

## Migration notes
- Clients should key off `schema_version` and/or tolerate `v1_event_type` for continuity during transition.
