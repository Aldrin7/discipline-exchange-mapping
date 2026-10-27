# 04 — GATE C Run Report (topic model + network analysis)

**Status:** run complete; outputs verified. **Acknowledgment required before any Gate E drafting.**

---

## 1. Scope applied

Frozen in `project/03_GATE_C_scope_declaration.md` (S1–S10), env-driven:

| Constraint | Value |
|---|---|
| Packages | numpy / fastembed / onnxruntime only — no new installs |
| Embedding model | BAAI/bge-small-en-v1.5 (384-dim, first in fallback chain) |
| PCA | 384 → 50 (centered SVD, rows L2-normalized) |
| Clustering | KMeans++ (Lloyd, deterministic given seed) |
| Primary K | 20, seeds {1, 2, 3} |
| Sensitivity | abstract-only (drop non-abstract sources) vs full, seed 1, ARI threshold 0.60 |
| K-sweep | k=15 and k=25, seed 1 |
| JCE normalization | macro-mono (S7 fixed) |
| Network metrics | S6 deterministic (self-cite share, same/cross-tag share, entropy norm) |

Host: 24 GB RAM, **no pagefile** (commit limit = RAM). Memory-tight embedding params: `batch_size=8`, `threads=4`, sequential in-process (`parallel=None`, fastembed default).

---

## 2. Exact command

```powershell
# venv python, run from project/scripts (PROJ = parents[1] of this file, PROC = data/processed)
C:\Users\aldri\.cline\data\workspaces\chat\agent-workbench\.venv\Scripts\python.exe -u "d:\Research\On-Progress\Disciplinary and Interdisciplinary Science Education Research\project\scripts\run_gatec.py"
```

Stdout/stderr redirected to `project/scripts/run_gatec.log` / `run_gatec.err` during the supervised run.

---

## 3. Wall-clock per stage

| Stage | Wall time | Notes |
|---|---|---|
| Load works.csv | fast (startup) | works = 14,333 |
| Embedding (bge-small-en-v1.5) | ~3,262 s (~54.4 min) | batch=8, threads=4, sequential in-process; ~250 docs/s sustained |
| PCA 384→50 + L2-normalize | <1 s | numpy SVD |
| KMeans k=20 seed1 | 1.04 s | 13 iters, inertia 15,740.9→8,894.8 |
| KMeans k=20 seed2 | 1.55 s | 26 iters, inertia 16,063.8→8,922.6 |
| KMeans k=20 seed3 | 1.89 s | 31 iters, inertia 15,384.2→8,956.0 |
| KMeans k=15 seed1 | 0.94 s | inertia final 9,292.5 |
| KMeans k=25 seed1 | 2.88 s | inertia final 8,544.2 |
| Sensitivity (abstract-only) | included above | n=13,023 docs |
| Topics + network metrics | <1 s | per-journal metrics |
| **TOTAL wall** | **3,284.7 s (~54.7 min)** | from `gatec_runs.json` |

Embedding dominated runtime (~99%). KMeans/topic/network stages were each under 3 s.

---

## 4. Outputs (all in `project/data/processed/`)

| File | Size | Content |
|---|---|---|
| `gatec_assignments.csv` | ~1.09 MB | id, year, journal, tag, source, cluster_seed1/2/3 (k=20), cluster_k15_s1, cluster_k25_s1 |
| `gatec_topics.json` | ~15.8 KB | top-10 terms/score per cluster 0–19 + cluster sizes (seed1) |
| `gatec_runs.json` | ~37.3 KB | full run record: model, k, seeds, pca_dim, per-run wall/inertia/sizes, sensitivity, k-sweep, inertia curves, per-journal network metrics, cross-tag shares |
| `embeddings.npy` | cache | (14,333 × 384) float32 embedding matrix |

---

## 5. Verification results

**Record counts:**
- Works loaded: **14,333** (matches Gate B)
- `gatec_assignments.csv` data rows: **14,333** ✓
- K=20 cluster sizes sum to 14,333 for **all three seeds** (seed1=14,333, seed2=14,333, seed3=14,333; 20 clusters each) ✓ — every work assigned, no orphans

**Seed-pair ARI (k=20, from assignments):**
| Pair | ARI |
|---|---|
| seed1 vs seed2 | 0.4966 |
| seed1 vs seed3 | 0.5189 |
| seed2 vs seed3 | 0.5062 |

Interpretation: moderate (~0.50) agreement across seeds — cluster assignments are reproducible in broad structure but not identical; expected for Lloyd KMeans with different initial centroids on 384→50-D embeddings.

**Sensitivity S8 (abstract-only vs full, seed 1):**
- n_docs = 13,023 (abstract-bearing subset)
- ARI vs full seed1 = **0.57**
- threshold = 0.60 → **verdict: CONCERN** (ARI < 0.60)

This matches the pre-declared open item: RSE abstract-sensitivity threshold ARI<0.60. Declared as a deviation to be acknowledged, not a blocker.

**Network metrics S6 (micro/macro over 15 journals):**
- cross-tag share micro = **0.136**
- cross-tag share macro = **0.265**
- Journal order: diser, science_education, jrst, ijse, rse, sse, jbe, cerp, jce, prper, physed, jge, jee, ejee, ijsted

Per-journal detail (out_total, in_total, self_cite_share, same_tag_share, cross_tag_share, entropy_norm_15, entropy_norm_8tag) is recorded in `gatec_runs.json` under `inertia_curves.<journal>`. Notable: JCE same_tag_share=0.952 (macro-mono normalized, S7), cross_tag_share=0.048.

---

## 6. Deviations (require acknowledgment before drafting)

1. **Embedding label mismatch.** `gatec_runs.json` `model_used` reads `"BAAI/bge-small-en-v1.5 (3261.9s, batch=16, parallel=1, threads=4)"`, but the edited script actually ran `batch_size=8`, `parallel=None` (sequential in-process), `threads=4`. The label string is hardcoded/stale (run_gatec.py:99); runtime params were the memory-tight ones. Results unaffected — run completed cleanly with no deadlock/OOM.

2. **Sensitivity ARI below threshold.** ARI = 0.57 < 0.60 → CONCERN (S8). Carried forward as open item (RSE abstract-sensitivity).

3. **Seed-pair ARI ~0.50.** Moderate, not high, cross-seed stability. Noted for interpretation of topic robustness.

4. **2026 partial-year exclusion.** Per Gate B open items, 2026 is a partial year and must be excluded from any rate claims (not applied in this run's counts — all years included as loaded).

---

## 7. Next step (blocked on acknowledgment)

Per the declared protocol, Gate C report must be **acknowledged before any Gate E drafting** (measure 2–3 more DISER Research reviews for word/reference norms; fetch ethics-and-disclosures wording; extend novelty search). No further drafting will proceed until this report is acknowledged.

---

**Run ID:** gatec, PID 14268, completed `2026-10-16`, wall 3,284.7 s, exit clean.
