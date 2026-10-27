# GATE B — Preprocessing / Features Verification Report

**Status: STOPPED FOR USER ACKNOWLEDGMENT** (Master §5). Date: 2026-10-15.
No model has been trained yet — Gate B only builds analysis tables.
Article type context: **Research** (user decision recorded in `00_GATE0…md` §1/§3/§5).

## 1. Policies declared BEFORE training (pre-registered, Rule 3)

- **P1 — missing-abstract:** reconstruct abstract from OpenAlex inverted index;
  if absent or <5 tokens → fall back to *title + author keywords*, flagged
  `text_source='title_keywords'`. Both variants retained for a later
  sensitivity check (abstract-only vs. with-fallback). OpenAlex `topics` are
  stored as **metadata only**, never model text (would be circular).
- **P2 — citation edges:** only edges whose cited ID is inside the 15-journal
  corpus are written; external refs are counted, not modeled. Differential
  reference coverage between journals stays visible in stats (Gate A caveat 2).
- **P3 — temporal:** 2026 is partial (harvest 2026-10-15) → flagged in stats;
  any rate-normalized analysis must exclude or separately handle 2026.

## 2. What ran & output verification (Rule 1 — counts from actual runs)

`scripts/build_tables.py` (exit 0, empty stderr):
- Pass 1: corpus IDs indexed **14,333**; duplicate-ID check passed; per-journal
  line counts == manifest counts for all 15 journals.
- Pass 2: wrote tables; then aggregates recomputed from the edge file.

Independent re-counts after the run:
| Output | Lines (incl. header) | Expected |
|---|---|---|
| `data/processed/works.csv` | 14,334 | 14,333 rows + header ✓ |
| `data/processed/citation_edges_internal.csv` | 50,966 | 50,965 + header ✓ |
| `journal_matrix.csv`, `discipline_matrix.csv` | 16×16, 9×9 incl. headers | built from same edge file ✓ |
| `gateb_stats.json` | written | contains policies + all counts ✓ |

## 3. Data facts (computed, not estimated)

- **Text coverage:** abstract = **13,023** (90.9%), title+keywords fallback =
  **1,310** (9.1%). Worst journal: RSE 207/578 abstracts (371 fallback);
  best: SSE 73/73. DISER: 167/177.
- **References:** total emitted by corpus = **563,289**; internal (cited work in
  corpus) = **50,965 (9.05%)** → the citation network models exchange *within
  the 15-journal system*; the other 90.95% cite outside it (counted, out of
  scope by design P2 — disclosed as scope, not silence).
- **Years:** 2019:1604 · 2020:1969 · 2021:1713 · 2022:1711 · 2023:1677 ·
  2024:1934 · 2025:1933 · **2026:1792 (partial, to Oct 15)**.
- **Discipline×discipline edge counts (descriptive only — interpretation is
  deferred to results after Gates C/D):** e.g., chemistry→chemistry 26,827;
  general→general 7,302; physics→physics 5,512; bridge(DISER)→general 294 vs
  bridge→bridge 87; biology→general 270 vs biology→biology 296. Full matrices:
  `discipline_matrix.csv`, `journal_matrix.csv`.

## 4. Limitations carried forward (not smoothed over)

1. **Differential reference coverage** (Gate A) → a journal with sparse ref
   deposits can look artificially isolated; any "silence between disciplines"
   claim needs the per-journal coverage table alongside it.
2. **RSE abstract sparsity** (64% fallback) → topic-model sensitivity run
   (abstract-only) is required before conclusions that involve RSE.
3. **JCE = 35% of corpus** → normalization/weighting decision must be made and
   declared at Gate C **before results are seen**.
4. **9.05% internal refs** → findings characterize intra-system exchange only.
5. 2026 partial year (P3).

## 5. Next phase (on acknowledgment): GATE C — SCOPE DECLARATION + TRAINING

Plan: (1) declare the analysis scope up front — models, settings, seed,
normalization choice for JCE skew, sensitivity runs (P1 fallback), and what is
being cut if anything, per Master §5/§6; (2) run topic modeling on `works.csv`
text + network analysis on the edge file (multi-seed where stochastic, per
Rule 5); (3) Gate C report = what was ACTUALLY trained/run with wall-clock and
logs. **Nothing beyond this report proceeds without your acknowledgment.**
