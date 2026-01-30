# Change: Accept URL input for parsing

## Why
Many users will paste links rather than raw article text. Supporting URL input reduces friction and improves consistency of extracted text.

This change intentionally expands beyond the current "text-only" constraint, so it must be explicitly spec’d with security safeguards.

## What Changes
- Add URL-based parsing capability that fetches a remote document, extracts text, and then runs the same parsing pipeline.
- Maintain the existing `POST /parse` (text-only) behavior unchanged.

## Impact
- Affected spec: `parse-api`
- New security considerations: SSRF protection, strict timeouts, max response size, content-type validation, HTML-to-text extraction.
- Compatibility: additive if introduced as a new endpoint (recommended).
