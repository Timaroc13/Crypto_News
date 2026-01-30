# Change: Save parses + accept user feedback for learning

## Why
We want the system to improve over time based on real user inputs and corrections.

Rather than mutating behavior online, we can log inputs/outputs and collect structured feedback that can be used to:
- expand the eval datasets (golden/synthetic)
- refine heuristics safely
- eventually train a learned classifier

## What Changes
- Add a persistence layer to record parse requests/responses (opt-in)
- Add a feedback endpoint where users can submit corrections (expected labels)
- Provide export tooling to turn stored feedback into eval/training artifacts

## Impact
- New capability: `feedback-api`
- Requires storage (local dev: SQLite; prod: managed DB)
- Security/privacy considerations: retention, PII handling, auth, rate limits
