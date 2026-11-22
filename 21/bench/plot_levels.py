#!/usr/bin/env python3
"""Vẽ số tập phổ biến theo kích thước k từ các file *_stat.txt do run_cli.jl sinh ra.

    python bench/plot_levels.py results/chess_hybrid_0.8_stat.txt results/mushrooms_hybrid_0.2_stat.txt ...
"""
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
MARKERS = ["o", "s", "^", "D"]


def parse(path):
    txt = open(path, encoding="utf-8").read()
    ds = re.search(r"Dataset:\s*(\S+)", txt).group(1)
    ms = re.search(r"Minsup tương đối:\s*([\d.]+)", txt).group(1)
    ks = [(int(k), int(v)) for k, v in re.findall(r"k = (\d+): (\d+)", txt)]
    return f"{ds} (minsup {ms})", ks


def main(paths):
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    for i, p in enumerate(paths):
        label, ks = parse(p)
        xs, ys = zip(*ks)
        ax.plot(xs, ys, color=COLORS[i % 4], marker=MARKERS[i % 4], label=label, lw=1.6, ms=5,
                markeredgecolor="white", markeredgewidth=0.6)
    ax.set_yscale("log")
    ax.set_xlabel("Kích thước itemset k")
    ax.set_ylabel("|L_k| (log)")
    ax.grid(color="#e4e3df", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    out = os.path.join("results", "exp", "fig", "levels")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(f"{out}.{ext}", dpi=200, bbox_inches="tight")
    print("->", out)


if __name__ == "__main__":
    main(sys.argv[1:])
