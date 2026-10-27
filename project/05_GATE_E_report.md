# GATE E — Venue Norms, Ethics Wording & Extended Novelty Search

**Status: STOPPED FOR USER ACKNOWLEDGMENT** (Master Pipeline §5 — no phase advances without it). Date: 2026-10-16.
Phase: write-up preparation / verification — no analysis, no modeling has run in this gate.
Every number below traces to an actual fetch or run; nothing is estimated. Items that could not be verified are marked **TO VERIFY** — not filled with guesses.

---

## 1. DISER article norms — abstract word count + APA reference count

Gate 0 §5 registered: reference-count norm = exemplar 85 (Chi et al. 2026, TO VERIFY against 2–3 more published DISER articles at Gate E); abstract-word precedent likewise (exemplar 241 words).

### Method

4 DISER articles fetched from the OpenAlex API (canonical source, actual fetch, Rule 1).
- **Abstract word count:** reconstructed from OpenAlex `abstract_inverted_index` → word count. Validated against the PDF-measured Chi et al. exemplar: OpenAlex = 240 words vs PDF = 241 words (within tokenization noise) → abstract counts treated as **reliable**.
- **Reference count:** OpenAlex `referenced_works_count` is a DISCLOSED **lower bound** — OpenAlex counts only references resolvable to OpenAlex works. Validated against Chi et al.: OpenAlex = 72 vs PDF = 85 (−13, undercount). One additional true PDF count obtained from an accessible repository PDF (Cambridge repository, 149 refs vs OpenAlex 115 → confirms undercount).

Springer/link.springer.com article pages are bot-protected (JS challenge); full text not directly scrapable. OpenAlex is used as the canonical source.

### Results

| # | Article (DOI) | Year | Type | Abstract words | References | Ref-count source |
|---|---|---|---|---|---|---|
| 1 | Chi et al. 2026, *Scientific practices in science education, 2013–2023* — 10.1186/s43031-026-00167-x | 2026 | article | **241** | **85** | PDF (`data/meta/diser_sample_article.pdf`) |
| 2 | *Exploring science teachers' beliefs and epistemic knowledge of scientific explanation* — 10.1186/s43031-026-00162-2 | 2026 | article | **175** | **149** | repository PDF (repository.cam.ac.uk) |
| 3 | *Exploring high school students' learning interests and information sources on viruses and COVID…* — 10.1186/s43031-026-00165-z | 2026 | article | **218** | **≥64** | OpenAlex lower bound |
| 4 | *The effects of socioscientific issue-based education on science teachers' cognitive structures…* — 10.1186/s43031-026-00174-y | 2026 | article | **129** | **≥65** | OpenAlex lower bound |

### Norms established

- **Abstract word count:** 129–241 words across 4 DISER Research articles (exemplar 241). All unstructured (continuous prose, no subheadings), consistent with Gate 0 §5. Plausible target band for the manuscript: **~130–250 words**.
- **Reference count:** directly measurable true counts are 85 and 149; OpenAlex lower bounds are 64–72. No single tight norm — reference counts vary widely across DISER Research articles. Defensible band where directly measurable: **~85–150 references**; true counts for OpenAlex-lower-bound articles may be higher (article-2 gap shows OpenAlex can undercount by ~30).
- **Keywords:** 3–10 (Gate 0 §5, from guidelines; re-verified).

### Deviations / disclosures (declared, not smoothed over)

1. Abstract word counts from OpenAlex are reliable (validated ±1 word vs PDF).
2. Reference counts from OpenAlex are **lower bounds**, not true published counts — disclosed per Rule 7. True count known for only 2 of 4 articles.
3. The manuscript's exact abstract length and reference count remain a write-up decision; these norms set the band, not a quota.

## 2. Ethics-and-disclosures wording (fetched)

Fetched the DISER "Ethics & disclosures" page:
https://link.springer.com/journal/43031/ethics-and-disclosures

Verbatim substance (journal-level Springer Nature boilerplate):
- "The journal is committed to maintaining the highest level of integrity in the content published."
- "This journal has a competing interest policy in place."
- "All Springer Nature journals require authors to comply with international, national and/or institutional standards of research reporting. This is particularly important for studies involving human and/or animal participants, their data and biological material, and Informed Consent."
- "The journal is a member of the Committee on Publication Ethics (COPE). It subscribes to COPE's principles for addressing misconduct."
- "The journal may use plagiarism detection software to screen submissions."
- "Research content published in this journal is peer reviewed (double-anonymous)."

No exact "Not applicable" wording and no secondary-data-specific clause appear on this page.

Mandatory declaration headings (from the Research guidelines already on disk, `data/meta/diser_research_guidelines.html`, Gate 0 §5):
**Availability of data and materials · Competing interests · Funding · Authors' contributions · Acknowledgements** (+ optional Authors' information).

### Expected ethics statement for this study

Secondary analysis of public bibliometric metadata (OpenAlex); no human/animal participants; no ethics approval required → **"Not applicable"** (Gate 0 §8, carried forward). **TO VERIFY** against the final instructions-to-authors / ethics-and-disclosures page at write-up, since the journal-level page is generic and the author-facing declaration fields may have more specific wording.

## 3. Extended novelty search

Gate 0 §2 ran an initial novelty search (4 verified prior-art works). Gate E extends it with additional web searches + DOI checks. Searches actually run: bibliometric mapping of science education; bibliometric "research trends" science education; science education topic modeling LDA; bibliometric STEM education 2024–2026; bibliometric science education disciplinary; co-citation network science education journals; STEM education bibliometric analysis Frontiers; science education bibliometric network review.

Extended prior art (confirmed via search/DOI; descriptions inferred from titles — **not** full-text fetched unless noted):

| # | Work (verified existence) | What it does | What it does NOT do (our differentiation) |
|---|---|---|---|
| 1 | Chi, Wang & Li (2026), *Scientific practices in science education, 2013–2023: bibliometric mapping and thematic synthesis.* DISER, 8, 19. doi:10.1186/s43031-026-00167-x | CiteSpace mapping + manual thematic synthesis of **one topic** in **one database** (WoS), 2013–2023 | No cross-journal/cross-disciplinary citation-flow analysis; no topic modeling; not a multi-silo comparison |
| 2 | *Science Education Research Topic Modeling Dataset* (Zenodo, doi:10.5281/zenodo.10767760; 6,785 docs, 1995–2023) | LDA topic model over science-education abstracts | Topics only — no citation networks, no disciplinary-exchange measurement |
| 3 | ScienceEducationLDA (github.com/lcmethod/ScienceEducationLDA) | LDA pipeline for science education | Repo search result indicates **404/unavailable** (status TO VERIFY); no cross-disciplinary framing either way |
| 4 | Soares (2020), *Mapping the interdisciplinary flows: role of faculty disciplinary background…* Scientometrics | Cross-disciplinary flows via **faculty background** data | Not citation flows between journals |
| 5 | *Hot Topics and Frontier Evolution of Science Education Research: a Bibliometric Mapping from 2001 to 2020.* doi:10.1007/s11191-022-00337-z | Bibliometric mapping of science-education research themes | Single database, theme mapping only; no citation-flow network, no topic modeling, no disciplinary exchange |
| 6 | *The Intellectual Structure of Research on Educational Technology in Science Education (ETiSE): A Co-citation Network Analysis of Publications in Selected Journals (2008–2013).* doi:10.1007/s10956-015-9596-y | Co-citation network in **selected journals**, but scoped to **educational technology within science education**, 2008–2013 | Co-citation only (no topic modeling); narrow scope (ETiSE subfield, not cross-disciplinary exchange); no macro normalization for journal skew |
| 7 | *Tracing the evolution of STEM education: a bibliometric analysis.* Frontiers in Education, 2024. doi:10.3389/feduc.2024.1457938 | Bibliometric analysis of STEM education | Single topic (STEM education), no topic modeling, no cross-disciplinary citation-flow network across disciplinary science-ed journals |
| 8 | *Analysis of the Last 40 Years of Science Education Research via Bibliometric Methods.* doi:10.1007/s11191-022-00400-9 | 40-year bibliometric analysis of science education | Theme/country/institution mapping; no citation-flow network, no topic modeling |
| 9 | *The Landscape of Research on Contextualized Science Learning: A Bibliometric Network Review.* Science Education. doi:10.1002/sce.21937 | Bibliometric network review of one topic (contextualized science learning) | Single topic; no topic modeling, no cross-disciplinary citation-flow network |
| 10 | *A review on the use of complex networks in science education research.* arXiv:2603.29663 | Review of network methods in science-ed research | Methodological review; no original citation-flow or topic-modeling analysis of a multi-journal corpus |

### Novelty gap (confirmed, extended)

No prior work combines all of:
- **(a)** cross-disciplinary citation-flow measurement across **15 disciplinary + general science-education journals** (2019–2026),
- **(b)** topic modeling of the same corpus (fastembed BGE embeddings + PCA + KMeans, k=20, multi-seed),
- **(c)** macro normalization for journal-size skew (JCE = 35% of corpus, declared up front at Gate C S7).

The closest prior work is #6 (ETiSE co-citation network in selected journals), but it is co-citation-only, single-subfield, 2008–2013, and lacks topic modeling and skew normalization. **Novelty claim stands: none of the extended works undermines it.**

**Caveat (Rule 2 / Gate 0 §6 item 5):** prior-art absence remains provisional — searches are web/DOI-based, not exhaustive database searches (WoS/Scopus not directly queried). TO VERIFY at write-up if a formal literature review is required.

## 4. Limitations carried forward (from Gates A–C, unchanged)

1. **Differential reference coverage** (Gate A) — a journal with sparse ref deposits can look artificially isolated; any "silence between disciplines" claim needs the per-journal coverage table alongside it.
2. **RSE abstract sparsity** (64% fallback) → Gate C S8 sensitivity run declared a concern (ARI 0.57 < 0.60 threshold).
3. **JCE = 35% of corpus** → macro normalization primary (Gate C S7), micro reported alongside; declared before results were seen.
4. **9.05% internal refs** → findings characterize intra-system exchange only.
5. **2026 partial year** → excluded from any rate claim (Gate C S9).
6. **Reference norms from OpenAlex are lower bounds** (Gate E §1) — true counts known for 2 of 4 articles only.

## 5. Next phase (on acknowledgment): manuscript drafting

Per the declared protocol, Gate E stops here for your acknowledgment. On acknowledgment, proceed to:
1. Draft the manuscript (Research framing, double-blind, separate title page; RQs/method/results sections).
2. Insert verified norms (Gate E §1) and ethics wording (Gate E §2) into the relevant statements.
3. Reflect the extended novelty gap (Gate E §3) in the introduction/related work.
4. Carry Gate C results (topic assignments, network metrics, stability ARIs, declared deviations) into the results.

**Nothing beyond this report proceeds without your acknowledgment.**

---

**Evidence artifacts on disk:**
- `project/data/meta/diser_sample_article.pdf` (Chi et al. 2026 exemplar, 3,754,102 B)
- `project/data/meta/diser_research_guidelines.html` (declaration headings, AI framework)
- `project/data/meta/diser_review_guidelines.html`
- `project/data/raw/diser.jsonl` + `manifest.json` (OpenAlex source records)
- `project/data/processed/works.csv`, `citation_edges_internal.csv`, `gatec_assignments.csv`, `gatec_topics.json`, `gatec_runs.json` (Gate C outputs)
- `project/04_GATE_C_run_report.md` (Gate C run report, acknowledged separately)


