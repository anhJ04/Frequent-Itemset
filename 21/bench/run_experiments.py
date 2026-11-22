#!/usr/bin/env python3
"""Chạy toàn bộ thực nghiệm Chương 2 và ghi CSV vào results/exp/.

Chạy từ thư mục gốc của project (nơi có Project.toml):

    python bench/run_experiments.py                       # đầy đủ: 4 dataset + SPMF
    python bench/run_experiments.py --no-spmf             # không có Java/SPMF
    python bench/run_experiments.py --datasets chess mushrooms --cap 60
    python bench/run_experiments.py --exps runtime        # chỉ chạy một thí nghiệm

Thí nghiệm (--exps):
  runtime : thời gian + số itemset + bộ nhớ theo minsup, kèm kiểm tra correctness với SPMF
  scal    : scalability, các tập con 10/25/50/75/100% của Retail (lấy mẫu với seed 42)
  length  : ảnh hưởng của độ dài giao dịch trung bình (CSDL tổng hợp, seed 42)

Mỗi lần đo chạy trong một tiến trình Julia riêng (bench/run_one.jl) để đo peak RAM chính xác.
Nếu một lần chạy vượt --cap giây, lần đó bị dừng và các minsup thấp hơn của cùng thuật toán
được đánh dấu "skipped" (minsup thấp hơn chắc chắn chạy lâu hơn).
Chỉ dùng thư viện chuẩn của Python.
"""
import argparse
import csv
import json
import math
import os
import random
import re
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from gen_data import generate  # noqa: E402

# minsup giảm dần; "mid" là minsup trung bình dùng cho biểu đồ bộ nhớ
DATASETS = {
    "chess":      {"minsups": [0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60], "mid": 0.80},
    "mushrooms":  {"minsups": [0.50, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15], "mid": 0.30},
    "retail":     {"minsups": [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005], "mid": 0.02},
    "T10I4D100K": {"minsups": [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005], "mid": 0.02},
}
FIELDS = ["exp", "dataset", "x", "algo", "minsup", "minsup_abs", "n", "avg_len", "count",
          "max_k", "time", "alloc_mb", "rss_before_mb", "rss_peak_mb", "status"]
CORR_FIELDS = ["dataset", "minsup", "algo", "spmf_count", "our_count", "exact", "missing",
               "extra", "wrong_support", "match_rate"]


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


# ---------------------------------------------------------------- chạy một lần đo
def run_julia(args, inp, minsup, algo, out_path):
    cmd = [args.julia, f"--project={ROOT}", os.path.join(ROOT, "bench", "run_one.jl"),
           inp, repr(minsup), algo] + ([out_path] if out_path else [])
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=args.cap, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
    if p.returncode != 0 or not lines:
        log("  LỖI Julia:", (p.stderr or p.stdout)[-800:])
        return {"status": "error"}
    r = json.loads(lines[-1])
    r["status"] = "ok"
    return r


def run_spmf(args, inp, minsup, out_path, n):
    cmd = [args.java, f"-Xmx{args.java_mem}", "-jar", args.spmf, "run", "Apriori",
           inp, out_path, f"{minsup * 100:g}%"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=args.cap)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    txt = p.stdout + p.stderr
    t = re.search(r"Total time ~?\s*([\d.]+)\s*ms", txt)
    c = re.search(r"Frequent itemsets count\s*:\s*(\d+)", txt)
    m = re.search(r"Maximum memory usage\s*:\s*([\d.]+)\s*mb", txt)
    if not (t and c):
        log("  LỖI SPMF:", txt[-800:])
        return {"status": "error"}
    return {"status": "ok", "algo": "spmf", "time": float(t.group(1)) / 1000,
            "count": int(c.group(1)), "rss_peak_mb": float(m.group(1)) if m else "",
            "minsup_abs": math.ceil(minsup * n), "n": n}


# ---------------------------------------------------------------- correctness
def load_itemsets(path):
    d = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("@"):
                continue
            items, _, sup = line.partition("#SUP:")
            d[tuple(sorted(map(int, items.split())))] = int(sup)
    return d


def compare(ref_path, mine_path):
    ref, mine = load_itemsets(ref_path), load_itemsets(mine_path)
    exact = sum(1 for k, v in ref.items() if mine.get(k) == v)
    missing = sum(1 for k in ref if k not in mine)
    extra = sum(1 for k in mine if k not in ref)
    wrong = len(ref) - exact - missing
    denom = len(ref) + extra
    return {"spmf_count": len(ref), "our_count": len(mine), "exact": exact,
            "missing": missing, "extra": extra, "wrong_support": wrong,
            "match_rate": round(exact / denom, 6) if denom else 1.0}


# ---------------------------------------------------------------- tiện ích CSV
class Writer:
    def __init__(self, path, fields):
        new = not os.path.exists(path)
        self.f = open(path, "a", newline="")
        self.w = csv.DictWriter(self.f, fieldnames=fields, extrasaction="ignore")
        if new:
            self.w.writeheader()

    def row(self, d):
        self.w.writerow(d)
        self.f.flush()


def count_lines(path):
    with open(path) as f:
        return sum(1 for l in f if l.strip())


def sweep(args, w, exp, dataset, points, algos, corr=None):
    """points: list (x, input_path, minsup) theo thứ tự 'dễ -> khó'."""
    dead = set()                                # thuật toán đã timeout ở điểm dễ hơn
    for x, inp, ms in points:
        n = count_lines(inp)
        spmf_out = None
        for algo in algos:
            base = {"exp": exp, "dataset": dataset, "x": x, "algo": algo, "minsup": ms}
            if algo in dead:
                w.row({**base, "status": "skipped"})
                continue
            out = tempfile.mktemp(suffix=".txt", dir=args.tmp) if corr else None
            r = (run_spmf(args, inp, ms, out or os.devnull, n) if algo == "spmf"
                 else run_julia(args, inp, ms, algo, out))
            w.row({**base, **r, "exp": exp, "x": x, "algo": algo})
            msg = (f"{r.get('count')} itemsets, {r.get('time')} s" if r["status"] == "ok"
                   else r["status"])
            log(f"  {exp:7} {dataset:11} x={x:<7} {algo:9} -> {msg}")
            if r["status"] != "ok":
                dead.add(algo)
            if not corr:
                continue
            if algo == "spmf":
                spmf_out = out if r["status"] == "ok" else None
                continue
            if r["status"] == "ok" and spmf_out:
                c = compare(spmf_out, out)
                corr.row({"dataset": dataset, "minsup": ms, "algo": algo, **c})
                if c["match_rate"] < 1:
                    log(f"    !! {algo} khớp {c['match_rate']:.4%} (thiếu {c['missing']}, "
                        f"thừa {c['extra']}, sai support {c['wrong_support']})")
            if out and os.path.exists(out):
                os.remove(out)
        if spmf_out and os.path.exists(spmf_out):
            os.remove(spmf_out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", nargs="+", default=list(DATASETS))
    ap.add_argument("--algos", nargs="+", default=["basic", "optimized", "tid", "hybrid"])
    ap.add_argument("--exps", nargs="+", default=["runtime", "scal", "length"])
    ap.add_argument("--cap", type=float, default=90, help="giới hạn giây cho mỗi lần chạy")
    ap.add_argument("--julia", default="julia")
    ap.add_argument("--java", default="java")
    ap.add_argument("--java-mem", default="4g")
    ap.add_argument("--spmf", default=os.path.join(ROOT, "tools", "spmf.jar"))
    ap.add_argument("--no-spmf", action="store_true")
    ap.add_argument("--scal-dataset", default="retail")
    ap.add_argument("--scal-minsup", type=float, default=0.01)
    ap.add_argument("--length-minsup", type=float, default=0.03)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "exp"))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    args.tmp = tempfile.mkdtemp(prefix="fim_")
    algos = ([] if args.no_spmf else ["spmf"]) + args.algos   # SPMF chạy trước để làm tham chiếu
    with open(os.path.join(args.out, "config.json"), "w") as f:
        json.dump({"datasets": {d: DATASETS[d] for d in args.datasets}, "algos": algos,
                   "cap": args.cap, "scal": [args.scal_dataset, args.scal_minsup],
                   "length_minsup": args.length_minsup, "seed": args.seed}, f, indent=2)
    bench = os.path.join(ROOT, "data", "benchmark")

    if "runtime" in args.exps:
        w = Writer(os.path.join(args.out, "runtime.csv"), FIELDS)
        corr = None if args.no_spmf else Writer(os.path.join(args.out, "correctness.csv"),
                                                CORR_FIELDS)
        for ds in args.datasets:
            log(f"== runtime: {ds}")
            inp = os.path.join(bench, ds + ".txt")
            pts = [(ms, inp, ms) for ms in DATASETS[ds]["minsups"]]
            sweep(args, w, "runtime", ds, pts, algos, corr)

    if "scal" in args.exps:
        log(f"== scalability: {args.scal_dataset} minsup={args.scal_minsup}")
        w = Writer(os.path.join(args.out, "scalability.csv"), FIELDS)
        with open(os.path.join(bench, args.scal_dataset + ".txt")) as f:
            rows = [l for l in f if l.strip()]
        rng = random.Random(args.seed)
        order = list(range(len(rows)))
        rng.shuffle(order)
        pts = []
        for frac in (0.10, 0.25, 0.50, 0.75, 1.00):
            keep = sorted(order[:round(frac * len(rows))])   # giữ thứ tự gốc
            p = os.path.join(args.tmp, f"scal_{frac}.txt")
            with open(p, "w") as f:
                f.writelines(rows[i] if rows[i].endswith("\n") else rows[i] + "\n"
                             for i in keep)
            pts.append((frac, p, args.scal_minsup))
        sweep(args, w, "scal", args.scal_dataset, pts, algos)

    if "length" in args.exps:
        log(f"== độ dài giao dịch: minsup={args.length_minsup}")
        w = Writer(os.path.join(args.out, "length.csv"), FIELDS)
        pts = []
        for L in (5, 10, 15, 20, 25):
            p = os.path.join(args.tmp, f"syn_len{L}.txt")
            with open(p, "w") as f:
                for r in generate(10000, 1000, L, seed=args.seed):
                    f.write(" ".join(map(str, r)) + "\n")
            pts.append((L, p, args.length_minsup))
        sweep(args, w, "length", "synthetic", pts, algos)

    log("Xong. CSV nằm trong", args.out)


if __name__ == "__main__":
    main()
