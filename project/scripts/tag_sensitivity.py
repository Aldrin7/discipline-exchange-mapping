"""Sensitivity: recompute DISER cross-tag share and E-I under alternative
tag groupings (merge DISER into an existing non-singleton tag)."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"
edges = pd.read_csv(PROC / "citation_edges_internal.csv")

def recompute(tag_map):
    # tag_map: dict slug -> tag (revised)
    # Recompute cross-tag share and E-I for DISER
    diser_out = edges[edges["citing_journal"] == "diser"]
    diser_in = edges[edges["cited_journal"] == "diser"]
    # outgoing
    out_cross = (diser_out["citing_tag"].map(tag_map) != diser_out["cited_tag"].map(tag_map)).mean() if len(diser_out) else 0
    # Wait, need to use revised tags for both sides
    out_cross = (diser_out["citing_journal"].map(lambda x: tag_map.get(x, x)) != diser_out["cited_journal"].map(lambda x: tag_map.get(x, x))).mean()
    in_cross = (diser_in["citing_journal"].map(lambda x: tag_map.get(x, x)) != diser_in["cited_journal"].map(lambda x: tag_map.get(x, x))).mean()
    # E-I = (cross - same) / (cross + same) = 2*cross - 1
    ei_out = 2 * out_cross - 1
    ei_in = 2 * in_cross - 1
    return {"cross_out": round(float(out_cross), 4), "cross_in": round(float(in_cross), 4),
            "EI_out": round(float(ei_out), 4), "EI_in": round(float(ei_in), 4)}

# Original: DISER -> bridge (singleton)
original_map = {s: s for s in edges["citing_journal"].unique()}
# Actually use the original tag mapping
orig_tags = {}
for _, r in edges[["citing_journal", "citing_tag"]].drop_duplicates().iterrows():
    orig_tags[r["citing_journal"]] = r["citing_tag"]
print("Original tags:", orig_tags)

# Scenario A: merge DISER into "interdisciplinary"
map_A = dict(orig_tags)
map_A["diser"] = "interdisciplinary"
res_A = recompute(map_A)
print("Scenario A (DISER -> interdisciplinary):", res_A)

# Scenario B: merge DISER into "general"
map_B = dict(orig_tags)
map_B["diser"] = "general"
res_B = recompute(map_B)
print("Scenario B (DISER -> general):", res_B)

# Scenario C: merge DISER into "biology"
map_C = dict(orig_tags)
map_C["diser"] = "biology"
res_C = recompute(map_C)
print("Scenario C (DISER -> biology):", res_C)

# Original
res_orig = recompute(orig_tags)
print("Original (DISER -> bridge singleton):", res_orig)

# Also: what if we exclude DISER entirely and report entropy-based brokerage?
# Entropy across 15 journals (tag-independent) for DISER
from collections import Counter
import math
diser_out = edges[edges["citing_journal"] == "diser"]
cited_counts = Counter(diser_out["cited_journal"])
total = sum(cited_counts.values())
p = {j: c/total for j, c in cited_counts.items()}
H = -sum(pp * math.log(pp) for pp in p.values() if pp > 0)
print(f"DISER outgoing entropy (15 journals): {H:.4f} (max possible: {math.log(15):.4f})")

# Save results
out = {
    "original_bridge_singleton": res_orig,
    "scenario_A_interdisciplinary": res_A,
    "scenario_B_general": res_B,
    "scenario_C_biology": res_C,
    "diser_entropy_15": round(H, 4),
    "max_entropy_15": round(math.log(15), 4),
}
import json
(BASE / "data" / "processed" / "tag_sensitivity.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))