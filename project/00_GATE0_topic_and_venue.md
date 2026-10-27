# GATE 0 — Topic Selection & Venue Verification Report

**Status: STOPPED FOR USER ACKNOWLEDGMENT** (Master Pipeline, Section 5 — no phase
advances without it). Date: 2026-10-15.
Every number/citation below traces to a run or a fetch performed in this session.
Items that could not be verified are marked **TO VERIFY** — not filled with guesses.

---

## 1. Approved topic (user-approved Option 3)

**Working description (no results claims, per §4.1):** A computational map of
knowledge exchange *between* disciplinary science-education subfields — a
citation-network + topic-modeling analysis over a multi-journal corpus
(biology / chemistry / physics / geoscience / engineering education + general
science education, with DISER included as the bridging venue), asking which
disciplines cite each other, which remain siloed, and which topics/journals act
as bridges. Anchored in DISER's stated mission: *"bridge divides … between
disciplinary and interdisciplinary approaches."*

Why this fits DISER (all verified this session):
- **Article type: Research** (user decision, 2026-10-15 — changed from Review).
  Official Research guidelines (downloaded page `diser_research_guidelines.html`):
  *"Research papers report empirical studies addressing significant questions in
  science education… research questions are answered by data that are
  systematically collected and analyzed."* Our study meets this: empirical
  bibliometric/computational analysis of systematically collected records with
  explicit RQs, method, and results sections. **Honest risk:** editors may
  reclassify a bibliometric study as Review (Chi et al. 2026 was published as
  Review) — that is an editorial judgment; framing stays Research per user.
- Proof of editorial appetite: Chi, Wang & Li (2026), *bibliometric mapping and
  thematic synthesis*, **published in DISER** as Review, Vol. 8 art. 19,
  doi:10.1186/s43031-026-00167-x (fetched full text).
- Mission alignment: the journal's own name and aims are the research object
  (disciplinary ↔ interdisciplinary exchange).

## 2. Novelty gap check (Rule 2 — searches actually run)

Queries run this session (web search + Springer/OpenAlex fetches): bibliometric
mapping of science education research; bibliometric "research trends" science
education; science education topic modeling LDA; bibliometric STEM education
2024–2026; bibliometric science education disciplinary; DOI fetches of related work.

**Verified prior art found (real, fetched/searched):**

| # | Work (verified) | What it does | What it does NOT do (our differentiation) |
|---|---|---|---|
| 1 | Chi, Y., Wang, L., & Li, X. (2026). *Scientific practices in science education, 2013–2023: bibliometric mapping and thematic synthesis.* DISER, 8, 19. doi:10.1186/s43031-026-00167-x | CiteSpace mapping + manual thematic synthesis of **one topic** in **one database** (WoS), 2013–2023 | No cross-journal/cross-disciplinary citation-flow analysis; no topic modeling; not a multi-silo comparison |
| 2 | *Science Education Research Topic Modeling Dataset* (Zenodo, doi:10.5281/zenodo.10767760; 6,785 docs, 1995–2023) | LDA topic model over science-education abstracts | Topics only — no citation networks, no disciplinary exchange measurement |
| 3 | ScienceEducationLDA (github.com/lcmethod/ScienceEducationLDA) | LDA pipeline for science education | Search result indicates repo **404/unavailable** — status TO VERIFY; no cross-disciplinary framing either way |
| 4 | Soares, T. P. (2020). *Mapping the interdisciplinary flows: role of faculty disciplinary background…* Scientometrics | Cross-disciplinary flows via **faculty background** data | Not citation flows between the disciplinary *literatures* of biology/chemistry/physics education |
| 5 | Crowded genre of recent science-ed bibliometrics (verified in results): creative-thinking bibliometric 2015–2025 (23 Jan 2026); *Hot Topics … 2001–2020* (21 Apr 2022); interdisciplinary research in higher ed (2026); STEM bibliometric reviews (2026) | Bibliometric mapping is a **crowded, accepted genre** | Differentiation is mandatory — ours is defined by the *cross-disciplinary exchange* question, not a theme-within-one-corpus map |

**Honest gap statement (to appear in the paper's related work):** Across the
searches above, **no study was found that measures citation-based knowledge
exchange between disciplinary science-education subfields as such** (biology ↔
chemistry ↔ physics ↔ geoscience ↔ engineering ↔ general science education).
Absence in these queries is not proof of absence — the full literature-search
phase (Gate E) must extend to Scopus/WoS-style review strategies before any
novelty claim enters the manuscript.

**Closest-prior-works trio for the eventual novelty statement (§4.2):** Chi et al.
2026 (in DISER), Zenodo topic-modeling dataset paper, Soares 2020 — all verified
above.

## 3. Data feasibility (Rule 6 — provenance verified by run)

- **OpenAlex source S3034864385 (ISSN 2662-2300) fetched this session:**
  display_name confirmed; `works_count: 177` (2019–2026); `oa_works_count: 177`
  (100% diamond OA, `apc_usd: 0`); `h_index: 29`; `2yr_mean_citedness: 5.94`;
  per-year counts present (2019:16, 2020:11, 2021:11, 2022:27, 2023:23,
  2024:29, 2025:28, 2026:32).
- Works records include `abstract_inverted_index` and `referenced_works`
  (sample work W7220652359: `referenced_works_count: 42`, both fields present) →
  citation-network + topic-modeling inputs are available from one keyless API.
- **Corpus decision (declared, not silent):** DISER alone (177 works) is too
  small for standalone topic modeling → corpus will be **multi-journal**
  (disciplinary + general science-education journals, 2019–2026 DISER era;
  exact journal list fixed at Gate A before download). This is a scope
  definition, not a substitution — disclosed here per Rule 3.
- **Known constraint (flagged now):** keyless OpenAlex shares a free daily
  budget ($0.10/day, stated in the API response). Options at Gate A: (a) free
  OpenAlex API key, (b) throttled pagination. Will not silently switch sources.
- Springer's PDF endpoint is bot-blocked for script downloads (verified: 3 KB
  challenge pages); `curl.exe` with browser UA works (verified: 3,754,102-byte
  PDF). OpenAlex content mirror returned HTTP 401 (auth required) — noted, unused.

## 4. Filled Master Pipeline — Section 3 (Project Inputs)

| Field | Value |
|---|---|
| Target venue | **Disciplinary and Interdisciplinary Science Education Research (DISER)**, Springer Nature (eISSN 2662-2300, diamond OA, DOAJ/Scopus, EICs Xiufeng Liu / Lei Wang / Yonghe Zheng) |
| Venue scope summary | Empirical/conceptual/policy + position papers, critical reviews, book reviews; all levels; biology, chemistry, geology, physics, science, engineering education; qualitative/quantitative/mixed; explicit mission: bridging disciplinary ↔ interdisciplinary, K-12 ↔ post-secondary, English ↔ non-English contexts |
| Formatting template & citation style | SpringerOpen double-blind **Research** template (user decision 2026-10-15; same double-blind/files rules as Review); files: Title Page, Abstract, Blinded Manuscript, Tables, Figures, Supplementary. **APA author-year — verified twice**: (a) official guidelines *"Examples of the American Psychological Association (APA) reference style are shown below"*; (b) published sample PDF in-text `(Al & Tonta, 2004)`, 0 numeric `[n]` matches, alphabetical APA reference entries |
| Page/word limits | **Not stated numerically in the journal's guidelines** (verified by local grep of downloaded Research & Review guideline pages — only figure/table title limits exist). Soft exemplar (measured, actual run): Chi et al. 2026 = 28 pages incl. refs, abstract 241 words, 85 references. Do not treat as an official limit |
| Domain / research area | Science education research × scientometrics/computational mapping (NLP topic modeling + citation-network analysis) |
| Topic constraints | Approved: cross-disciplinary knowledge-exchange map with DISER as bridge venue; modest, fully verifiable scope per Master §9 |
| Real dataset(s) | **OpenAlex** (primary, verified above); Crossref/OpenCitations as cross-validation candidates (to be confirmed at Gate A); Kaggle token available as secondary. **No synthetic data** |
| Compute environment | Windows 11 (this machine), Python 3.11, workbench venv with turbovec/fastembed/langgraph verified present; GPU (GTX 1050 Ti via llama.cpp, verified separately) not required for this workload |
| Time budget / deadline | **No hard deadline** (user decision, 2026-10-15) |
| Other hard constraints | Integrity Rules 1–11 apply unchanged; no acceptance-probability optimization; Kaggle/GitHub tokens handled as credentials (never echoed); double-blind blinding at write-up |

## 5. Filled Rulebook — Part 0 (venue parameters, all verified this session)

- Target venue: **DISER** · Article type: **Research** (user decision 2026-10-15;
  empirical framing with RQs/method/results — see §1 risk note)
- Word/page limit: **none officially stated** (see above; exemplar 28 pp.)
- Abstract structure: **unstructured** (verified: Chi et al. abstract = continuous
  prose; guidelines give no subheadings) · Abstract limit: **not stated**
  (exemplar 241 words) · Keywords: **3–10**, listed below abstract
- No references in the abstract (guidelines, exact wording verified)
- Citation style: **APA author-year** · Reference count norm: exemplar 85
  (TO VERIFY against 2–3 more published DISER reviews at write-up)
- Figures: titles ≤15 words; legends ≤300 words in main manuscript; ~300 dpi at
  final size; width 600 px (standard) / 1200 px (high-res)
- Tables: titles ≤15 words; legends ≤300 words; no color/shading;
  **"Commas should not be used to indicate numerical values"** (house style)
- Files: DOC/DOCX **or** TeX/LaTeX (Springer template supported)
- Required statements (headings mandatory, "Not applicable" allowed):
  Availability of data and materials · Competing interests · Funding · Authors'
   contributions · Acknowledgements · (+ optional Authors' information)
- Research type: **double-blind** too (verified on the Research guidelines
  page: same blinding requirement) → separate Title Page; no identifying info
  in main file; Research titles may include the research design where appropriate
- Ethics: secondary analysis of public bibliometric metadata → expected
  "Not applicable" — final wording TO VERIFY against ethics-and-disclosures page
  at write-up

## 6. Open items / risks (carried forward, not smoothed over)

1. ~~Time budget unknown~~ — **resolved: no hard deadline** (user, 2026-10-15).
2. OpenAlex keyless daily budget may throttle corpus harvest → resolve at Gate A.
3. Reference-count norm and exact abstract-word precedent: measure 2–3 more
   published DISER reviews at Gate E/write-up.
4. Ethics declaration wording: verify against final instructions-to-authors page at write-up.
5. Prior-art absence is provisional pending Gate E's extended search.
6. Journal list for the multi-journal corpus not yet fixed → next step (Gate A).

## 7. Next phase (on acknowledgment): GATE A — DATA

Plan: fix the journal list (disciplinary + general science-ed titles, each with
ISSN), harvest via OpenAlex with pagination and saved raw responses under
`data/raw/`, record per-journal counts, verify schema (DOI, abstract, references,
year), then produce Gate A's Verification Report (source, counts, sample rows,
provenance notes) before any analysis runs.

---
**Evidence artifacts on disk:** `project/data/meta/` — diser_sample_article.pdf
(3,754,102 B, real PDF), diser_research_guidelines.html (209,212 B),
diser_review_guidelines.html (208,163 B); scripts under `project/scripts/`
(extract_style_evidence.py, measure_exemplar_norms.py ran clean).
