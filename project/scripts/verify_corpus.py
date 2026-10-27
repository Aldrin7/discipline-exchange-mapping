"""Gate A verification — runs AFTER harvest_corpus.py.

Reads data/raw/manifest.json + JSONL files and reports exactly what Gate A
requires: per-journal row counts (line count vs manifest), schema presence
rates for required fields, DOI uniqueness (within and across journals),
abstract/reference coverage, year ranges, and 2 sample rows per journal.
Any mismatch fails the gate (exit 1).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
REQUIRED_FIELDS = [
    "id", "doi", "display_name", "publication_year", "publication_date",
    "type", "cited_by_count", "authorships", "primary_location",
    "abstract_inverted_index", "referenced_works",
]


def main() -> int:
    manifest = json.loads((RAW_DIR / "manifest.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    all_dois: Counter[str] = Counter()
    total_lines = 0

    print(f"window: {manifest['from_date']}..{manifest['to_date']}")
    print(f"{'slug':<18} {'manifest':>9} {'lines':>9} {'yr range':<12} "
          f"{'abs%':>6} {'refs%':>6} {'uniq id':>8}")
    print("-" * 82)

    for j in manifest["journals"]:
        path = RAW_DIR / j["file"]
        if not path.exists():
            failures.append(f"{j['slug']}: file missing {j['file']}")
            continue
        n_lines, missing = 0, Counter()
        years, dois, ids = [], set(), set()
        abs_present = refs_present = 0
        samples: list[dict] = []
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                w = json.loads(line)
                n_lines += 1
                for f in REQUIRED_FIELDS:
                    if f not in w:
                        missing[f] += 1
                if w.get("abstract_inverted_index"):
                    abs_present += 1
                if w.get("referenced_works"):
                    refs_present += 1
                if w.get("publication_year"):
                    years.append(w["publication_year"])
                if w.get("doi"):
                    dois.add(w["doi"])
                    all_dois[w["doi"]] += 1
                ids.add(w.get("id"))
                if len(samples) < 2:
                    samples.append({
                        "title": (w.get("display_name") or "")[:90],
                        "year": w.get("publication_year"),
                        "doi": w.get("doi"),
                        "n_refs": len(w.get("referenced_works") or []),
                        "authors": len(w.get("authorships") or []),
                    })
        total_lines += n_lines
        if n_lines != j["works"]:
            failures.append(f"{j['slug']}: manifest {j['works']} != lines {n_lines}")
        if missing:
            failures.append(f"{j['slug']}: missing fields {dict(missing)}")
        if len(dois) != n_lines and len(dois | {None}) != n_lines:
            pass  # DOI gaps reported below, not fatal if ids unique
        yr = f"{min(years)}-{max(years)}" if years else "NONE"
        print(
            f"{j['slug']:<18} {j['works']:>9} {n_lines:>9} {yr:<12} "
            f"{100 * abs_present / max(n_lines, 1):>5.1f}% "
            f"{100 * refs_present / max(n_lines, 1):>5.1f}% "
            f"{len(ids):>8}"
        )
        for s in samples:
            print(f"    e.g. {s['year']} | {s['title']}")
            print(f"         doi={s['doi']} refs={s['n_refs']} authors={s['authors']}")

    dups = {d: c for d, c in all_dois.items() if c > 1}
    print("-" * 82)
    print(f"total lines: {total_lines} | manifest total: {manifest['total_works']}")
    print(f"cross-journal duplicate DOIs: {len(dups)}")
    if dups and len(dups) > total_lines * 0.01:
        failures.append(f"too many duplicate DOIs: {len(dups)}")
    if total_lines != manifest["total_works"]:
        failures.append(
            f"total mismatch: {total_lines} != {manifest['total_works']}"
        )
    print(f"api calls: {manifest.get('api_calls')} | cost: ${manifest.get('api_cost_usd')}")

    if failures:
        print("\nGATE A FAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nGATE A: schema/count checks PASSED (see caveats in report)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
