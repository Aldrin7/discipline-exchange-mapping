# Mapping Knowledge Exchange Across Disciplinary Boundaries in Science Education

**MAPPING KNOWLEDGE EXCHANGE ACROSS DISCIPLINARY BOUNDARIES IN SCIENCE EDUCATION: A CITATION-NETWORK AND TOPIC-MODELING ANALYSIS OF 15 JOURNALS, 2019–2026**

## Overview

This repository contains the complete research project for a computational map of knowledge exchange between disciplinary science-education subfields. The study combines citation-network analysis with topic modeling over a multi-journal corpus (14,333 records from 15 journals, 2019–2026) to answer three research questions:

1. **RQ1:** Which science-education disciplines cite each other, and which remain siloed?
2. **RQ2:** Which topics and journals act as bridges across disciplinary boundaries?
3. **RQ3:** Does DISER (Disciplinary and Interdisciplinary Science Education Research), whose mission explicitly emphasizes bridging disciplinary and interdisciplinary approaches, function as a broker?

## Key Findings

- **DISER** exhibits the highest cross-disciplinary citation share (0.841 citing, 0.798 cited), highest E-I index (+0.68), and highest Rao-Stirling diversity (Simpson 0.66).
- **JCE** (Journal of Chemical Education) and **PRPER** (Physical Review Physics Education Research) are the most siloed venues.
- Cross-disciplinary exchange increased modestly post-pandemic (macro-average 0.22–0.29).
- 20 topic clusters recover interpretable subfield specializations; STEM equity and biology education clusters show the strongest bridging potential.

## Repository Structure

```
project/
├── 00_GATE0_topic_and_venue.md       # Topic selection & venue verification
├── 01_GATE_A_data_report.md          # Corpus harvesting report
├── 02_GATE_B_preprocessing_report.md # Data preprocessing pipeline
├── 03_GATE_C_scope_declaration.md    # Scope & methodology declaration
├── 04_GATE_C_run_report.md           # Analysis run report
├── 05_GATE_E_report.md               # Extended novelty search & ethics
├── data/
│   ├── raw/                          # Raw OpenAlex JSONL responses
│   ├── processed/                    # Processed data (embeddings, matrices, JSON)
│   └── meta/                         # Journal guidelines and metadata
├── manuscript/                       # Manuscript files (MD, DOCX, PDF, TeX)
│   └── figures/                      # Publication figures
└── scripts/                          # Analysis scripts (Python)
```

## Data

- **Source:** OpenAlex API (public, keyless with rate limits)
- **Corpus:** 15 science-education journals (2019–2026)
- **Records:** 14,333 works with abstracts, citation edges, and topic assignments
- **Processed data** includes: citation networks, journal matrices, KMeans topic assignments, embeddings, and all computed metrics

## Reproducibility

All analysis scripts use open-source tools (numpy, fastembed, ONNX Runtime). The processing pipeline follows a gated approach:

- **GATE A:** Data harvesting and verification
- **GATE B:** Preprocessing with declared policies
- **GATE C:** Scope declaration and model training
- **GATE E:** Extended novelty search and final reporting

Scripts are numbered to match gates and can be run sequentially from the `project/` directory.

## License

This repository contains research data and code for academic purposes. The underlying OpenAlex data is licensed under CC0.

## Citation

When using this work, please cite the manuscript and acknowledge the OpenAlex project for providing open bibliometric metadata.
