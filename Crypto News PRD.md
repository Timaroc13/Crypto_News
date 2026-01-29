# **PRD — Crypto News → Structured Signals API**

**Status:** Draft  
 **Version:** v1  
 **Last Updated:** 2026-01-29  
 **Authors:** TBD

---

## **1\. Executive Summary**

This product is a **B2B, API-first intelligence layer** that converts unstructured crypto news text into **standardized, machine-readable event objects**.

Given arbitrary crypto-related text (articles, posts, press releases), the system outputs **clean, normalized JSON** that downstream systems can consume deterministically.

The API acts as the missing translation layer between **human-readable news** and **machine logic**, enabling automated trading, alerting, analytics, and agent-based decision-making.

There is no UI and no news aggregation. This is pure infrastructure.

---

## **2\. Problem Statement**

### **2.1 Current State**

Crypto news is fundamentally unstructured:

* Articles

* Blog posts

* Tweets

* Press releases

However, every serious crypto system requires **structured inputs**. As a result, teams are forced to:

* Manually tag news

* Maintain brittle regex pipelines

* Build bespoke NLP stacks with inconsistent outputs

This work is duplicated across:

* Trading firms

* Funds

* Analytics platforms

* Research desks

Every mature organization eventually builds this internally.

### **2.2 Desired Outcome**

A **canonical, standalone API** that:

* Transforms raw text into a normalized event schema

* Uses strict enums and versioned fields

* Produces confidence-weighted, queryable outputs

* Can be safely integrated into automated systems

---

## **3\. Goals & Non-Goals**

### **3.1 Goals**

| ID | Goal | Priority |
| ----- | ----- | ----- |
| G1 | Convert unstructured crypto news into structured JSON | P0 |
| G2 | Provide deterministic, schema-safe outputs | P0 |
| G3 | Enable programmatic filtering and querying | P0 |
| G4 | Support automated trading, alerts, and agents | P0 |
| G5 | Establish a canonical crypto event taxonomy | P1 |

### **3.2 Non-Goals**

| ID | Non-Goal | Rationale |
| ----- | ----- | ----- |
| NG1 | Consumer-facing UI | API-only product |
| NG2 | News sourcing or aggregation | Input text is user-provided |
| NG3 | Trading execution | Signals only |
| NG4 | Alpha or performance guarantees | Intelligence layer only |

---

## **4\. Target Users**

### **4.1 Primary Users**

* Quant trading teams

* Crypto hedge funds

* Prop trading desks

* Analytics & data startups

* AI agent developers

### **4.2 Common Use Cases**

* Event-driven trading logic

* Jurisdictional risk alerts

* Research dashboards

* Sentiment and narrative tracking

* Autonomous agent inputs

---

## **5\. Product Scope (v1)**

### **5.1 Core Capability**

Given a single block of crypto-related text, return **exactly one canonical event object**.

Multi-event extraction is explicitly out of scope for v1.

### **5.2 API Endpoint**

**POST /parse**

#### **Headers**

* `Content-Type: application/json`
* `Authorization: Bearer <API_KEY>`

#### **Request**

`{`  
  `"text": "BlackRock’s Bitcoin ETF saw $400M in inflows after SEC approval.",`  
  `"source_url": "https://example.com/article"`  
`}`

#### **Response**

`{`  
  `"event_type": "ETF_INFLOW",`  
  `"topics": ["ETF", "REGULATION"],`  
  `"assets": ["BTC"],`  
  `"entities": ["BlackRock", "SEC"],`  
  `"jurisdiction": "US",`  
  `"sentiment": "positive",`  
  `"impact_score": 0.74,`  
  `"confidence": 0.81,`  
  `"time_horizon": "short_term",`  
  `"schema_version": "v1",`  
  `"model_version": "news-parser-1.0"`  
`}`

#### **Response (no match)**

If the text does not cleanly map to any v1 canonical event type, the API returns a valid, schema-compliant response with:

* `event_type = "UNKNOWN"`
* All other fields best-effort populated from the text (e.g., `assets`, `entities`, `sentiment`, `confidence`, etc.)

---

## **6\. Event Model**

### **6.1 Event Cardinality**

* **Exactly one `event_type` per request**

* If multiple events are detected:

  * The highest-impact primary event is selected (see §6.2)

  * All others are ignored

* If no event matches the v1 taxonomy:

  * `event_type = "UNKNOWN"`

  * The response MUST still be schema-valid

### **6.2 Primary Event Selection (v1)**

When multiple candidate events are detected, the API selects the single returned `event_type` as follows:

1. Generate a set of candidate event hypotheses from the text (each hypothesis has its own extracted entities/assets and provisional confidence).
2. Compute `impact_score` for each candidate (0.0–1.0).
3. Select the candidate with the highest `impact_score`.
4. Tie-breakers (in order):
   * Higher `confidence`
   * Higher precedence rank (stable table below)
   * First mention order in the text

**Precedence table (used only for ties):**

1) EXCHANGE_HACK
2) ENFORCEMENT_ACTION
3) STABLECOIN_DEPEG
4) ETF_APPROVAL / ETF_REJECTION
5) ETF_INFLOW / ETF_OUTFLOW
6) ETF_FILING
7) PROTOCOL_UPGRADE
8) STABLECOIN_ISSUANCE
9) CEX_INFLOW / CEX_OUTFLOW
10) MINER_SHUTDOWN
11) UNKNOWN

---

## **7\. Event Taxonomy (v1)**

### **7.1 Canonical Event Types**

Closed-set enum for v1:

* UNKNOWN

* ETF\_APPROVAL

* ETF\_REJECTION

* ETF\_FILING

* ETF\_INFLOW

* ETF\_OUTFLOW

* ENFORCEMENT\_ACTION

* EXCHANGE\_HACK

* STABLECOIN\_ISSUANCE

* STABLECOIN\_DEPEG

* CEX\_INFLOW

* CEX\_OUTFLOW

* PROTOCOL\_UPGRADE

* MINER\_SHUTDOWN

**No new event types may be added to v1.**  
 Extensions require a new API version.

---

## **8\. Output Schema**

### **8.1 Required Fields**

| Field | Type | Description |
| ----- | ----- | ----- |
| event\_type | enum | Canonical event classification |
| topics | string\[\] | High-level themes |
| assets | string\[\] | Uppercase tickers |
| entities | string\[\] | Normalized proper nouns |
| jurisdiction | enum | Geographic scope |
| sentiment | enum | positive / neutral / negative |
| impact\_score | float | 0.0–1.0 market relevance |
| confidence | float | 0.0–1.0 model confidence |
| schema\_version | string | Response schema version (e.g., `v1`) |
| model\_version | string | Parser/model version identifier |

### **8.2 Optional Fields**

| Field | Type | Description |
| ----- | ----- | ----- |
| market\_direction | enum | bullish / bearish / neutral |
| systemic\_risk | boolean | Market-wide implications |
| retail\_relevant | boolean | Consumer-facing relevance |
| time\_horizon | enum | short\_term / medium\_term / long\_term |

### **8.3 Notes on Topics (v1)**

`topics` are intentionally **non-enforced** in v1 (free-form strings). They should be stable and reasonably canonical, but are not a closed enum until a future version.

---

## **9\. Jurisdiction Resolution (v1)**

### **9.1 Jurisdiction Enum (v1)**

Allowed values:

* `US`
* `AMERICAS_NON_US`
* `EUROPE`
* `ASIA`
* `AFRICA`
* `OCEANIA`
* `GLOBAL`

### **9.2 Resolution Rules**

* Jurisdiction is inferred **only when explicitly referenced** (e.g., SEC → US).

* If no explicit signal exists:

  * `jurisdiction = "GLOBAL"`

* No probabilistic guessing in v1.

* If multiple explicit jurisdictions are referenced, choose the most central jurisdiction to the primary event; otherwise fall back to `GLOBAL`.

---

## **10\. Determinism & Reproducibility**

### **10.1 Deterministic Mode**

Optional request parameter:

`{`  
  `"text": "...",`  
  `"deterministic": true`  
`}`

When enabled:

* Same input text \+ same model version → same output

* Suitable for backtesting and audits

### **10.2 Versioning**

Every response includes:

* `schema_version`

* `model_version`

---

## **11A\. Input Constraints (v1)**

* `text` must be a non-empty UTF-8 string.
* Max length: **20,000 characters** (reject larger inputs with an explicit error).
* Language: v1 is optimized for **English**. Non-English inputs are accepted but may reduce extraction quality (they are not an error by default).

---

## **11\. System Architecture (High Level)**

`Client`  
  `│`  
  `│ POST /parse`  
  `▼`  
`API Gateway`  
  `│`  
  `├─ Text Normalization`  
  `├─ Event Classification`  
  `├─ Entity & Asset Extraction`  
  `├─ Sentiment Analysis`  
  `├─ Impact Scoring`  
  `│`  
  `▼`  
`Structured JSON Response`

---

## **12\. Performance Targets**

| Metric | Target |
| ----- | ----- |
| p95 latency | \< 700ms |
| Schema validity | 100% |
| API availability | 99.9% |
| Error transparency | Explicit failures only |

v1 prioritizes **analysis depth over ultra-low latency**.

---

## **12A\. Errors & Failure Modes (v1)**

The API returns **typed, explicit errors** for invalid requests or system failures. Parsing uncertainty is represented via `confidence` and, when necessary, `event_type = "UNKNOWN"`.

### **12A.1 Error Response Shape**

`{`
  `"error": {`
    `"code": "INVALID_REQUEST",`
    `"message": "Human-readable summary.",`
    `"details": {}`
  `}`
`}`

### **12A.2 HTTP Status Codes**

* `400` Invalid JSON / malformed request body
* `415` Unsupported media type (non-JSON)
* `422` Valid JSON but invalid semantics (e.g., missing/empty `text`)
* `413` Payload too large (exceeds max `text` length)
* `429` Rate limit exceeded
* `500` Internal error (explicit failure; no partial success)

---

## **13\. Monetization & Rate Limits**

### **13.1 Pricing Tiers**

| Tier | Limits | Price |
| ----- | ----- | ----- |
| Free | 100 requests/day | $0 |
| Pro | 10k requests/month | $29 |
| Funds | Unlimited (soft cap) | $199 |
| Enterprise | Custom | Contract |

### **13.2 Enforcement**

* API key required

* Per-key rate limiting

* Hard enforcement on Free tier

**Note:** Tier pricing/billing mechanics (overages, soft caps, burst/QPS numbers) are deferred to a later iteration; v1 will enforce basic per-key limits sufficient to protect availability and latency.

---

## **14\. Security & Abuse Considerations**

* Text-only input (no URLs fetched)

* No code execution

* Rate limiting and abuse detection

* No side effects or state mutation

---

## **15\. Roadmap**

### **v1**

* Single-event extraction

* English-only input

* Fixed taxonomy

### **v2**

* Multi-event extraction

* Webhooks / streaming output

* Extended taxonomy

### **v3**

* Historical backfill

* Event correlation

* Cross-event reasoning

---

## **16\. Explicit Out of Scope (v1)**

* News aggregation

* Price prediction

* Alpha guarantees

* UI dashboards

* Multi-event outputs

---

## **17\. Success Metrics**

| Metric | Description |
| ----- | ----- |
| Active API keys | Adoption |
| Requests per customer | Depth of integration |
| Paid conversion | Free → Pro |
| Retention | Stickiness |
| Automation usage | Used in live systems |

---

## **18\. Open Questions (Post-v1)**

* Multi-event response format

* Non-English language support

* Streaming vs polling

* Ontology governance process

---

**End of Document**

