"""Gate B — preprocessing / feature construction from raw OpenAlex JSONL.

Declared policies (made BEFORE any model is trained, per Gate C rules):
  P1 missing-abstract policy: reconstruct abstract from the inverted index;
     if absent/too short (<5 tokens) fall back to title + author keywords,
     flagged as text_source='title_keywords'. Both variants are kept so a
     sensitivity analysis (abstract-only vs. with-fallback) can run later.
     OpenAlex `topics` are stored as metadata ONLY — never as model text
     (would be circular: modeling OpenAlex's own topic assignments).
  P2 citation edges: only edges whose CITED id is inside the 15-journal
     corpus are written (internal edges); external refs are counted, not
     written. Ref-coverage differences across journals stay visible in stats.
  P3 temporal handling: 2026 is a partial year (harvest date 2026-10-15);
     years stored raw, 2026 flagged in stats for later rate-normalization.

Outputs (data/processed/): works.csv, citation_edges_internal.csv,
journal_matrix.csv, discipline_matrix.csv, gateb_stats.json.
Every count printed is computed from the files (Rule 1).
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_ABS_TOKENS = 5


def rebuild_abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pos: dict[int, str] = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def tokens(text: str) -> int:
    return len(text.split())


def main() -> int:
    manifest = json.loads((RAW_DIR / "manifest.json").read_text(encoding="utf-8"))
    journals = manifest["journals"]
    slug_meta = {j["slug"]: (j["tag"], j["display_name"]) for j in journals}
    expected = {j["slug"]: j["works"] for j in journals}

    # ---- pass 1: corpus id map + basic record checks ----
    id2slug: dict[str, str] = {}
    lines_seen: Counter = Counter()
    for j in journals:
        with (RAW_DIR / j["file"]).open(encoding="utf-8") as fh:
            for line in fh:
                w = json.loads(line)
                wid = w.get("id")
                if not wid:
                    raise SystemExit(f"row without id in {j['file']} (Gate B fail)")
                if wid in id2slug:
                    raise SystemExit(f"duplicate id {wid} (Gate B fail)")
                id2slug[wid] = j["slug"]
                lines_seen[j["slug"]] += 1
    for j in journals:
        if lines_seen[j["slug"]] != expected[j["slug"]]:
            raise SystemExit(f"count drift for {j['slug']} (Gate B fail)")
    print(f"corpus ids indexed: {len(id2slug)}", flush=True)

    # ---- pass 2: works table + internal citation edges ----
    works_path = OUT_DIR / "works.csv"
    edges_path = OUT_DIR / "citation_edges_internal.csv"
    text_sources: dict[str, Counter] = defaultdict(Counter)
    year_counts: Counter = Counter()
    n_refs_total = 0
    n_refs_internal = 0
    edge_rows = 0
    out_deg: Counter = Counter()
    in_deg: Counter = Counter()

    with works_path.open("w", newline="", encoding="utf-8") as wfh, \
         edges_path.open("w", newline="", encoding="utf-8") as efh:
        wcsv = csv.writer(wfh)
        wcsv.writerow([
            "id", "doi", "title", "year", "journal", "tag", "type",
            "text_source", "text", "keywords", "openalex_top_topic",
            "n_refs", "n_refs_internal", "n_authors", "cited_by_count",
        ])
        ecsv = csv.writer(efh)
        ecsv.writerow([
            "citing_id", "cited_id", "citing_journal", "cited_journal",
            "citing_tag", "cited_tag", "same_journal", "same_tag",
        ])

        for j in journals:
            slug, tag = j["slug"], j["tag"]
            with (RAW_DIR / j["file"]).open(encoding="utf-8") as fh:
                for line in fh:
                    w = json.loads(line)
                    abstract = rebuild_abstract(w.get("abstract_inverted_index"))
                    title = (w.get("display_name") or "").strip()
                    kws = ", ".join(
                        k.get("display_name", "") for k in (w.get("keywords") or [])
                    )
                    if tokens(abstract) >= MIN_ABS_TOKENS:
                        text_source, text = "abstract", abstract
                    else:
                        text_source, text = "title_keywords", title
                        if kws:
                            text = f"{title}. Keywords: {kws}"
                    text_sources[slug][text_source] += 1
                    year = w.get("publication_year") or ""
                    year_counts[year] += 1

                    refs = w.get("referenced_works") or []
                    n_refs_total += len(refs)
                    internal = [r for r in refs if r in id2slug]
                    n_refs_internal += len(internal)
                    n_auth = len(w.get("authorships") or [])
                    top_topic = ""
                    topics = w.get("topics") or []
                    if topics:
                        top_topic = (topics[0] or {}).get("display_name", "")
                    wcsv.writerow([
                        w.get("id"), w.get("doi") or "", title, year, slug, tag,
                        w.get("type") or "", text_source, text, kws, top_topic,
                        len(refs), len(internal), n_auth, w.get("cited_by_count", 0),
                    ])

                    for r in internal:
                        cslug = id2slug[r]
                        ctag = slug_meta[cslug][0]
                        ecsv.writerow([
                            w["id"], r, slug, cslug, tag, ctag,
                            int(slug == cslug), int(tag == ctag),
                        ])
                        edge_rows += 1
                        out_deg[slug] += 1
                        in_deg[cslug] += 1
            print(f"[{slug}] table rows: {lines_seen[slug]}", flush=True)

    # ---- aggregates ----
    order = [j["slug"] for j in journals]
    idx = {s: i for i, s in enumerate(order)}
    jm = [[0] * len(order) for _ in order]
    tag_order = sorted({j["tag"] for j in journals})
    tidx = {t: i for i, t in enumerate(tag_order)}
    tm = [[0] * len(tag_order) for _ in tag_order]
    with edges_path.open(encoding="utf-8") as fh:
        next(fh)
        for row in csv.reader(fh):
            _, _, cj, tj, ct, tt, _, _ = row
            jm[idx[cj]][idx[tj]] += 1
            tm[tidx[ct]][tidx[tt]] += 1

    with (OUT_DIR / "journal_matrix.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["citing\\cited"] + order)
        for i, s in enumerate(order):
            w.writerow([s] + jm[i])
    with (OUT_DIR / "discipline_matrix.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["citing\\cited"] + tag_order)
        for i, t in enumerate(tag_order):
            w.writerow([t] + tm[i])

    stats = {
        "corpus_works": len(id2slug),
        "year_counts": {str(k): v for k, v in sorted(year_counts.items())},
        "partial_year_flag": {"2026": "partial through 2026-10-15 (policy P3)"},
        "text_sources": {s: dict(c) for s, c in text_sources.items()},
        "refs_total": n_refs_total,
        "refs_internal": n_refs_internal,
        "refs_internal_pct": round(100 * n_refs_internal / max(n_refs_total, 1), 2),
        "internal_edge_rows": edge_rows,
        "out_degree": {s: out_deg[s] for s in order},
        "in_degree": {s: in_deg[s] for s in order},
        "journal_order": order,
        "discipline_order": tag_order,
        "policies": {
            "P1": "abstract if >=5 tokens else title+keywords (flagged)",
            "P2": "internal citation edges only; external refs counted",
            "P3": "2026 partial year flagged for rate analyses",
        },
    }
    (OUT_DIR / "gateb_stats.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8"
    )

    abs_n = sum(c.get("abstract", 0) for c in text_sources.values())
    fb_n = sum(c.get("title_keywords", 0) for c in text_sources.values())
    print("\n=== GATE B STATS (computed from files) ===")
    print(f"works rows: {len(id2slug)}")
    print(f"text_source: abstract={abs_n}  title_keywords={fb_n}")
    print(f"refs total={n_refs_total} internal={n_refs_internal} "
          f"({stats['refs_internal_pct']}%)")
    print(f"internal edges written: {edge_rows}")
    print(f"year counts: {dict(sorted(year_counts.items()))}")
    print(f"outputs -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

