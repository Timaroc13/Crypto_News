## 1. Specification
- [ ] 1.1 Add v2 response fields requirements to `parse-api` delta spec

## 2. Implementation
- [ ] 2.1 Update response model to include `jurisdiction_confidence` and `jurisdiction_basis`
- [ ] 2.2 Populate fields in parser output (explicit/implied/none + confidence)
- [ ] 2.3 Update tests + eval harness to tolerate/optionally assert new fields

## 3. Validation
- [ ] 3.1 Run `pytest`
- [ ] 3.2 Run strict eval (`RUN_GOLDEN_STRICT=1`)
