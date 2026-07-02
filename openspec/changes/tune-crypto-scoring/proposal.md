# Change: Liquidity-relative scoring, crypto subtypes, noise-market exclusion

## Why

Two days of crypto-only scanning (180 scans, 61 markets) exposed three flaws:

1. **Tier starvation**: 180/180 scans scored LOW. The capital tiers ($5k/$20k/$100k) were
   implicitly calibrated for huge sports books; in a $30k-liquidity crypto market, $2.4k of
   fresh money (7% of the book — the largest observation) scores near zero. HIGH-tier n would
   stay 0 forever, so the gates could never be evaluated. Observed noise floor: median
   new-wallet capital is 0.44% of liquidity, p90 ≈ 4.4%.
2. **Sub-universe blindness**: 53/61 scanned markets are price markets ("Will BTC dip to $X")
   where no insider information exists; the 8 event markets (e.g. "Over $25M committed to the
   Laso Finance public sale?") are the actual thesis case — but both are tagged plain `crypto`,
   so the dashboard can't show where the edge lives.
3. **Coin-flip noise**: hourly/daily "Bitcoin Up or Down" markets carry zero information and
   pad the sample.

Per METHODOLOGY §3, changing scoring resets the calibration counter — which is why this ships
now (day 2 post-reset, n=8) rather than after weeks of unusable data.

## What Changes

- **`wallet-flow` scoring (ADDED requirement — supersedes the absolute capital tiers)**:
  capital points from dominant-side new-wallet USDC as a **fraction of market liquidity**
  (fallback: volume): ≥3% +15, ≥10% +15, ≥25% +10. Wallet-count, burst, and count-dominance
  components unchanged. Result gains `dominant_side_liquidity_pct`.
- **Crypto subtypes (ADDED)**: crypto markets are stored as `crypto-price` (price-threshold
  questions) or `crypto-event` (everything else — sales, airdrops, listings, ATHs), so the
  per-category dashboard panel separates thesis markets from momentum markets. The `crypto`
  allow-list entry matches both.
- **Noise exclusion (ADDED)**: "Up or Down" markets are skipped at fetch time.
- **Clean slate #2**: archive + clear the 2-day run (8 qualifying trades) since scoring changed.

## Impact

- Affected specs: `wallet-flow` (scoring requirement), `market-category` (subtypes, exclusion)
- Affected code: `wallet_flow.py` (detect scoring, subtype refinement, exclusion), `scheduler.py`
  (alert shows category), tests (scoring asserts recomputed), METHODOLOGY §7
- **Non-breaking API**: response fields are additive; tier semantics change by design (reset).
