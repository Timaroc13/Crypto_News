# Tasks: tune-crypto-scoring

## 1. Implementation

- [x] 1.1 `detect()`: capital tiers → dominant_usdc / (liquidity or volume) at ≥3%/+15, ≥10%/+15, ≥25%/+10; add `dominant_side_liquidity_pct` to the result
- [x] 1.2 Crypto subtype: `_PRICE_PAT`; `analyze_market` refines `crypto` → `crypto-price` | `crypto-event`
- [x] 1.3 `fetch_top_markets`: skip questions matching `up or down`
- [x] 1.4 `format_alert`: include category

## 2. Tests + validation

- [x] 2.1 Recompute scoring asserts in `test_wallet_flow.py` (relative math); add spec-scenario tests (small vs huge market, volume fallback)
- [x] 2.2 `test_category.py`: subtype tagging (price/event), up-or-down exclusion
- [x] 2.3 `ruff check .`, full pytest, `openspec validate tune-crypto-scoring --strict --no-interactive`

## 3. Cut over

- [x] 3.1 Reset (archive + clear) the 2-day run; restart server; verify a live scan tags subtypes and scores relatively
- [x] 3.2 METHODOLOGY §7 + README: relative thresholds, subtypes, exclusion, calibration reset #2 noted
