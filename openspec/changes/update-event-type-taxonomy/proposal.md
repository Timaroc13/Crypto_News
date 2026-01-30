# Change: Update `event_type` taxonomy to MECE (v2)

## Why
The current v1 `event_type` enum is intentionally narrow (ETF_*, enforcement, hacks, etc.) and forces many real-world crypto news items into `UNKNOWN`. We want a more complete, MECE primary taxonomy while keeping `event_subtype` as the refinement field.

## What Changes
- **BREAKING**: Replace the response `event_type` enum with the MECE taxonomy (v2).
- Add `event_type = "MISC_OTHER"` as a crypto-related catch-all bucket.
- Keep `event_type = "UNKNOWN"` for non-crypto or truly unclassifiable inputs.
- Keep `event_subtype` as an optional refinement consistent with `event_type`.
- Add optional `v1_event_type` in responses to aid migration/debugging.

## Proposed MECE `event_type` values (initial v2 set)
Based on the current golden set in [eval/golden_cases.jsonl](eval/golden_cases.jsonl):

- `REGULATORY_GUIDANCE`
- `CRYPTO_REGULATION_RESTRICTION`
- `CRYPTO_POLICY_MEETING`
- `FUND_RAISE`
- `STRATEGIC_INVESTMENT`
- `CORPORATE_BITCOIN_PURCHASE`
- `CRYPTO_MARKET_VOLATILITY`
- `MACRO_MARKET_SHOCK`
- `NETWORK_VALIDATOR_DECLINE`
- `STABLECOIN_LAUNCH`
- `STABLECOIN_IMPACT_WARNING`
- `STABLECOIN_RESERVE_UPDATE`
- `CRYPTO_EXCHANGE_PRODUCT_EXPANSION`
- `CRYPTO_PAYMENTS_COMPANY_UPDATE`
- `TOKENIZED_ASSET_VOLUME_SURGE`
- `TOKENIZED_EQUITIES_STRATEGY`
- `IPO_FILING`
- `IPO_PLANNING`
- `IPO_MARKET_DEBUT`
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
