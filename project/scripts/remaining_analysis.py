"""Remaining analyses: BT quasi-variances (bootstrap CIs), Sankey alluvial,
and dynamic community detection (yearly)."""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"
FIGS = BASE / "manuscript" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

edges = pd.read_csv(PROC / "citation_edges_internal.csv")
jm = pd.read_csv(PROC / "journal_matrix.csv", index_col=0)
journal_order = list(jm.index)
C = jm.values.astype(float)
n = len(journal_order)

# ---------- 1. Bradley-Terry quasi-variances (bootstrap) ----------
# Resample edges with replacement, refit BT, collect influence per journal.
# Use 200 bootstrap reps (fast enough).
rng = np.random.default_rng(42)
N_BOOT = 200
boot_influence = np.zeros((N_BOOT, n))
# Precompute edge list for resampling
edge_list = edges[["citing_journal", "cited_journal"]].values
for b in range(N_BOOT):
    idx = rng.integers(0, len(edge_list), size=len(edge_list))
    sampled = edge_list[idx]
    # Build count matrix
    Cb = np.zeros((n, n))
    ji = {j: i for i, j in enumerate(journal_order)}
    for cj, cd in sampled:
        Cb[ji[cj], ji[cd]] += 1
    # Fit BT (Hunter MM)
    W = Cb.T.copy()
    W_i = W.sum(axis=1)
    N_ij = Cb + Cb.T
    pi = np.ones(n)
    for _ in range(200):
        pi_new = np.zeros(n)
        for i in range(n):
            denom = 0.0
            for j in range(n):
                if i == j or N_ij[i, j] == 0:
                    continue
                denom += N_ij[i, j] / (pi[i] + pi[j])
            pi_new[i] = W_i[i] / denom if denom > 0 else pi[i]
        pi_new = pi_new / pi_new.mean()
        if np.max(np.abs(pi_new - pi)) < 1e-10:
            pi = pi_new
            break
        pi = pi_new
    inf = pi / pi.sum()
    boot_influence[b] = inf

# Quasi-variance: SD across bootstrap
bt_qv = {}
for i, j in enumerate(journal_order):
    vals = boot_influence[:, i]
    bt_qv[j] = {
        "point": float(np.median(vals)),
        "lo_95": float(np.percentile(vals, 2.5)),
        "hi_95": float(np.percentile(vals, 97.5)),
        "sd": float(np.std(vals)),
    }
print("BT quasi-variance (DISER):", bt_qv["diser"])

# ---------- 2. Sankey alluvial (discipline -> journal -> discipline) ----------
# Source disciplines (citing) -> target disciplines (cited), aggregated
tag_order = sorted(edges["citing_tag"].unique())
# Build flow: source tag -> target tag
flow = edges.groupby(["citing_tag", "cited_tag"]).size().reset_index(name="count")
# Sankey nodes: source tags + target tags (same set, but separate indices for left/right)
src_nodes = [f"{t} (src)" for t in tag_order]
tgt_nodes = [f"{t} (tgt)" for t in tag_order]
all_nodes = src_nodes + tgt_nodes
node_idx = {name: i for i, name in enumerate(all_nodes)}

links_src = []
links_tgt = []
links_val = []
for _, r in flow.iterrows():
    s = f"{r['citing_tag']} (src)"
    t = f"{r['cited_tag']} (tgt)"
    links_src.append(node_idx[s])
    links_tgt.append(node_idx[t])
    links_val.append(int(r["count"]))

fig_sankey = go.Figure(data=[go.Sankey(
    node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
              label=all_nodes, color="rgba(31,119,180,0.8)"),
    link=dict(source=links_src, target=links_tgt, value=links_val,
              color="rgba(150,150,150,0.3)"),
)])
fig_sankey.update_layout(title_text="Discipline-to-discipline citation flows (internal edges)",
                         font_size=10, width=900, height=600)
fig_sankey.write_html(str(FIGS / "fig7_sankey.html"))
fig_sankey.write_image(str(FIGS / "fig7_sankey.png"), scale=2)
print("Saved fig7_sankey.png/html")

# ---------- 3. Dynamic community detection (yearly Louvain on tag-level) ----------
# Build yearly tag-tag networks and compute modularity
yearly_mod = {}
for year in sorted(edges["citing_year"].unique() if "citing_year" in edges.columns else []):
    pass

# edges doesn't have year; use works to get year per citing id
works = pd.read_csv(PROC / "works.csv")
id2year = dict(zip(works["id"], works["year"]))
edges["year"] = edges["citing_id"].map(id2year)
years = sorted(edges["year"].dropna().unique())
# Only use 2019-2025
years = [y for y in years if 2019 <= y <= 2025]
modularity_by_year = {}
for y in years:
    ey = edges[edges["year"] == y]
    # Build tag-tag adjacency
    T = pd.crosstab(ey["citing_tag"], ey["cited_tag"])
    # Align
    all_tags = sorted(set(tag_order))
    T = T.reindex(index=all_tags, columns=all_tags, fill_value=0)
    # Louvain on weighted graph
    G = nx.Graph()
    for t1 in all_tags:
        for t2 in all_tags:
            w = T.loc[t1, t2]
            if w > 0:
                G.add_edge(t1, t2, weight=float(w))
    if G.number_of_edges() == 0:
        modularity_by_year[int(y)] = None
        continue
    try:
        import community as community_louvain
        partition = community_louvain.best_partition(G, weight="weight", random_state=42)
        mod = community_louvain.modularity(partition, G, weight="weight")
    except ImportError:
        # fallback: use networkx greedy modularity
        communities = nx.community.greedy_modularity_communities(G, weight="weight")
        partition = {}
        for ci, comm in enumerate(communities):
            for node in comm:
                partition[node] = ci
        mod = nx.community.modularity(G, communities, weight="weight")
    modularity_by_year[int(y)] = round(float(mod), 4)
    print(f"  {int(y)}: modularity={mod:.4f}, communities={len(set(partition.values()))}")

# ---------- 4. Missingness bias: topic assignment by text source ----------
# Already in review_fixes; add per-journal ARI reference
missingness_bias = json.load(open(PROC / "review_fixes.json")) if (PROC / "review_fixes.json").exists() else {}

# ---------- save ----------
out = {
    "bt_quasi_variance": bt_qv,
    "sankey": "fig7_sankey.png",
    "modularity_by_year": modularity_by_year,
}
(PROC / "remaining_analysis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
print("Saved remaining_analysis.json")
print("Modularity by year:", modularity_by_year)
print("DONE")