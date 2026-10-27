# GATE C — Scope Declaration (FROZEN BEFORE ANY TRAINING RUN)

Date: 2026-10-15. Written **before** any model ran — this is the up-front
analysis-scope declaration required by Master Pipeline §5a/§6.
Any deviation observed later must be recorded with a reason in
`04_GATE_C_run_report.md` (never silently).

## Environment-driven constraint (verified, not assumed)

Availability check in the workbench venv: numpy ✓ fastembed ✓ onnxruntime ✓ —
sklearn ✗ scipy ✗ pandas ✗ networkx ✗ umap ✗ hdbscan ✗ bertopic ✗ gensim ✗.
**Decision: no new packages are installed** (scope honesty over tool
fashion); dimensionality reduction, clustering, ARI, and network metrics are
implemented directly in numpy/python with the formulas stated below.

## Declared scope S1–S10

- **S1 Corpus/text:** all 14,333 rows of `works.csv`, P1 text (abstract if
  ≥5 tokens else title+keywords). No document dropped.
- **S2 Embeddings:** fastembed `BAAI/bge-small-en-v1.5` (384-d, ONNX/CPU),
  raw text, no instruction prefixes, truncation at model max length (512
  subword tokens). Declared fallback order if unavailable:
  `sentence-transformers/all-MiniLM-L6-v2`, then
  `snowflake/snowflake-arctic-embed-xs`; the actually-used model is recorded.
- **S3 Reduction:** PCA (numpy SVD) 384→50 dims on centered data; rows
  L2-normalized afterwards. No UMAP (absent; declared substitute).
- **S4 Clustering:** numpy KMeans, **k=20 primary**, seeds **{1,2,3}**,
  k-means++ init, Lloyd, max_iter=300, tol=1e-4 (relative inertia),
  empty-cluster reseeding to farthest point. **Secondary k-sweep {15,25}** at
  seed 1, compared to k=20 by ARI. Inertia-vs-iteration curve = the training
  curve analogue. BERTopic/HDBSCAN-class density clustering is OUT (absent) —
  declared limitation: KMeans imposes spherical clusters of roughly equal
  effort; no outlier cluster exists.
- **S5 Topic naming:** per-cluster top-10 terms by
  `score(t,c) = (n_t,c / total_tokens_c) × ln(N_docs / df_t)`, lowercase
  alpha tokens len≥3, static English stoplist, corpus-wide min_df=20.
   Labels are extractive (terms ranked by within-cluster frequency × log corpus frequency).
- **S6 Citation-network analysis:** deterministic (no randomness → no seeds
  needed): journal×journal 15×15 matrix → per-journal row shares (self-cite
  diagonal, same-tag, cross-tag), discipline-aggregated out-distributions,
  normalized Shannon entropy (÷ln 8), in/out degrees.
- **S7 Skew normalization (JCE=35%):** PRIMARY = macro-average (each of the
  15 journals weighted equally) for any cross-journal/cross-discipline claim;
  micro (raw pooled counts) reported alongside, never alone.
- **S8 Sensitivity (P1 fallback):** for the 13,023 abstract-covered docs,
  reuse their identical embeddings (deterministic), refit PCA+kmeans
  (k=20, seed 1) on that subset; agreement with the full-model seed-1
  assignment on the same docs via ARI. Threshold for concern: ARI < 0.60.
- **S9 Cuts declared up front (what this study does NOT do):** no temporal
  trend modeling (2019–2026 counts stay descriptive; 2026 partial excluded
  from any rate claim), no citation-prediction/ML forecasting, no SHAP-style
  attribution, no modeling of the 90.95% external references (P2),
  no inference between topic similarity and causation.
- **S10 Compute/accounting:** CPU only; wall-clock logged per stage; all
  reported numbers computed from output files (Rule 1), seeds given (Rule 5).

Gate rule: after the run, `04_GATE_C_run_report.md` must be presented and
**acknowledged before any manuscript/drafting work begins** (Master §7).
