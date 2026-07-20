# Task 2 Brief — Signa API: Fetch-by-ID, Media, Pagination & Proposed Record Schema

## Feedback on Task 1 (Signa API Review)

The per-office field inventory was thorough and the cross-office findings
were genuinely useful. Your three findings stood out as high-value and hold up against the raw data:

- The docs-vs-API mismatch on `status.source` / `status.raw_code` / `status.raw_label`
  (documented but present in none of the 10 offices).
- The `renewal_due_date` unreliability (null on active marks with a populated `expiry_date`
  in 7 of 10 offices).
- The distinct Madrid / WIPO record shape (`ir_number` replaces `registration_number`,
  `origin_office_code` populated).

Two notes for next time:

1. **Never paste live API keys into deliverables.** The key was included in cleartext in the
   last doc — always use a placeholder like `sig_xxx` in write-ups. (The key is being rotated.)
2. First Task covered **only the search endpoint** and mostly the query `q=apple`, so the
   sample was ~90% "active" marks. This task deliberately pushes past both limits.

---

## Objective

Verify the parts of the Signa Trademark API that the first review did not cover, and turn the
findings into a small standalone tool plus a proposed normalized data model we can build on.

## What You Have

- **Endpoint base:** `https://api.signa.so/v1`
- **Auth:** `Authorization: Bearer <API_KEY>` — a fresh key will be sent separately.
- **Docs:** https://docs.signa.so/guides/trademarks
- This is fully isolated work — no access to any internal systems is needed. Everything below
  runs against Signa's public API only.

---

## Scope — Investigate and Document Each of These

### 1. Single-record fetch — `GET /v1/trademarks/{id}`
Pull 3–4 IDs from search results, then fetch each one directly. Answer:
- Which fields present in a *search* record disappear on a single fetch? (Specifically check
  `relevance_score`, `match_explanation`, `highlights`, `search_meta`.)
- Is `classifications[].goods_services_text` returned in **full** here, vs. truncated in search?
  Confirm using the `goods_services_text_truncated` flag.
- Any fields that appear *only* on the single-record response?

### 2. Media — `primary_image_url` / `/media/{id}`
Fetch a `primary_image_url` from a record where `has_media: true`. Document:
- Does it require the same Bearer auth?
- What `Content-Type` / image format comes back?
- Any noticeable size or rate limits?

### 3. Pagination
Take one query with `has_more: true`, follow `pagination.cursor` through **at least 3 pages**.
Confirm:
- Do records repeat or drop across pages?
- Does `has_more` eventually turn false?
- Roughly how many results per page / total for a common term?

### 4. Filtering & Query Behavior
(This fixes the "all active" gap from Task 1.)
From the docs, find and test any supported query params beyond `q` and `offices` — e.g.
status/stage filters, Nice class, owner, date ranges, and the `aggregations` param. Deliberately
try to surface **inactive / abandoned / refused / opposed** marks. Document which filters exist,
which work, and give one example call + result summary for each.

### 5. Error & Edge Behavior
Briefly document what the API returns for:
- a bad / expired key,
- a malformed ID,
- a query with zero results.

(Capture status codes + response body shape for each.)

---

## Deliverables

1. **A short report** (same style as the last one) covering the 5 areas above, using `sig_xxx`
   placeholders for the key.

2. **A standalone Python script** (`signa_client.py`) with four functions — `search()`,
   `get(id)`, `get_media(url)`, `paginate(query)` — plus a `main()` that demonstrates each.
   The API key must be read from an environment variable, **not hardcoded**.

3. **A proposed "normalized record" schema (your own design):** a flat list of the fields you
   would keep if designing a clean internal representation of a trademark from this data. For
   each field, note:
   - the source Signa field(s),
   - the type,
   - how you would handle the known quirks — e.g. `renewal_due_date` falling back to
     `expiry_date`, Madrid records using `ir_number` instead of `registration_number`, and PRV's
     `1900-01-01` placeholder → `null`.

   This is a design proposal for us to react to, not a match to anything existing.

---

## Out of Scope
Anything requiring internal systems. Keep it strictly to the public Signa API.
