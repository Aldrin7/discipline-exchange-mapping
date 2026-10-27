"""Gate A phase 2 — corpus harvest from OpenAlex.

Fixes the journal list (ISSNs verified by name search in phase 1b), paginates
works per journal for 2019-2026 (DISER era), writes raw JSONL per journal plus
a manifest with real counts and total API cost. No analysis happens here.

Provenance rule (Rule 6): raw responses are saved as fetched; the manifest
records source IDs, filters, and cost, so any later substitution is visible.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# slug, issn, expected display_name (asserted), discipline tag
SOURCES = [
    ("diser", "2662-2300", "Disciplinary and Interdisciplinary Science Education Research", "bridge"),
    ("science_education", "0036-8326", "Science Education", "general"),
    ("jrst", "0022-4308", "Journal of Research in Science Teaching", "general"),
    ("ijse", "0950-0693", "International Journal of Science Education", "general"),
    ("rse", "0157-244X", "Research in Science Education", "general"),
    ("sse", "0305-7267", "Studies in Science Education", "general"),
    ("jbe", "0021-9266", "Journal of Biological Education", "biology"),
    ("cerp", "1756-1108", "Chemistry Education Research and Practice", "chemistry"),
    ("jce", "0021-9584", "Journal of Chemical Education", "chemistry"),
    ("prper", "2469-9896", "Physical Review Physics Education Research", "physics"),
    ("physed", "0031-9120", "Physics Education", "physics"),
    ("jge", "1089-9995", "Journal of Geoscience Education", "geoscience"),
    ("jee", "1069-4730", "Journal of Engineering Education", "engineering"),
    ("ejee", "0304-3797", "European Journal of Engineering Education", "engineering"),
    ("ijsted", "2196-7822", "International Journal of STEM Education", "interdisciplinary"),
]

FROM_DATE, TO_DATE = "2019-01-01", "2026-12-31"
PER_PAGE = 200
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_PATH = RAW_DIR / "progress.json"


def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {}


def save_progress(prog: dict) -> None:
    tmp = PROGRESS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(prog, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(PROGRESS_PATH)

SELECT = ",".join(
    [
        "id", "doi", "display_name", "publication_year", "publication_date",
        "type", "cited_by_count", "authorships", "primary_location",
        "abstract_inverted_index", "referenced_works", "topics", "keywords",
    ]
)

COST = {"usd": 0.0, "calls": 0}


def get_json(url: str, tries: int = 6) -> dict:
    """GET with backoff. Observed in Gate A: OpenAlex intermittently returns
    transient 401s to keyless clients under burst load (verified: same URL
    returns 200 seconds later via curl), so 401/429/5xx are retryable with
    long backoff — not fatal."""
    backoff = [30, 60, 90, 120, 120]
    for attempt in range(tries):
        try:
            full_url = url
            api_key = os.environ.get("OPENALEX_API_KEY", "").strip()
            if api_key:
                full_url = url + ("&" if "?" in url else "?") + f"api_key={api_key}"
            req = urllib.request.Request(full_url, headers={"User-Agent": "diser-corpus/1.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            COST["usd"] += float(data.get("meta", {}).get("cost_usd", 0.0))
            COST["calls"] += 1
            return data
        except urllib.error.HTTPError as exc:
            retryable = exc.code in (401, 408, 429, 500, 502, 503, 504)
            if not retryable or attempt == tries - 1:
                raise
            wait = backoff[min(attempt, len(backoff) - 1)]
            print(f"    HTTP {exc.code}; retry {attempt + 1}/{tries - 1} in {wait}s")
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == tries - 1:
                raise
            wait = backoff[min(attempt, len(backoff) - 1)]
            print(f"    retry {attempt + 1} after error: {exc} (in {wait}s)")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def resolve(issn: str, expected: str) -> str:
    src = get_json(f"https://api.openalex.org/sources/issn:{issn}")
    name = src.get("display_name", "")
    if name != expected:
        raise SystemExit(
            f"ISSN {issn} resolved to {name!r}, expected {expected!r} — ABORT (Rule 6)"
        )
    sid = src["id"].rsplit("/", 1)[-1]
    print(f"  resolved {issn} -> {sid} {name!r} (total works {src.get('works_count')})")
    return sid


def main() -> int:
    prog = load_progress()
    COST["usd"] = float(prog.get("_cost_usd", 0.0))
    manifest: dict = {
        "from_date": FROM_DATE,
        "to_date": TO_DATE,
        "per_page": PER_PAGE,
        "endpoint": "https://api.openalex.org/works",
        "journals": [],
    }
    for slug, issn, expected, tag in SOURCES:
        if slug in prog:
            manifest["journals"].append(prog[slug])
            print(f"[{slug}] skip — already harvested ({prog[slug]['works']} works)")
            continue
        print(f"[{slug}] resolving…", flush=True)
        sid = resolve(issn, expected)
        time.sleep(0.3)

        flt = (
            f"primary_location.source.id:{sid},"
            f"from_publication_date:{FROM_DATE},to_publication_date:{TO_DATE}"
        )
        out_path = RAW_DIR / f"{slug}.jsonl"
        n, cursor, years = 0, "*", {}
        with out_path.open("w", encoding="utf-8") as fh:
            while cursor:
                url = (
                    "https://api.openalex.org/works?filter="
                    + urllib.parse.quote(flt, safe=":,.@")
                    + f"&per-page={PER_PAGE}&cursor={urllib.parse.quote(cursor)}"
                    + f"&select={urllib.parse.quote(SELECT, safe=',')}"
                )
                data = get_json(url)
                results = data.get("results", [])
                for w in results:
                    fh.write(json.dumps(w, ensure_ascii=False) + "\n")
                    y = w.get("publication_year")
                    years[y] = years.get(y, 0) + 1
                n += len(results)
                cursor = data.get("meta", {}).get("next_cursor")
                if cursor == "*":
                    cursor = None
                time.sleep(0.5)
                if n and n % 2000 < PER_PAGE:
                    print(f"  {slug}: {n} works… (cost ${COST['usd']:.4f})")
        entry = {
            "slug": slug, "issn": issn, "openalex_source_id": sid,
            "display_name": expected, "tag": tag, "works": n,
            "by_year": {str(k): years[k] for k in sorted(years) if k},
            "file": out_path.name,
        }
        manifest["journals"].append(entry)
        prog[slug] = entry
        prog["_cost_usd"] = round(COST["usd"], 6)
        save_progress(prog)
        print(f"[{slug}] done: {n} works -> {out_path.name}", flush=True)
        time.sleep(0.5)

    manifest["total_works"] = sum(j["works"] for j in manifest["journals"])
    manifest["api_calls"] = COST["calls"]
    manifest["api_cost_usd"] = round(COST["usd"], 6)
    (RAW_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"TOTAL works: {manifest['total_works']}")
    print(f"API calls: {COST['calls']}  cost: ${COST['usd']:.4f}")
    print(f"manifest -> {RAW_DIR / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
