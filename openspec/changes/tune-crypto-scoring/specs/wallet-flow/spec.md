# Capability: Wallet Flow — liquidity-relative scoring

## ADDED Requirements

### Requirement: Liquidity-relative capital scoring
The flow score's capital component SHALL be computed from the dominant side's new-wallet USDC as a fraction of market liquidity (falling back to total volume when liquidity is unavailable; zero points when both are unavailable): ratio ≥ 0.03 → +15, ≥ 0.10 → +15, ≥ 0.25 → +10. Wallet-count tiers (≥3/+10, ≥10/+10, ≥20/+10), volume-burst tiers, and count-dominance tiers are unchanged. Each result SHALL include `dominant_side_liquidity_pct`. This supersedes the absolute-dollar capital tiers ($5k/$20k/$100k), which were calibrated for large sports books and scored every crypto market LOW.

#### Scenario: Meaningful capital in a small market
- **WHEN** 3 new wallets hold $4,000 net on YES in a market with $30,000 liquidity (13.3%), with 100% count dominance and no burst
- **THEN** the score is 50 (count +10, capital +30, dominance +10) and the tier is MEDIUM

#### Scenario: Same dollars in a huge market score less
- **WHEN** the same $4,000 sits in a $1,000,000-liquidity market (0.4%)
- **THEN** no capital points are awarded

#### Scenario: Missing liquidity falls back to volume
- **WHEN** liquidity is 0 but total volume is $50,000 and dominant capital is $6,000 (12%)
- **THEN** capital points are +30
