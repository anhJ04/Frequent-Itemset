#!/usr/bin/env python3
"""Vẽ biểu đồ + xuất bảng LaTeX từ CSV của run_experiments.py.

    python bench/plot_results.py                 # đọc results/exp/, ghi results/exp/fig/
    python bench/plot_results.py --dir results/exp

Cần matplotlib. Mỗi hình được lưu cả .pdf (chèn vào báo cáo LaTeX) và .png (README/notebook).
"""
import argparse
import csv
import json
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Bảng màu categorical đã kiểm tra mù màu (thứ tự cố định); marker riêng = mã hoá phụ
STYLE = {
    "spmf":      {"color": "#2a78d6", "marker": "o", "ls": "--", "label": "SPMF (Java)"},
    "basic":     {"color": "#eb6834", "marker": "s", "ls": "-", "label": "Apriori cơ bản"},
    "optimized": {"color": "#1baf7a", "marker": "^", "ls": "-", "label": "Apriori-BitVector"},
    "tid":       {"color": "#eda100", "marker": "D", "ls": "-", "label": "AprioriTid"},
    "hybrid":    {"color": "#e87ba4", "marker": "v", "ls": "-", "label": "AprioriHybrid"},
}
ORDER = ["spmf", "basic", "optimized", "tid", "hybrid"]
DS_LABEL = {"chess": "Chess", "mushrooms": "Mushroom", "retail": "Retail",
            "T10I4D100K": "T10I4D100K", "synthetic": "Tổng hợp"}

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#e4e3df", "grid.linewidth": 0.6, "axes.edgecolor": "#8a8984",
    "lines.linewidth": 1.6, "lines.markersize": 5, "savefig.dpi": 200,
    "savefig.bbox": "tight",
})


def read(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def save(fig, out, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out, f"{name}.{ext}"))
    plt.close(fig)
    print("  ->", name)


def series(rows, key="time"):
    """{algo: [(x, y)]} chỉ lấy các lần chạy ok."""
    s = defaultdict(list)
    for r in rows:
        if r["status"] == "ok" and num(r.get(key)) is not None:
            s[r["algo"]].append((float(r["x"]), float(r[key])))
    return {a: sorted(v) for a, v in s.items()}


def draw_lines(ax, s, logy=True):
    for a in ORDER:
        if a in s:
            st = STYLE[a]
            xs, ys = zip(*s[a])
            ax.plot(xs, ys, color=st["color"], marker=st["marker"], ls=st["ls"],
                    label=st["label"], markeredgecolor="white", markeredgewidth=0.6)
    if logy:
        ax.set_yscale("log")


def grid(n):
    cols = 2 if n > 1 else 1
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(3.4 * cols, 2.6 * rows), squeeze=False)
    return fig, axes.flatten()


def shared_legend(fig, axes):
    seen = {}
    for ax in axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            seen.setdefault(l, h)
    fig.legend(seen.values(), seen.keys(), loc="lower center", ncol=min(5, len(seen)),
               frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.06, 1, 1))


def plot_alloc(rows, out):
    """Tổng bộ nhớ cấp phát (Julia @timed) theo minsup — chỉ các biến thể của nhóm."""
    by_ds = defaultdict(list)
    for r in rows:
        if r["algo"] != "spmf":
            by_ds[r["dataset"]].append(r)
    if not by_ds:
        return
    fig, axes = grid(len(by_ds))
    for ax, (ds, rs) in zip(axes, by_ds.items()):
        draw_lines(ax, series(rs, key="alloc_mb"))
        ax.invert_xaxis()
        ax.set_title(DS_LABEL.get(ds, ds))
        ax.set_xlabel("minsup (tỉ lệ)")
        ax.set_ylabel("Bộ nhớ cấp phát (MB, log)")
    for ax in axes[len(by_ds):]:
        ax.axis("off")
    shared_legend(fig, axes)
    save(fig, out, "alloc_vs_minsup")


def plot_runtime(rows, out, cap):
    by_ds = defaultdict(list)
    for r in rows:
        by_ds[r["dataset"]].append(r)
    if not by_ds:
        return
    fig, axes = grid(len(by_ds))
    for ax, (ds, rs) in zip(axes, by_ds.items()):
        draw_lines(ax, series(rs))
        ax.invert_xaxis()                         # minsup giảm dần từ trái sang phải
        ax.set_title(DS_LABEL.get(ds, ds))
        ax.set_xlabel("minsup (tỉ lệ)")
        ax.set_ylabel("Thời gian (s, log)")
    for ax in axes[len(by_ds):]:
        ax.axis("off")
    shared_legend(fig, axes)
    save(fig, out, "runtime_vs_minsup")


def plot_count(rows, out):
    """Số itemset theo minsup: lấy count của SPMF (hoặc thuật toán nhóm nếu không có SPMF)."""
    by_ds = defaultdict(dict)
    for r in rows:
        if r["status"] == "ok":
            by_ds[r["dataset"]].setdefault(float(r["x"]), (int(float(r["count"])),
                                                           num(r["max_k"])))
    if not by_ds:
        return
    fig, axes = grid(len(by_ds))
    for ax, (ds, pts) in zip(axes, by_ds.items()):
        xs = sorted(pts)
        ax.plot(xs, [max(pts[x][0], 1) for x in xs], color="#2a78d6", marker="o",
                markeredgecolor="white", markeredgewidth=0.6)
        ax.set_yscale("log")
        ax.invert_xaxis()
        dense = ds in ("chess", "mushrooms")
        ax.set_title(f"{DS_LABEL.get(ds, ds)} ({'dày' if dense else 'thưa'})")
        ax.set_xlabel("minsup (tỉ lệ)")
        ax.set_ylabel("Số frequent itemset (log)")
        lo = xs[0]
        ax.annotate(f"{pts[lo][0]:,}", (lo, pts[lo][0]), textcoords="offset points",
                    xytext=(-4, 4), ha="right", fontsize=7, color="#52514d")
    for ax in axes[len(by_ds):]:
        ax.axis("off")
    fig.tight_layout()
    save(fig, out, "count_vs_minsup")


def plot_memory(rows, out, mids):
    data = defaultdict(dict)                     # ds -> algo -> peak MB
    for r in rows:
        ds = r["dataset"]
        if (r["status"] == "ok" and ds in mids and abs(float(r["x"]) - mids[ds]) < 1e-9
                and num(r["rss_peak_mb"]) is not None):
            peak = float(r["rss_peak_mb"])
            base = num(r.get("rss_before_mb"))
            # Julia: phần RAM tăng thêm khi chạy thuật toán (trừ runtime + CSDL đã nạp);
            # SPMF: bộ nhớ JVM do chính SPMF báo cáo
            data[ds][r["algo"]] = peak - base if (base is not None and r["algo"] != "spmf") else peak
    if not data:
        return
    algos = [a for a in ORDER if any(a in d for d in data.values())]
    dss = list(data)
    fig, ax = plt.subplots(figsize=(6.8, 2.8))
    w = 0.8 / len(algos)
    for i, a in enumerate(algos):
        xs = [j + (i - (len(algos) - 1) / 2) * w for j in range(len(dss))]
        ys = [data[d].get(a, 0) for d in dss]
        ax.bar(xs, ys, width=w * 0.92, color=STYLE[a]["color"], label=STYLE[a]["label"])
    ax.set_xticks(range(len(dss)))
    ax.set_xticklabels([f"{DS_LABEL.get(d, d)}\nminsup={mids[d]:g}" for d in dss])
    ax.set_ylabel("Peak RAM tăng thêm (MB)")
    ax.grid(axis="x", visible=False)
    ax.legend(ncol=len(algos), frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.18))
    save(fig, out, "memory_peak")


def plot_xy(rows, out, name, xlabel, title, logy=True, xfmt=None):
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    s = series(rows)
    draw_lines(ax, s, logy=logy)
    if xfmt:
        xs = sorted({x for v in s.values() for x, _ in v})
        ax.set_xticks(xs)
        ax.set_xticklabels([xfmt(x) for x in xs])
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Thời gian (s" + (", log)" if logy else ")"))
    ax.set_title(title)
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    save(fig, out, name)


def plot_length(rows, out):
    if not rows:
        return
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 2.6))
    draw_lines(a1, series(rows))
    a1.set_xlabel("Độ dài giao dịch trung bình")
    a1.set_ylabel("Thời gian (s, log)")
    a1.set_title("Thời gian chạy")
    cnt = {}
    for r in rows:
        if r["status"] == "ok":
            cnt.setdefault(float(r["x"]), int(float(r["count"])))
    xs = sorted(cnt)
    a2.plot(xs, [cnt[x] for x in xs], color="#2a78d6", marker="o",
            markeredgecolor="white", markeredgewidth=0.6)
    a2.set_yscale("log")
    a2.set_xlabel("Độ dài giao dịch trung bình")
    a2.set_ylabel("Số frequent itemset (log)")
    a2.set_title("Kích thước đầu ra")
    shared_legend(fig, [a1])
    save(fig, out, "length_effect")


# ---------------------------------------------------------------- bảng LaTeX
def tex_correctness(corr, out):
    if not corr:
        return
    lines = [r"\begin{tabular}{llrrrr}", r"\toprule",
             r"CSDL & minsup & SPMF & Nhóm & Khớp & Tỉ lệ \\", r"\midrule"]
    agg = defaultdict(lambda: [0, 0, 0, 0])      # (ds, minsup) -> lấy bản hybrid làm đại diện
    for r in corr:
        if r["algo"] != "hybrid":
            continue
        lines.append(f"{DS_LABEL.get(r['dataset'], r['dataset'])} & {float(r['minsup']):g} & "
                     f"{int(r['spmf_count']):,} & {int(r['our_count']):,} & "
                     f"{int(r['exact']):,} & {100 * float(r['match_rate']):.2f}\\% \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(out, "correctness_table.tex"), "w") as f:
        f.write("\n".join(lines).replace(",", "{,}"))
    total = len(corr)
    ok = sum(1 for r in corr if float(r["match_rate"]) == 1.0)
    print(f"  correctness: {ok}/{total} lần so sánh khớp 100% (mọi thuật toán)")


def tex_runtime(rows, out):
    by = defaultdict(dict)
    for r in rows:
        key = (r["dataset"], float(r["x"]))
        by[key][r["algo"]] = (f"{float(r['time']):.2f}" if r["status"] == "ok"
                              else ("TO" if r["status"] in ("timeout", "skipped") else "--"))
        if r["status"] == "ok":
            by[key]["count"] = int(float(r["count"]))
    if not by:
        return
    algos = [a for a in ORDER if any(a in v for v in by.values())]
    short = {"spmf": "SPMF", "basic": "Basic", "optimized": "BitVector", "tid": "Tid",
             "hybrid": "Hybrid"}
    head = " & ".join(short[a] for a in algos)
    lines = [r"\begin{tabular}{ll r" + "r" * len(algos) + "}", r"\toprule",
             f"CSDL & minsup & \\#itemset & {head} \\\\", r"\midrule"]
    for (ds, x) in sorted(by, key=lambda k: (k[0], -k[1])):
        v = by[(ds, x)]
        cells = " & ".join(v.get(a, "--") for a in algos)
        lines.append(f"{DS_LABEL.get(ds, ds)} & {x:g} & {v.get('count', '--'):,} & {cells} \\\\"
                     if isinstance(v.get("count"), int) else
                     f"{DS_LABEL.get(ds, ds)} & {x:g} & -- & {cells} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(out, "runtime_table.tex"), "w") as f:
        f.write("\n".join(lines).replace(",", "{,}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(ROOT, "results", "exp"))
    a = ap.parse_args()
    out = os.path.join(a.dir, "fig")
    os.makedirs(out, exist_ok=True)
    cfg = {}
    if os.path.exists(os.path.join(a.dir, "config.json")):
        cfg = json.load(open(os.path.join(a.dir, "config.json")))
    mids = {d: v["mid"] for d, v in cfg.get("datasets", {}).items()}

    rt = read(os.path.join(a.dir, "runtime.csv"))
    plot_runtime(rt, out, cfg.get("cap"))
    plot_count(rt, out)
    plot_alloc(rt, out)
    plot_memory(rt, out, mids)
    sc = read(os.path.join(a.dir, "scalability.csv"))
    plot_xy(sc, out, "scalability", "Tỉ lệ giao dịch của CSDL",
            f"Scalability ({DS_LABEL.get(sc[0]['dataset'], '') if sc else ''}, "
            f"minsup={float(sc[0]['minsup']):g})" if sc else "", logy=False,
            xfmt=lambda x: f"{x:.0%}")
    plot_length(read(os.path.join(a.dir, "length.csv")), out)
    tex_correctness(read(os.path.join(a.dir, "correctness.csv")), out)
    tex_runtime(rt, out)
    print("Xong:", out)


if __name__ == "__main__":
    main()
