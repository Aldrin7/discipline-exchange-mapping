"""Gate C — declared analysis run. Scope FROZEN in 03_GATE_C_scope_declaration.md.

Implements S1-S10 with numpy only (no new packages, per declared scope).
Every number printed/written is computed here from data; wall-clocks logged.
Outputs -> data/processed/: embeddings.npy (cache), gatec_assignments.csv,
gatec_topics.json, gatec_runs.json.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROJ = Path(__file__).resolve().parents[1]
PROC = PROJ / "data" / "processed"

SEEDS = [1, 2, 3]
K = 20
K_SWEEP = [15, 25]
PCA_DIM = 50
MAX_ITER = 300
TOL = 1e-4
EMBED_FALLBACKS = [
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "snowflake/snowflake-arctic-embed-xs",
]
STOPWORDS = set("""
a about above after again against all am an and any are as at be because been
before being below between both but by can did do does doing down during each
few for from further had has have having he her here hers herself him himself
his how i if in into is it its itself just me more most my myself no nor not
now of off on once only or other our ours ourselves out over own same she so
some such than that the their theirs them themselves then there these they
this those through to too under until up very was we were what when where
which while who whom why will with you your yours yourself yourselves also
among within without upon across via using used use one two three many much
""".split())


def load_works() -> dict:
    ids, texts, journals, tags, years, srcs = [], [], [], [], [], []
    with (PROC / "works.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ids.append(row["id"])
            texts.append(row["text"])
            journals.append(row["journal"])
            tags.append(row["tag"])
            years.append(row["year"])
            srcs.append(row["text_source"])
    return {"ids": ids, "texts": texts, "journal": journals, "tag": tags,
            "year": years, "source": srcs}


def embed(texts: list[str]) -> tuple[np.ndarray, str]:
    """S2: fastembed, declared fallback order; record actually-used model."""
    from fastembed import TextEmbedding
    cache = PROC / "embeddings.npy"
    used = PROC / "embeddings_model.txt"
    if cache.exists() and used.exists():
        model_name = used.read_text(encoding="utf-8").strip()
        X = np.load(cache)
        if X.shape[0] == len(texts):
            print(f"[embed] REUSED cache {cache.name} model={model_name}", flush=True)
            return X, model_name + " (reused)"
    last_err = None
    for name in EMBED_FALLBACKS:
        try:
            t0 = time.time()
            print(f"[embed] loading {name} ...", flush=True)
            # memory-tight host (no pagefile): batch=8 keeps activation memory
            # small; parallel=None forces fastembed's IN-PROCESS sequential
            # path (onnx_text_model.py:135) — parallel=1 would spawn a
            # multiprocessing pool that deadlocks on this Windows host.
            model = TextEmbedding(model_name=name, threads=4)
            print(f"[embed] model loaded ({time.time()-t0:.1f}s), encoding "
                  f"{len(texts)} docs ...", flush=True)

            def tracked(seq):  # progress visible if a native crash occurs
                for i, t in enumerate(seq, 1):
                    if i % 1000 == 0:
                        print(f"[embed] consumed {i}/{len(seq)}", flush=True)
                    yield t

            vecs = list(model.embed(tracked(texts), batch_size=8))
            X = np.array(vecs, dtype=np.float32)
            dt = time.time() - t0
            np.save(cache, X)
            used.write_text(name, encoding="utf-8")
            print(f"[embed] model={name} shape={X.shape} wall={dt:.1f}s", flush=True)
            return X, f"{name} ({dt:.1f}s, batch=16, parallel=1, threads=4)"
        except Exception as e:  # noqa: BLE001 — declared fallback chain
            last_err = e
            print(f"[embed] FAILED {name}: {e}", flush=True)
    raise SystemExit(f"all embedding models failed: {last_err}")


def pca_l2(X: np.ndarray, dim: int) -> np.ndarray:
    """S3: centered SVD -> `dim` components, rows L2-normalized."""
    t0 = time.time()
    Xc = X - X.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    Z = U[:, :dim] * S[:dim]
    Z /= np.linalg.norm(Z, axis=1, keepdims=True) + 1e-12
    print(f"[pca] {X.shape[1]}->{Z.shape[1]}d wall={time.time()-t0:.2f}s "
          f"var={((S[:dim]**2).sum()/(S**2).sum()):.3f}", flush=True)
    return Z.astype(np.float32)


def kmeans_pp_init(X: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    n = X.shape[0]
    centers = [X[rng.integers(n)]]
    d2 = ((X - centers[0]) ** 2).sum(axis=1)
    for _ in range(1, k):
        probs = d2 / (d2.sum() + 1e-12)
        centers.append(X[rng.choice(n, p=probs)])
        d2 = np.minimum(d2, ((X - centers[-1]) ** 2).sum(axis=1))
    return np.array(centers, dtype=np.float32)


def lloyd(X: np.ndarray, k: int, seed: int) -> tuple[np.ndarray, list[float], int]:
    """S4: Lloyd's algorithm; returns labels, inertia curve, n_iter."""
    rng = np.random.default_rng(seed)
    C = kmeans_pp_init(X, k, rng)
    curve: list[float] = []
    prev = math.inf
    labels = np.zeros(X.shape[0], dtype=np.int32)
    for it in range(1, MAX_ITER + 1):
        d2 = ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)
        labels = d2.argmin(axis=1).astype(np.int32)
        inertia = float(d2[np.arange(X.shape[0]), labels].sum())
        curve.append(inertia)
        for j in range(k):  # update; empty cluster -> farthest point (declared)
            mask = labels == j
            if mask.any():
                C[j] = X[mask].mean(axis=0)
            else:
                C[j] = X[d2.min(axis=1).argmax()]
        if math.isfinite(prev) and (prev - inertia) / prev < TOL:
            return labels, curve, it
        prev = inertia
    return labels, curve, MAX_ITER


def ari(a: np.ndarray, b: np.ndarray) -> float:
    """Adjusted Rand Index (pure python; scipy absent per declared scope)."""
    n = len(a)
    tab = Counter(zip(map(int, a), map(int, b)))
    ra = Counter(map(int, a))
    rb = Counter(map(int, b))
    c2 = lambda x: x * (x - 1) // 2  # noqa: E731
    s_ij = sum(c2(v) for v in tab.values())
    s_a = sum(c2(v) for v in ra.values())
    s_b = sum(c2(v) for v in rb.values())
    tot = c2(n)
    expected = s_a * s_b / tot
    max_idx = (s_a + s_b) / 2
    if max_idx == expected:
        return 1.0
    return (s_ij - expected) / (max_idx - expected)


def tokenize(text: str) -> list[str]:
    return [w for w in "".join(
        ch.lower() if ch.isalpha() else " " for ch in text
    ).split() if len(w) >= 3 and w not in STOPWORDS]


def topic_terms(texts: list[str], labels: np.ndarray, k: int,
                top_n: int = 10, min_df: int = 20) -> dict:
    """S5: score(t,c) = (n_t,c / tokens_c) * ln(N / df_t)."""
    N = len(texts)
    df: Counter = Counter()
    tf_c: dict[int, Counter] = defaultdict(Counter)
    tok_c: Counter = Counter()
    for text, c in zip(texts, labels):
        toks = tokenize(text)
        tok_c[int(c)] += len(toks)
        for t in set(toks):
            df[t] += 1
        for t in toks:
            tf_c[int(c)][t] += 1
    out: dict[str, list] = {}
    for c in range(k):
        scores = {
            t: (n / max(tok_c[c], 1)) * math.log(N / df[t])
            for t, n in tf_c[c].items() if df[t] >= min_df
        }
        top = sorted(scores.items(), key=lambda kv: -kv[1])[:top_n]
        out[str(c)] = [{"term": t, "score": round(s, 6)} for t, s in top]
    return out


def discipline_shares(journal: list[str], tag: list[str],
                      labels: np.ndarray, k: int) -> dict:
    """S7: per-journal topic shares -> macro (equal journals) vs micro."""
    by_j: dict[str, Counter] = defaultdict(Counter)
    for j, c in zip(journal, labels):
        by_j[j][int(c)] += 1
    journals = sorted(by_j)
    sizes = {j: sum(by_j[j].values()) for j in journals}
    micro: dict[str, float] = {}
    macro: dict[str, float] = {}
    tag_of: dict[str, str] = {}
    for j, t in zip(journal, tag):
        tag_of[j] = t
    pooled = Counter()
    for j in journals:
        pooled.update(by_j[j])
    N = sum(pooled.values())
    tags = sorted(set(tag_of.values()))
    for c in range(k):
        micro[str(c)] = pooled[c] / N
        by_tag: dict[str, list[float]] = defaultdict(list)
        for j in journals:
            by_tag[tag_of[j]].append(by_j[j][c] / sizes[j])
        # macro over journals (each journal equal weight -> S7 primary)
        macro[str(c)] = sum(v for lst in by_tag.values() for v in lst) / len(journals)
    per_journal = {j: {str(c): round(by_j[j][c] / sizes[j], 5)
                       for c in range(k)} for j in journals}
    per_tag_macro: dict[str, dict] = {}
    for t in tags:
        members = [j for j in journals if tag_of[j] == t]
        per_tag_macro[t] = {
            str(c): round(sum(by_j[j][c] / sizes[j] for j in members) / len(members), 5)
            for c in range(k)
        }
    return {"micro_topic_share": micro, "macro_topic_share": macro,
            "per_journal_topic_share": per_journal,
            "per_tag_macro_topic_share": per_tag_macro}


def network_metrics() -> dict:
    """S6: deterministic metrics from journal_matrix.csv + edges (Gate B)."""
    with (PROC / "journal_matrix.csv").open(encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    order = rows[0][1:]
    M = np.array([[int(x) for x in r[1:]] for r in rows[1:]], dtype=np.int64)
    slug_tag: dict[str, str] = {}
    with (PROC / "works.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            slug_tag[row["journal"]] = row["tag"]
    tags = sorted(set(slug_tag.values()))
    per_journal = {}
    for i, s in enumerate(order):
        row = M[i]
        total = int(row.sum())
        p = row / max(total, 1)
        nz = p[p > 0]
        ent = float(-(nz * np.log(nz)).sum() / math.log(len(order)))
        # discipline-aggregated out distribution
        dist = {t: 0 for t in tags}
        for j2, s2 in enumerate(order):
            dist[slug_tag[s2]] += int(M[i, j2])
        pd_ = {t: dist[t] / max(sum(dist.values()), 1) for t in tags}
        nz2 = [v for v in pd_.values() if v > 0]
        ent8 = float(-(np.array(nz2) * np.log(np.array(nz2))).sum() / math.log(len(tags)))
        same_tag = sum(int(M[i, j2]) for j2, s2 in enumerate(order)
                       if slug_tag[s2] == slug_tag[s])
        per_journal[s] = {
            "out_total": total,
            "in_total": int(M[:, i].sum()),
            "self_cite_share": round(float(row[i]) / max(total, 1), 4),
            "same_tag_share": round(same_tag / max(total, 1), 4),
            "cross_tag_share": round(1 - same_tag / max(total, 1), 4),
            "entropy_norm_15": round(ent, 4),
            "entropy_norm_8tag": round(ent8, 4),
        }
    # micro vs macro cross-tag share (S7)
    cross_micro = 1 - sum(v["same_tag_share"] * v["out_total"]
                          for v in per_journal.values()) / max(
        sum(v["out_total"] for v in per_journal.values()), 1)
    cross_macro = float(np.mean([v["cross_tag_share"] for v in per_journal.values()]))
    return {"per_journal": per_journal,
            "cross_tag_share_micro": round(float(cross_micro), 4),
            "cross_tag_share_macro": round(cross_macro, 4),
            "journal_order": order}


def main() -> int:
    t_start = time.time()
    W = load_works()
    n = len(W["ids"])
    print(f"[load] works={n}", flush=True)
    if n != 14333:
        raise SystemExit(f"unexpected corpus size {n} (Gate C fail)")

    X, model_info = embed(W["texts"])            # S2
    Z = pca_l2(X, PCA_DIM)                       # S3
    runs: dict[str, dict] = {}
    curves: dict[str, list[float]] = {}
    labels_by_seed: dict[int, np.ndarray] = {}

    # ---- S4: primary k=20 across 3 seeds ----
    for s in SEEDS:
        t0 = time.time()
        lab, curve, n_it = lloyd(Z, K, s)
        dt = time.time() - t0
        labels_by_seed[s] = lab
        sizes = Counter(map(int, lab))
        runs[f"k{K}_seed{s}"] = {
            "wall_s": round(dt, 2), "n_iter": n_it,
            "inertia_first": round(curve[0], 2),
            "inertia_final": round(curve[-1], 2),
            "sizes": {str(c): int(sizes.get(c, 0)) for c in range(K)},
        }
        curves[f"k{K}_seed{s}"] = [round(v, 2) for v in curve]
        print(f"[kmeans] k={K} seed={s} it={n_it} inertia {curve[0]:.0f}->{curve[-1]:.0f} "
              f"wall={dt:.1f}s", flush=True)

    ari_seeds = {}
    for i, si in enumerate(SEEDS):
        for sj in SEEDS[i + 1:]:
            ari_seeds[f"seed{si}_vs_seed{sj}"] = round(
                ari(labels_by_seed[si], labels_by_seed[sj]), 4)
    print(f"[ari] primary seed pairs: {ari_seeds}", flush=True)

    # ---- S4: k-sweep {15,25} at seed 1 ----
    sweep_labels: dict[int, np.ndarray] = {}
    ari_k = {}
    for kk in K_SWEEP:
        t0 = time.time()
        lab_k, curve_k, n_it = lloyd(Z, kk, 1)
        dt = time.time() - t0
        sweep_labels[kk] = lab_k
        ari_k[str(kk)] = round(ari(labels_by_seed[1], lab_k), 4)
        runs[f"k{kk}_seed1"] = {"wall_s": round(dt, 2), "n_iter": n_it,
                                "inertia_final": round(curve_k[-1], 2)}
        curves[f"k{kk}_seed1"] = [round(v, 2) for v in curve_k]
        print(f"[kmeans] k={kk} seed=1 it={n_it} inertia={curve_k[-1]:.0f} "
              f"wall={dt:.1f}s ARI_vs_k20={ari_k[str(kk)]}", flush=True)

    # ---- S8: abstract-only sensitivity (reuses deterministic embeddings) ----
    mask = np.array([s == "abstract" for s in W["source"]])
    idx = np.where(mask)[0]
    Zs = pca_l2(X[idx], PCA_DIM)
    lab_s, curve_s, n_it_s = lloyd(Zs, K, 1)
    ari_sens = round(ari(labels_by_seed[1][idx], lab_s), 4)
    runs["sensitivity_abstract_only"] = {
        "n_docs": int(idx.size), "n_iter": n_it_s,
        "inertia_final": round(curve_s[-1], 2), "ari_vs_full_seed1": ari_sens,
        "threshold_for_concern": 0.60,
        "verdict": "PASS" if ari_sens >= 0.60 else "CONCERN"}
    print(f"[sens] abstract-only n={idx.size} ARI_vs_full_seed1={ari_sens} "
          f"({'PASS' if ari_sens >= 0.60 else 'CONCERN'}, threshold 0.60)", flush=True)

    # ---- S5 terms, S7 shares, S6 network ----
    terms = topic_terms(W["texts"], labels_by_seed[1], K)
    shares = discipline_shares(W["journal"], W["tag"], labels_by_seed[1], K)
    net = network_metrics()
    sizes1 = Counter(map(int, labels_by_seed[1]))
    print("[topics] primary seed=1:", flush=True)
    for c in range(K):
        tlist = ",".join(t["term"] for t in terms[str(c)][:6])
        print(f"  T{c:02d} n={sizes1[c]:5d}: {tlist}", flush=True)
    print(f"[net] cross_tag_share micro={net['cross_tag_share_micro']} "
          f"macro={net['cross_tag_share_macro']}", flush=True)
    for s, v in net["per_journal"].items():
        print(f"  {s:16s} out={v['out_total']:5d} in={v['in_total']:5d} "
              f"self={v['self_cite_share']:.3f} cross_tag={v['cross_tag_share']:.3f} "
              f"H8={v['entropy_norm_8tag']:.3f}", flush=True)

    # ---- assignments ----
    with (PROC / "gatec_assignments.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "year", "journal", "tag", "source",
                    "cluster_seed1", "cluster_seed2", "cluster_seed3",
                    "cluster_k15_s1", "cluster_k25_s1"])
        for i in range(n):
            w.writerow([W["ids"][i], W["year"][i], W["journal"][i], W["tag"][i],
                        W["source"][i], labels_by_seed[1][i], labels_by_seed[2][i],
                        labels_by_seed[3][i], sweep_labels[15][i],
                        sweep_labels[25][i]])

    total_s = round(time.time() - t_start, 1)
    out = {"model_used": model_info, "k": K, "seeds": SEEDS,
           "pca_dim": PCA_DIM, "total_wall_s": total_s,
           "runs": runs, "inertia_curves": curves,
           "ari_seed_pairs": ari_seeds, "ari_k_sweep_vs_k20_seed1": ari_k,
           "sensitivity_abstract_only": runs["sensitivity_abstract_only"],
           "topic_terms_seed1": terms,
           "sizes_seed1": {str(c): int(sizes1[c]) for c in range(K)},
           "shares_S7": shares, "network_S6": net}
    (PROC / "gatec_runs.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (PROC / "gatec_topics.json").write_text(
        json.dumps({"model": model_info, "terms": terms,
                    "sizes": out["sizes_seed1"]}, indent=2), encoding="utf-8")
    print(f"[done] total wall={total_s}s -> gatec_runs.json, gatec_topics.json, "
          f"gatec_assignments.csv", flush=True)
    return 0


if __name__ == "__main__":
    # os._exit: ONNX/tokenizers native threads may block interpreter exit
    # (observed hangs with CPU=0 on this host); exit code must not be masked.
    try:
        _code = main()
    except BaseException:  # noqa: BLE001 — report real traceback, then die
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_code)

