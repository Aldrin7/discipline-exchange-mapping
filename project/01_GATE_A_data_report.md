# GATE A — DATA Verification Report

**Status: STOPPED FOR USER ACKNOWLEDGMENT** (Master §5). Date: 2026-10-15.
Phase: data acquisition only — no analysis, no modeling has run.

## 1. What ran (commands → outputs)

| Step | Script / command | Result |
|---|---|---|
| Source verification by ISSN | `scripts/verify_sources.py` | Caught **3 wrong ISSNs (404)** and **4 ISSNs resolving to wrong journals** (e.g., "Journal of Biological Education" ISSN I recalled → *Journal of Clinical Psychology*). All recalled ISSNs discarded |
| Source resolution by name | `scripts/resolve_by_name.py` | All 7 doubtful titles resolved with host-organization confirmation (T&F, RSC, ACS, Wiley, Springer) — final ISSN list locked |
| Corpus harvest | `scripts/harvest_corpus.py` | **14,333 works, 15 journals, 2019-01-01→2026-12-31, 92 API calls, $0.0079** — raw JSONL per journal + `data/raw/manifest.json` (incl. per-year counts, source IDs, filters) |
| Gate A schema verification | `scripts/verify_corpus.py` | **PASSED**: line counts = manifest counts for all 15 journals; required fields present in **all 14,333 rows**; unique work IDs = row counts; **0 cross-journal duplicate DOIs**; year range 2019–2026 everywhere |

## 2. Corpus (real counts from the run, not estimates)

| Journal (tag) | Works | Journal (tag) | Works |
|---|---|---|---|
| DISER / bridge (bridge) | 177 | Physics Education (physics) | 1,898 |
| Science Education (general) | 881 | PRPER (physics) | 916 |
| JRST (general) | 657 | J. Geoscience Education (geoscience) | 324 |
| IJSE (general) | 1,106 | J. Engineering Education (engineering) | 486 |
| Research in Sci. Educ. (general) | 578 | European J. Eng. Educ. (engineering) | 573 |
| Studies in Sci. Educ. (general) | 73 | Int. J. STEM Education (interdisc.) | 496 |
| J. Biological Education (biology) | 469 | **TOTAL** | **14,333** |
| CERP (chemistry) | 655 | J. Chem. Education (chemistry) | 5,044 |

Sample rows printed by the verifier are real records with publisher DOI prefixes
matching each journal (e.g., DISER `10.1186/s43031-…`, JCE `10.1021/acs.jchemed.…`,
PRPER `10.1103/physrevphyseducres.…`).

## 3. Provenance & incidents (declared per Rules 3/6/7)

- **Source:** OpenAlex REST API (`api.openalex.org`), filters
  `primary_location.source.id:<verified>, from_publication_date:2019-01-01,
  to_publication_date:2026-12-31`, cursor-paginated at 200/page, field `select`
  recorded in the script. Raw responses saved unmodified as JSONL.
- **Keyless throttling incident (diagnosed, not narrated away):** keyless calls
  returned intermittent multi-minute **HTTP 401 windows** (verified: the identical
  URL returned 200 seconds later via curl/python singles). Root cause: shared
  per-IP free budget. **Resolution:** user provided an OpenAlex API key; saved to
  user env var `OPENALEX_API_KEY` (reused by Cline/Kilo) and `project/.env`.
  Harvest rerun completed cleanly on first keyed pass (no retries).
- No dataset substitution: OpenAlex is the canonical source for this design;
  no mirror was used.

## 4. Known data limitations (carried into Gate B — disclosed, not hidden)

1. **Abstract coverage varies by journal:** DISER 94.4%, IJSE 98.8%, JCE 97.7%,
   but *Research in Science Education* **35.8%**, Science Education 65.7%,
   JRST 74.7%, JEE 77.4%. Topic modeling must state its missing-abstract policy
   (title/keyword fallback vs. exclusion) as an explicit Gate B/C decision.
2. **Reference-list coverage varies:** Science Education 61.1%, JEE 78.4%,
   CERP 82.9% vs. IJSED 99.6%, EJEE 98.6%. Cross-journal citation edges will
   have differential missingness → must be disclosed as a limitation of any
   "silence between disciplines" finding (a discipline with low reference
   deposit coverage can look artificially isolated).
3. **Journal-size skew:** JCE alone = 5,044/14,333 (35%). Any aggregate topic or
   citation statistic must define its normalization (per-journal weighting,
   stratified sampling, or stratified reporting) *before* results are seen —
   decided at Gate C scope declaration.
4. OpenAlex `reference` records reflect publisher deposits; refs are OpenAlex
   work IDs — citations to works *outside* the 15-journal corpus exist and are
   expected (they will be handled in network construction, Gate B/C).

## 5. Artifacts on disk

- `project/data/raw/<slug>.jsonl` × 15 (raw, unmodified API records)
- `project/data/raw/manifest.json` (filters, source IDs, per-journal + per-year
  counts, `api_calls: 92`, `api_cost_usd: 0.0079`)
- `project/data/raw/progress.json` (resume state)
- `project/.env` + user env var `OPENALEX_API_KEY` (credential handling)
- logs: `project/scripts/harvest_corpus.log`, `verify_sources.log`,
  `resolve_by_name.log`

## 6. Next phase (on acknowledgment): GATE B — PREPROCESSING / FEATURES

Plan: build the analysis tables from raw JSONL — (a) reconstruct abstracts from
inverted indexes with coverage stats per journal; (b) declare and implement the
missing-abstract policy; (c) construct the inter-journal citation edge list
(who-cites-whom across the 15 journals, within vs. cross-discipline);
(d) split/leakage analogue for this design = temporal handling decisions
(2019–2026 window, 2026 partial year flagged); (e) report exact row counts at
every transformation. Gate B report stops for acknowledgment before any
topic-model training (Gate C).
