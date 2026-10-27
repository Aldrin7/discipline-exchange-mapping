# -*- coding: utf-8 -*-
"""
recompute_stats.py — Recompute every quantified manuscript claim from real data.

Produces data/processed/recomputed_stats.json + stdout summary.
Sections:
  1. Per-journal deposit coverage + Wilson CIs (Table 1 replacement)
  2. Per-journal metrics: cross-tag share, EI, RS-Simpson, RS-distance (topic-profile)
  3. Betweenness, 4 graph specs (Table 3) + Spearman rho vs primary
  4. Weighting schemes micro/macro/sqrt/MoR (Table 5) + Kendall's W
  5. Leave-one-out (Table 6)
  6. Stratified bootstrap 2000 (CIs)
  7. Temporal pre/post, discipline-level
  8. Per-cluster metrics + gensim C_v (Table 2); LDA + HDBSCAN robustness
  9. External-field triangulation via sampled OpenAlex primary_topic fields
 10. Coverage adjustment (citing-side IPW) + JSON dump

Deviation declaration: gensim + scikit-learn used for robustness/coherence
(primary Gate C pipeline was numpy/fastembed/onnx only).
"""
import json, os, re, sys, time, math, random
import urllib.request, urllib.parse
import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr, pearsonr

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(PROJ, "data", "processed")
RAW = os.path.join(PROJ, "data", "raw")
OUT = os.path.join(PROC, "recomputed_stats.json")
RNG_SEED = 20261016

JOURNALS = ["cerp", "diser", "ejee", "ijse", "ijsted", "jbe", "jce", "jee",
            "jge", "jrst", "physed", "prper", "rse", "science_education", "sse"]
TAGS = sorted(["bridge", "chemistry", "engineering", "general",
               "interdisciplinary", "biology", "geoscience", "physics"])

def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def wilson(k, n, z=1.959963984540054):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0.0, c-h), min(1.0, c+h))

def norm_id(x):
    if not isinstance(x, str): return None
    return x.rsplit("/", 1)[-1]

# ---------- load core artifacts ----------
log("loading artifacts")
works = pd.read_csv(os.path.join(PROC, "works.csv"))
works["wid"] = works["id"].map(norm_id)
edges = pd.read_csv(os.path.join(PROC, "citation_edges_internal.csv"))
for c in ("citing_id", "cited_id"):
    edges[c] = edges[c].map(norm_id)
assign = pd.read_csv(os.path.join(PROC, "gatec_assignments.csv"))
assign["wid"] = assign["id"].map(norm_id)
jmat = pd.read_csv(os.path.join(PROC, "journal_matrix.csv"), index_col=0)
dmat = pd.read_csv(os.path.join(PROC, "discipline_matrix.csv"), index_col=0)
gtopics = json.load(open(os.path.join(PROC, "gatec_topics.json"), encoding="utf-8"))
gruns = json.load(open(os.path.join(PROC, "gatec_runs.json"), encoding="utf-8"))
gb = json.load(open(os.path.join(PROC, "gateb_stats.json"), encoding="utf-8"))

M = jmat.reindex(index=JOURNALS, columns=JOURNALS).fillna(0.0).to_numpy(float)  # rows=citing
tag_of = {r["journal"]: r["tag"] for _, r in works[["journal", "tag"]].drop_duplicates().iterrows()}
n_rec = works.groupby("journal").size().reindex(JOURNALS).to_numpy(float)
out_tot = M.sum(1); in_tot = M.sum(0)
RES = {"meta": {"seed": RNG_SEED, "n_works": int(len(works)), "n_edges_internal": int(len(edges))}}
log(f"works={len(works)} edges={len(edges)} internal matrix total={M.sum():.0f}")

# ---------- 1. deposit coverage (Table 1) ----------
cov = {}
for j in JOURNALS:
    wj = works[works.journal == j]
    k = int((wj.n_refs > 0).sum()); n = int(len(wj))
    lo, hi = wilson(k, n)
    cov[j] = {"n": n, "with_refs": k, "coverage": round(k/n, 4),
              "wilson95": [round(lo, 4), round(hi, 4)],
              "median_n_refs_with": float(wj.n_refs[wj.n_refs > 0].median()),
              "n_no_refs": n - k}
RES["deposit_coverage"] = cov
log("coverage:", {j: cov[j]["coverage"] for j in JOURNALS})

# ---------- 2. per-journal core metrics ----------
same = np.zeros(15); cross = np.zeros(15)
for i in range(15):
    for k in range(15):
        if tag_of[JOURNALS[k]] == tag_of[JOURNALS[i]]:
            same[i] += M[i, k]
        else:
            cross[i] += M[i, k]
share = cross / (cross + same)

# tag x cluster prevalence profiles (for RS-distance d_ik)
ct = pd.crosstab(assign["tag"], assign["cluster_seed1"]).reindex(index=TAGS).fillna(0.0)
prof = ct.div(ct.sum(1), axis=0).to_numpy(float)  # 8 x 20
def cosine_dist_rows(A):
    n = A.shape[0]; D = np.zeros((n, n))
    nrm = np.linalg.norm(A, axis=1, keepdims=True); nrm[nrm == 0] = 1
    An = A / nrm
    D = 1 - An @ An.T
    return D
Dtag = cosine_dist_rows(prof)
off = Dtag[np.triu_indices(8, 1)]
dmin, dmax = float(off.min()), float(off.max())
D01 = (Dtag - dmin) / (dmax - dmin) if dmax > dmin else Dtag * 0.0
np.fill_diagonal(D01, 0.0)

jr = {}
for i, j in enumerate(JOURNALS):
    tagp = np.zeros(8)
    for k in range(15):
        if tag_of[JOURNALS[k]] == tag_of[j]:
            tagp[TAGS.index(tag_of[j])] += M[i, k]
        else:
            tagp[TAGS.index(tag_of[JOURNALS[k]])] += M[i, k]
    tagp = tagp / tagp.sum()
    rs_s = float(1 - (tagp**2).sum())
    rs_d = float(tagp @ D01 @ tagp)
    jr[j] = {"out": int(out_tot[i]), "in": int(in_tot[i]),
             "cross_tag": round(float(share[i]), 4), "same_tag": round(float(same[i]), 4),
             "EI_out_tag": round(float(2*share[i] - 1), 4),
             "RS_simpson": round(rs_s, 4), "RS_dist": round(rs_d, 4),
             "tag_props": {TAGS[t]: round(float(tagp[t]), 4) for t in range(8) if tagp[t] > 0},
             "entropy_norm_15": gruns["network_S6"]["per_journal"][j]["entropy_norm_15"],
             "entropy_norm_8": gruns["network_S6"]["per_journal"][j]["entropy_norm_8tag"]}
RES["journal_metrics"] = jr
log("DISER:", jr["diser"]); log("JCE:", {k: jr["jce"][k] for k in ("cross_tag", "EI_out_tag", "RS_simpson")})

# ---------- 3. betweenness, 4 specs ----------
def betweenness(Mm, spec):
    n = Mm.shape[0]
    if spec in ("primary", "unweighted_directed"):
        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        for i in range(n):
            for k in range(n):
                if Mm[i, k] > 0:
                    G.add_edge(i, k, dist=(1.0/Mm[i, k] if spec == "primary" else 1.0))
        w = "dist" if spec == "primary" else None
    else:
        Ms = Mm + Mm.T
        G = nx.Graph()
        G.add_nodes_from(range(n))
        for i in range(n):
            for k in range(i+1, n):
                if Ms[i, k] > 0:
                    G.add_edge(i, k, dist=(1.0/Ms[i, k] if spec == "weighted_sym" else 1.0))
        w = "dist" if spec == "weighted_sym" else None
    bc = nx.betweenness_centrality(G, weight=w, normalized=True)
    return np.array([bc[i] for i in range(n)])

SPECS = ["primary", "unweighted_directed", "weighted_sym", "unweighted_undirected"]
bc_by_spec = {s: betweenness(M, s) for s in SPECS}

# RS under each spec: directed -> out-edge tag props; undirected -> combined ties
def tag_props_from_matrix(Mm, sym=False):
    out = {}
    Mm2 = Mm if not sym else (Mm + Mm.T)
    for i, j in enumerate(JOURNALS):
        tagp = np.zeros(8)
        for k in range(15):
            t = tag_of[JOURNALS[k]]
            tagp[TAGS.index(t)] += Mm2[i, k]
        tagp = tagp / tagp.sum()
        out[j] = tagp
    return out

t3 = {}
for s in SPECS:
    sym = s in ("weighted_sym", "unweighted_undirected")
    tp = tag_props_from_matrix(M, sym=sym)
    rows = {}
    for j in ("diser", "jce"):
        i = JOURNALS.index(j)
        rs_s = float(1 - (tp[j]**2).sum()); rs_d = float(tp[j] @ D01 @ tp[j])
        rows[j] = {"betweenness": round(float(bc_by_spec[s][i]), 4),
                   "RS_simpson": round(rs_s, 4), "RS_dist": round(rs_d, 4)}
    t3[s] = rows
rho = {}
for s in SPECS:
    r = spearmanr(bc_by_spec["primary"], bc_by_spec[s]).statistic
    rho[s] = round(float(r), 4)
RES["table3_betweenness_specs"] = {"by_spec": t3, "spearman_vs_primary": rho,
    "ranking_primary": [JOURNALS[i] for i in np.argsort(-bc_by_spec["primary"])]}
log("betweenness primary:", {j: round(float(bc_by_spec['primary'][JOURNALS.index(j)]), 3) for j in JOURNALS})
log("spearman:", rho)

# ---------- 4. weighting schemes (Table 5) ----------
# cite-side weights: journal j contributes total edge weight w_j
#   micro: w=out_j (raw counts); macro: w=1; sqrt: w=sqrt(n_j); MoR: w=m_j
def mor_size_factors():
    ntc = pd.crosstab(assign["journal"], assign["cluster_seed1"]).reindex(index=JOURNALS).fillna(0.0).to_numpy(float)
    X = ntc + 0.5
    g = np.exp(np.mean(np.log(X), axis=0))          # per-topic geometric mean over journals
    m = np.median(X / g, axis=1)
    return m / np.exp(np.mean(np.log(m)))           # renormalize to mean 1
m_mor = mor_size_factors()
w_scheme = {"micro": out_tot.copy(), "macro": np.ones(15),
            "sqrt": np.sqrt(n_rec), "MoR": m_mor}
agg_share = {s: float((w * share).sum() / w.sum()) for s, w in w_scheme.items()}
def kendall_w(rank_matrix):  # m judges x n items, entries = ranks
    R = np.asarray(rank_matrix, float)
    m, n = R.shape
    Rbar = R.mean()
    S = ((R - Rbar)**2).sum()
    return float(12 * S / (m*m * (n**3 - n)))
t5 = {}; btw_ranks = []
for s, w in w_scheme.items():
    bc_s = betweenness(M * (w / out_tot)[:, None], "primary")   # row j scaled to total w_j
    i = JOURNALS.index("diser")
    btw_ranks.append(np.argsort(np.argsort(-bc_s)))
    t5[s] = {"aggregate_cross_tag": round(agg_share[s], 4),
             "DISER_cross_tag": round(float(share[i]), 4),
             "DISER_betweenness": round(float(bc_s[i]), 4),
             "DISER_RS_simpson": round(jr["diser"]["RS_simpson"], 4),
             "DISER_btw_rank": int((-bc_s).argsort().argsort()[i] + 1)}
share_ranks = [np.argsort(np.argsort(-share)) for _ in w_scheme]   # share invariant -> identical
RES["table5_schemes"] = {"rows": t5,
    "kendall_w_btw": round(kendall_w(btw_ranks), 4),
    "kendall_w_share": round(kendall_w(share_ranks), 4),
    "mor_factors": {JOURNALS[i]: round(float(m_mor[i]), 3) for i in range(15)}}
log("t5 agg shares:", {s: round(v, 3) for s, v in agg_share.items()},
    "W_btw:", RES["table5_schemes"]["kendall_w_btw"])

# ---------- 5. leave-one-out (Table 6) ----------
loo = {}
for exc in JOURNALS:
    if exc == "diser":
        continue
    k = JOURNALS.index(exc)
    keep = [i for i in range(15) if i != k]
    M14 = M[np.ix_(keep, keep)]
    names14 = [JOURNALS[i] for i in keep]
    bc14 = betweenness(M14, "primary")
    idis = names14.index("diser")
    c = s_ = 0.0
    for kk in range(14):
        if tag_of[names14[kk]] == tag_of["diser"]:
            s_ += M14[idis, kk]
        else:
            c += M14[idis, kk]
    sh14 = {names14[i]: None for i in range(14)}
    for i in range(14):
        cc = ss = 0.0
        for kk in range(14):
            if tag_of[names14[kk]] == tag_of[names14[i]]:
                ss += M14[i, kk]
            else:
                cc += M14[i, kk]
        sh14[names14[i]] = cc / (cc + ss) if (cc + ss) > 0 else float("nan")
    rank_share = 1 + sum(1 for v in sh14.values() if v > sh14["diser"] and not math.isnan(v))
    rank_btw = 1 + sum(1 for i in range(14) if bc14[i] > bc14[idis])
    # RS simpson on remaining
    tagp = np.zeros(8)
    for kk in range(14):
        tagp[TAGS.index(tag_of[names14[kk]])] += M14[idis, kk]
    tagp = tagp / tagp.sum()
    loo[exc] = {"DISER_cross_tag": round(float(sh14["diser"]), 4),
                "DISER_betweenness": round(float(bc14[idis]), 4),
                "DISER_RS_simpson": round(float(1 - (tagp**2).sum()), 4),
                "DISER_rank_share": int(rank_share), "DISER_rank_btw": int(rank_btw)}
RES["table6_looo"] = loo
log("LOOO diser share range:", min(v["DISER_cross_tag"] for v in loo.values()),
    "-", max(v["DISER_cross_tag"] for v in loo.values()))

# ---------- 6. stratified bootstrap (2000) ----------
log("bootstrap...")
JIDX = {j: i for i, j in enumerate(JOURNALS)}
Wmat = np.zeros((len(assign), 15), np.int16)  # per-work counts to cited journals
rows_by_id = {w: i for i, w in enumerate(assign["wid"].tolist())}
eg = edges.groupby(["citing_id", "cited_journal"]).size().reset_index(name="n")
for _, r in eg.iterrows():
    i = rows_by_id.get(r["citing_id"])
    if i is not None:
        Wmat[i, JIDX[r["cited_journal"]]] = r["n"]
work_j = assign["journal"].map(JIDX).to_numpy()
groups = [np.where(work_j == i)[0] for i in range(15)]

def metrics_from_Mm(Mm):
    i = JOURNALS.index("diser"); ij = JOURNALS.index("jce")
    def sh(ii):
        c = s_ = 0.0
        for kk in range(15):
            if tag_of[JOURNALS[kk]] == tag_of[JOURNALS[ii]]:
                s_ += Mm[ii, kk]
            else:
                c += Mm[ii, kk]
        return c / (c + s_) if (c + s_) > 0 else np.nan
    tp = np.zeros(8)
    for kk in range(15):
        tp[TAGS.index(tag_of[JOURNALS[kk]])] += Mm[i, kk]
    tp = tp / tp.sum()
    bc = betweenness(Mm, "primary")[i]
    return sh(i), sh(ij), bc, float(1 - (tp**2).sum()), float(tp @ D01 @ tp)

rng = np.random.default_rng(RNG_SEED)
boot = []
for b in range(2000):
    tot = np.zeros((15, 15), np.int32)
    for gi in range(15):
        idx = rng.choice(groups[gi], size=len(groups[gi]), replace=True)
        tot[gi] = Wmat[idx].sum(0)
    boot.append(metrics_from_Mm(tot.astype(float)))
boot = np.array(boot)
names = ["DISER_share", "JCE_share", "DISER_btw", "DISER_RS_simpson", "DISER_RS_dist"]
RES["bootstrap95"] = {names[k]: {"point": round(float(np.nanmedian(boot[:, k])), 4) if k != 2 else round(float(np.nanmedian(boot[:, k])), 4),
                                 "lo": round(float(np.nanpercentile(boot[:, k], 2.5)), 4),
                                 "hi": round(float(np.nanpercentile(boot[:, k], 97.5)), 4),
                                 "span": round(float(np.nanpercentile(boot[:, k], 97.5) - np.nanpercentile(boot[:, k], 2.5)), 4)}
                      for k in range(5)}
log("bootstrap:", RES["bootstrap95"])

# ---------- 7. temporal + discipline ----------
wid_year = dict(zip(assign["wid"], assign["year"]))
edges["year"] = edges["citing_id"].map(wid_year)
temp = {}
for label, yrs in (("pre_2019_2021", (2019, 2021)), ("post_2022", (2022, 2100))):
    sub = edges[(edges.year >= yrs[0]) & (edges.year <= yrs[1])]
    row = {"n_edges": int(len(sub))}
    per = {}
    for j in JOURNALS:
        sj = sub[sub.citing_journal == j]
        if len(sj) == 0:
            continue
        per[j] = float((1 - sj.same_tag.mean()))
    row["DISER_share"] = round(per.get("diser", float("nan")), 4)
    row["JCE_share"] = round(per.get("jce", float("nan")), 4)
    row["macro_share"] = round(float(np.mean(list(per.values()))), 4)
    row["n_journals"] = len(per)
    aw = assign[assign.year.between(yrs[0], yrs[1])]
    prev = aw.cluster_seed1.value_counts(normalize=True)
    row["cluster_prev"] = {int(k): round(float(v), 4) for k, v in prev.items()}
    temp[label] = row
RES["temporal"] = temp
log("temporal macro:", temp["pre_2019_2021"]["macro_share"], "->", temp["post_2022"]["macro_share"])

disc = {}
Dm = dmat.to_numpy(float)
dnames = list(dmat.index)
cross_d = Dm.sum() - np.trace(Dm)
disc["micro_share_offdiag"] = round(float(cross_d / Dm.sum()), 4)
per_d = []
for i in range(len(dnames)):
    tot = Dm[i].sum()
    if tot > 0:
        per_d.append(1 - Dm[i, i] / tot)
disc["macro_share"] = round(float(np.mean(per_d)), 4)
disc["matrix"] = dmat.to_dict()
RES["discipline"] = disc
log("discipline micro/macro:", disc["micro_share_offdiag"], disc["macro_share"])

# ---------- 8. per-cluster metrics + coherence ----------
log("tokenizing corpus for coherence...")
STOP = set("""a about above after again against all am an and any are as at be because been before being below
between both but by could did do does doing down during each few for from further had has have having he her here
hers herself him himself his how i if in into is it its itself just me more most my myself no nor not now of off on
once only or other our ours ourselves out over own same she should so some such than that the their theirs them
themselves then there these they this those through to too under until up very was we were what when where which
while who whom why will with you your yours yourself yourselves also may can within across among get like use used
using one two three four five new study studies paper present analysis based results result methods method
""".split())
pat = re.compile(r"[a-z]{3,}")
def tok(text):
    return [t for t in pat.findall(str(text).lower()) if t not in STOP]

works_tok = [tok(t) for t in works["text"].tolist()]
works["wid2"] = works["wid"]
tok_by_id = dict(zip(works["wid"], works_tok))

from gensim.corpora import Dictionary
from gensim.models import CoherenceModel
dictionary = Dictionary(works_tok)
dictionary.filter_extremes(no_below=20, no_above=0.8)
corpus_tokens = [[t for t in d if t in dictionary.token2id] for d in works_tok]

cluster_terms = {}
BOILER = {"altmetric", "crossref", "pdf", "attention", "citations", "updated",
          "publication", "get", "source", "author", "institution", "doi", "url",
          "link", "page", "volume", "issue", "publisher", "date", "type", "id",
          "version", "cited_by", "referenced_by", "referenced_by_count", "cited_by_count"}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gatec import topic_terms as gc_topic_terms
cl1 = assign["cluster_seed1"].to_numpy()
raw_terms = gc_topic_terms(works["text"].fillna("").astype(str).tolist(), cl1, 20, top_n=20, min_df=20)
for k in range(20):
    tt = [e["term"] for e in raw_terms[str(k)] if e["term"] not in BOILER]
    cluster_terms[k] = tt[:10]
    if len(tt) < 5:
        log("WARN: cluster", k, "has only", len(tt), "cleaned terms")
    log("cluster", k, "cleaned:", ", ".join(cluster_terms[k]))

cm = CoherenceModel(topics=[cluster_terms[k] for k in range(20)],
                    texts=corpus_tokens, dictionary=dictionary, coherence="c_v",
                    processes=1)
cv_all = cm.get_coherence_per_topic()
per_cv = {k: round(float(cv_all[k]), 4) for k in range(20)}
log("KMeans C_v per cluster:", per_cv)

cl1 = assign["cluster_seed1"].to_numpy()
ent = {}; cross_cl = {}
eg2 = edges.merge(assign[["wid", "cluster_seed1", "tag"]], left_on="citing_id", right_on="wid", how="left", suffixes=("", "_c"))
for k in range(20):
    wj = assign[cl1 == k]["journal"].value_counts(normalize=True).to_numpy()
    ent[k] = round(float(-(wj * np.log(wj)).sum()), 4)
    sk = eg2[eg2.cluster_seed1 == k]
    cross_cl[k] = round(float((1 - sk.same_tag.mean())), 4) if len(sk) else None
t2 = {}
sizes = gruns["sizes_seed1"]
for k in range(20):
    t2[k] = {"size": int(sizes[str(k)] if str(k) in sizes else sizes[k]),
             "entropy_ln": ent[k], "cross_tag_share": cross_cl[k],
             "C_v": per_cv[k], "terms10": cluster_terms[k]}
RES["table2_clusters"] = t2
log("cluster 17:", {kk: t2[17][kk] for kk in ("size", "entropy_ln", "cross_tag_share")})
log("cluster 1:", {kk: t2[1][kk] for kk in ("size", "entropy_ln", "cross_tag_share")})
log("cluster 11:", {kk: t2[11][kk] for kk in ("size", "entropy_ln", "cross_tag_share")})

# ---------- 8b. LDA (sklearn) ----------
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import HDBSCAN
from sklearn.metrics import adjusted_rand_score
from scipy.optimize import linear_sum_assignment

log("fitting LDA k=20 (max_iter=100)...")
tfidf = TfidfVectorizer(min_df=20, max_df=0.8, stop_words="english",
                        token_pattern=r"(?u)\b[a-zA-Z]{3,}\b")
Xt = tfidf.fit_transform(works["text"].fillna("").astype(str).tolist())
vocab = np.array(tfidf.get_feature_names_out())
lda = LatentDirichletAllocation(n_components=20, doc_topic_prior=0.1,
                                topic_word_prior=0.01, max_iter=100,
                                learning_method="batch", random_state=1, n_jobs=-1)
theta = lda.fit_transform(Xt)
lda_top = {t: [vocab[i] for i in lda.components_[t].argsort()[-10:][::-1]] for t in range(20)}
cm_lda = CoherenceModel(topics=[lda_top[t] for t in range(20)],
                        texts=corpus_tokens, dictionary=dictionary, coherence="c_v",
                        processes=1)
cv_lda = cm_lda.get_coherence_per_topic()
lda_assign = theta.argmax(1)

# soft topic x journal distribution -> entropy per LDA topic
Jcol = assign["journal"].to_numpy()
lda_ent = []
for t in range(20):
    wsum = np.zeros(15)
    for gi in range(15):
        wsum[gi] = theta[Jcol == JOURNALS[gi], t].sum()
    p = wsum / wsum.sum()
    lda_ent.append(float(-(p[p > 0] * np.log(p[p > 0])).sum()))

# Hungarian match LDA <-> KMeans on soft-vs-hard contingency
C = np.zeros((20, 20))
for k in range(20):
    C[:, k] = theta[cl1 == k].sum(0)
ri, ci = linear_sum_assignment(-C)
matched = dict(zip(ri, ci))   # lda topic -> kmeans cluster
km_top5_bridge = sorted(range(20), key=lambda k: -ent[k])[:5]
lda_top5_bridge = sorted(range(20), key=lambda t: -lda_ent[t])[:5]
overlap5 = len({matched[t] for t in lda_top5_bridge} & set(km_top5_bridge))
ari_lda = float(adjusted_rand_score(cl1, lda_assign))
RES["lda"] = {"C_v_mean": round(float(np.mean(cv_lda)), 4),
              "C_v_per_topic": [round(float(x), 4) for x in cv_lda],
              "topic_entropy": [round(x, 4) for x in lda_ent],
              "matched_top5_bridge_overlap": int(overlap5),
              "ARI_vs_kmeans": round(ari_lda, 4),
              "top_terms": {t: lda_top[t] for t in lda_top5_bridge},
              "max_iter_used": int(lda.n_iter_)}
log("LDA C_v mean:", RES["lda"]["C_v_mean"], "ARI:", ari_lda, "overlap5:", overlap5,
    "iters:", lda.n_iter_)

# ---------- 8c. HDBSCAN on PCA-50 (BERTopic's clustering stage, no UMAP) ----------
log("PCA-50 + HDBSCAN...")
emb = np.load(os.path.join(PROC, "embeddings.npy")).astype(np.float64)
Xc = emb - emb.mean(0, keepdims=True)
_, S, Vt = np.linalg.svd(Xc, full_matrices=False)
Z = (Xc @ Vt[:50].T)
Z = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
hdb = HDBSCAN(min_cluster_size=15)
hl = hdb.fit_predict(Z)
n_cl = len(set(hl.tolist()) - {-1})
out_share = float((hl == -1).mean())
# cluster top terms by term frequency among cluster docs
from collections import Counter
def top_terms_tf(docs_toks, min_df=20):
    df = Counter()
    for d in docs_toks:
        df.update(set(d))
    keep = {t for t, c in df.items() if c >= min_df}
    return keep
assert len(emb) == len(assign) == len(works), "embedding/assignment order mismatch"
keep_terms = top_terms_tf(works_tok)
hdb_topics = {}; hdb_cv_list = []
for k in sorted(set(hl.tolist())):
    if k < 0:
        continue
    cnt = Counter()
    for i in np.where(hl == k)[0]:
        cnt.update({t for t in works_tok[i] if t in keep_terms})
    if len(cnt) == 0:
        continue
    tt = [t for t, _ in cnt.most_common(10)]
    hdb_topics[k] = tt
if hdb_topics:
    cm_h = CoherenceModel(topics=list(hdb_topics.values()), texts=corpus_tokens,
                          dictionary=dictionary, coherence="c_v", processes=1)
    hdb_cv_list = [float(x) for x in cm_h.get_coherence_per_topic()]
rse_share_in_outliers = float((works["journal"].to_numpy()[hl == -1] == "rse").mean()) if (hl == -1).any() else None
RES["hdbscan"] = {"n_clusters": int(n_cl), "outlier_share": round(out_share, 4),
                  "C_v_mean": round(float(np.mean(hdb_cv_list)), 4) if hdb_cv_list else None,
                  "ARI_vs_kmeans": round(float(adjusted_rand_score(cl1, hl)), 4),
                  "outlier_journal_composition": {j: round(float(v), 4) for j, v in
                      (works["journal"][hl == -1].value_counts(normalize=True).items())} if (hl == -1).any() else {},
                  "RSE_share_of_outliers": round(rse_share_in_outliers, 4) if rse_share_in_outliers is not None else None}
log("HDBSCAN:", n_cl, "clusters, outliers:", round(out_share, 3),
    "C_v:", RES["hdbscan"]["C_v_mean"], "ARI:", RES["hdbscan"]["ARI_vs_kmeans"])

# ---------- 9. external-field triangulation (sampled OpenAlex fields) ----------
log("parsing raw JSONL for external references + citing-side fields...")
STEM_F = {"Agricultural and Biological Sciences", "Biochemistry, Genetics and Molecular Biology",
          "Chemical Engineering", "Chemistry", "Computer Science", "Earth and Planetary Sciences",
          "Energy", "Engineering", "Environmental Science", "Immunology and Microbiology",
          "Materials Science", "Mathematics", "Neuroscience",
          "Pharmacology, Toxicology and Pharmaceutics", "Physics and Astronomy", "Veterinary Science"}
SOC_F = {"Psychology", "Education", "Social Sciences", "Economics, Econometrics and Finance"}
OTHER_F = {"Arts and Humanities", "Business, Management and Accounting", "Decision Sciences",
           "Dentistry", "Medicine", "Nursing", "Health Professions"}
def bucket(field):
    if field in STEM_F: return "stem"
    if field in SOC_F: return "social"
    return "other"

def rec_field(rec):
    pt = rec.get("primary_topic")
    if isinstance(pt, dict) and pt.get("field", {}).get("display_name"):
        return pt["field"]["display_name"]
    tops = rec.get("topics") or []
    if tops and isinstance(tops[0], dict) and tops[0].get("field", {}).get("display_name"):
        return tops[0]["field"]["display_name"]
    return None

corpus_ids = set(works["wid"])
cite_field = {}          # wid -> field bucket
ext_pairs = []           # (citing_wid, ref_wid)
for fn in sorted(os.listdir(RAW)):
    if not fn.endswith(".jsonl"):
        continue
    for line in open(os.path.join(RAW, fn), encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        wid = norm_id(rec.get("id"))
        f = rec_field(rec)
        if wid and f:
            cite_field[wid] = bucket(f)
        for r in (rec.get("referenced_works") or []):
            rid = norm_id(r)
            if rid and rid not in corpus_ids:
                ext_pairs.append((wid, rid))
n_ext = len(ext_pairs)
log(f"external ref instances: {n_ext} (manuscript claims 512,324)")

def api_fields(ids):   # ids: list of W-ids -> {wid: field_display_name}
    out = {}
    key = open(os.path.join(PROJ, ".env"), encoding="utf-8").read().split("OPENALEX_API_KEY=")[1].splitlines()[0].strip()
    for i in range(0, len(ids), 50):
        batch = ids[i:i+50]
        url = ("https://api.openalex.org/works?filter=openalex_id:" + "|".join(batch)
               + "&per-page=50&select=id,primary_topic&api_key=" + key)
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    data = json.load(r)
                for w in data.get("results", []):
                    f = (w.get("primary_topic") or {}).get("field", {}).get("display_name")
                    if f:
                        out[norm_id(w["id"])] = f
                break
            except Exception as ex:
                log("  api retry", attempt, str(ex)[:120])
                time.sleep(2 * (attempt + 1))
        time.sleep(0.12)
    return out

rng1 = np.random.default_rng(RNG_SEED)
samp_idx = rng1.choice(n_ext, size=3000, replace=False)
samp_pairs = [ext_pairs[i] for i in samp_idx]
# per-cluster supplement: up to 40 ext refs per cluster (seed+1)
cl_of = dict(zip(assign["wid"], cl1))
rng2 = np.random.default_rng(RNG_SEED + 1)
by_cluster = {}
for wid, rid in ext_pairs:
    k = cl_of.get(wid)
    if k is not None:
        by_cluster.setdefault(k, []).append((wid, rid))
sup_pairs = []
for k in range(20):
    pool = by_cluster.get(k, [])
    if not pool:
        continue
    m = min(40, len(pool))
    sup_pairs += [(k, pool[i]) for i in rng2.choice(len(pool), size=m, replace=False)]
all_fetch = sorted({rid for _, rid in samp_pairs} | {rid for _, (w2, rid) in sup_pairs})
log(f"fetching fields for {len(all_fetch)} unique external works...")
fmap = api_fields(all_fetch)
log(f"  resolved {len(fmap)}")
unresolved = len(all_fetch) - len(fmap)

def classify(pairs_wids):
    c = {"stem": 0, "social": 0, "other": 0, "unresolved": 0}
    for wid, rid in pairs_wids:
        f = fmap.get(rid)
        if f is None:
            c["unresolved"] += 1
        else:
            c[bucket(f)] += 1
    n = sum(c.values())
    props = {k: round(c[k] / n, 4) for k in ("stem", "social", "other")}
    ci = {k: [round(wilson(c[k], n)[0], 4), round(wilson(c[k], n)[1], 4)] for k in ("stem", "social", "other")}
    return {"n": n, "counts": c, "props": props, "wilson95": ci}

field_global = classify(samp_pairs)
# cluster-level divergence + correlation with internal cross-tag share
div = {}
for k, (wid, rid) in sup_pairs:
    f = fmap.get(rid)
    if f is None or wid not in cite_field:
        continue
    div.setdefault(k, [0, 0])
    div[k][1] += 1
    if bucket(f) != cite_field[wid]:
        div[k][0] += 1
div_share = {k: div[k][0] / div[k][1] for k in div if div[k][1] >= 15}
ks = sorted(div_share)
xs = [cross_cl[k] for k in ks]
ys = [div_share[k] for k in ks]
r, p = pearsonr(xs, ys)
RES["field_tri"] = {"global_sample": field_global, "api_resolved": len(fmap),
                    "api_unresolved": unresolved,
                    "citing_side_classified_share": round(len(cite_field) / len(works), 4),
                    "cluster_divergence": {int(k): round(v, 4) for k, v in div_share.items()},
                    "pearson_r_vs_internal_cross": {"r": round(float(r), 4), "p": float(p),
                                                    "n_clusters": len(xs)}}
log("field props:", field_global["props"], "n:", field_global["n"],
    "r:", round(float(r), 3), "p:", f"{p:.2g}")

# ---------- 10. coverage adjustment (citing-side IPW) ----------
kappa = np.array([cov[j]["coverage"] for j in JOURNALS])
Minv = M / kappa[:, None]
c2 = s2 = 0.0
for i in range(15):
    for kk in range(15):
        if tag_of[JOURNALS[kk]] == tag_of[JOURNALS[i]]:
            s2 += Minv[i, kk]
        else:
            c2 += Minv[i, kk]
micro_adj = c2 / (c2 + s2)
# topic-level: weighted vs raw cross-tag share per cluster
adj_topic = {}
for k in range(20):
    sk = eg2[eg2.cluster_seed1 == k]
    if len(sk) == 0:
        continue
    wipw = 1 / sk["citing_journal"].map(lambda j: cov[j]["coverage"]).to_numpy()
    raw = float((1 - sk.same_tag.mean()))
    adj = float((wipw * (1 - sk.same_tag.to_numpy())).sum() / wipw.sum())
    adj_topic[k] = {"raw": round(raw, 4), "ipw": round(adj, 4), "delta": round(adj - raw, 4)}
max_delta = max(abs(v["delta"]) for v in adj_topic.values()) if adj_topic else None
RES["coverage_adjustment"] = {
    "micro_raw": round(float(cross.sum() / (cross.sum() + same.sum())), 4),
    "micro_ipw": round(float(micro_adj), 4),
    "macro_ipw": round(float(np.mean([cross[i]/(cross[i]+same[i]) for i in range(15)])), 4),
    "per_journal_invariant": True,
    "topic_max_abs_delta": round(float(max_delta), 4) if max_delta else None,
    "topics": adj_topic}
log("coverage adj micro:", RES["coverage_adjustment"]["micro_raw"], "->", RES["coverage_adjustment"]["micro_ipw"],
    "topic max delta:", RES["coverage_adjustment"]["topic_max_abs_delta"])

json.dump(RES, open(OUT, "w", encoding="utf-8"), indent=1)
log("WROTE", OUT)





