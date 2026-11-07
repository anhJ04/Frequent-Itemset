#!/usr/bin/env python3
"""Chạy các thí nghiệm theo yêu cầu đồ án và xuất CSV + biểu đồ vào results/.

  python experiments.py data/retail.txt --name retail \
      --minsups 0.05 0.03 0.02 0.01 0.005 --mid-minsup 0.02

Thí nghiệm:
  1. runtime_vs_minsup      : thời gian chạy theo minsup (basic vs optimized)
  2. count_vs_minsup        : số frequent itemset theo minsup
  3. memory                 : peak RAM (tracemalloc) tại minsup trung bình
  4. scalability            : thời gian theo kích thước CSDL 10/25/50/75/100%
  5. (tùy chọn) --length-exp: ảnh hưởng độ dài giao dịch trung bình (CSDL tổng hợp)

Lưu ý: thêm đường cong SPMF vào đồ thị bằng cách chạy SPMF riêng, ghi thời gian vào
results/<name>_spmf_time.csv (cột minsup,time) - script sẽ tự vẽ nếu file tồn tại.
"""
import argparse
import csv
import os
import time
import tracemalloc

from apriori_fim import (apriori_basic, apriori_optimized, read_transactions,
                         resolve_minsup)
from gen_data import generate

ALGOS = {"basic": apriori_basic, "optimized": apriori_optimized}


def timed(fn, tx, minsup_abs, timeout_note=None):
    t0 = time.perf_counter()
    res = fn(tx, minsup_abs)
    return time.perf_counter() - t0, res


def peak_mem(fn, tx, minsup_abs):
    tracemalloc.start()
    fn(tx, minsup_abs)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak / 2**20


def save_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  ->", path)


def try_plot():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        print("(matplotlib chưa cài -> bỏ qua vẽ biểu đồ, vẫn có CSV)")
        return None


def read_spmf_times(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        r = csv.DictReader(f)
        return [(float(x["minsup"]), float(x["time"])) for x in r]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--name", default=None)
    ap.add_argument("--delimiter", default=None)
    ap.add_argument("--minsups", type=float, nargs="+", default=[0.05, 0.03, 0.02, 0.01, 0.005],
                    help="5-7 giá trị minsup giảm dần")
    ap.add_argument("--mid-minsup", type=float, default=None, help="minsup cho thí nghiệm bộ nhớ/scalability")
    ap.add_argument("--skip-basic-below", type=float, default=0.0,
                    help="bỏ qua bản basic khi minsup nhỏ hơn ngưỡng này (basic rất chậm)")
    ap.add_argument("--length-exp", action="store_true", help="chạy thí nghiệm độ dài giao dịch")
    ap.add_argument("--outdir", default="results")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    name = a.name or os.path.splitext(os.path.basename(a.input))[0]
    tx = read_transactions(a.input, a.delimiter)
    N = len(tx)
    minsups = sorted(a.minsups, reverse=True)
    mid = a.mid_minsup or minsups[len(minsups) // 2]
    plt = try_plot()
    print(f"[{name}] {N} giao dịch")

    # 1 + 2: runtime & count vs minsup
    print("\n[1,2] runtime / count theo minsup")
    rows = []
    for ms in minsups:
        abs_ms = resolve_minsup(ms, N)
        row = {"minsup": ms}
        for an, fn in ALGOS.items():
            if an == "basic" and ms < a.skip_basic_below:
                row[an] = ""
                continue
            t, res = timed(fn, tx, abs_ms)
            row[an] = round(t, 4)
            row["count"] = len(res)
        rows.append(row)
        print(f"  minsup={ms}: basic={row['basic']}s optimized={row['optimized']}s count={row['count']}")
    save_csv(f"{a.outdir}/{name}_runtime_count.csv", ["minsup", "basic_s", "optimized_s", "count"],
             [[r["minsup"], r["basic"], r["optimized"], r["count"]] for r in rows])

    # 3: memory
    print(f"\n[3] peak memory tại minsup={mid}")
    abs_mid = resolve_minsup(mid, N)
    mem = {an: round(peak_mem(fn, tx, abs_mid), 2) for an, fn in ALGOS.items()}
    print("  ", mem, "MiB")
    save_csv(f"{a.outdir}/{name}_memory.csv", ["algo", "peak_MiB"], list(mem.items()))

    # 4: scalability
    print(f"\n[4] scalability tại minsup={mid}")
    srows = []
    for pct in (10, 25, 50, 75, 100):
        sub = tx[: max(1, N * pct // 100)]
        ms_abs = resolve_minsup(mid, len(sub))
        r = [pct]
        for an, fn in ALGOS.items():
            t, _ = timed(fn, sub, ms_abs)
            r.append(round(t, 4))
        srows.append(r)
        print(f"  {pct}%: basic={r[1]}s optimized={r[2]}s")
    save_csv(f"{a.outdir}/{name}_scalability.csv", ["size_pct", "basic_s", "optimized_s"], srows)

    # 5: transaction length
    lrows = []
    if a.length_exp:
        print("\n[5] ảnh hưởng độ dài giao dịch (CSDL tổng hợp 3000 giao dịch, 150 item)")
        for L in (5, 8, 10, 12, 15):
            syn = generate(3000, 150, L)
            ms_abs = resolve_minsup(0.05, len(syn))
            r = [L]
            for an, fn in ALGOS.items():
                t, _ = timed(fn, syn, ms_abs)
                r.append(round(t, 4))
            lrows.append(r)
            print(f"  avg_len={L}: basic={r[1]}s optimized={r[2]}s")
        save_csv(f"{a.outdir}/{name}_length.csv", ["avg_len", "basic_s", "optimized_s"], lrows)

    # Vẽ biểu đồ
    if plt:
        spmf = read_spmf_times(f"{a.outdir}/{name}_spmf_time.csv")
        fig, ax = plt.subplots(figsize=(6, 4))
        for an in ALGOS:
            pts = [(r["minsup"], r[an]) for r in rows if r[an] != ""]
            ax.plot(*zip(*pts), marker="o", label=an)
        if spmf:
            ax.plot(*zip(*spmf), marker="s", linestyle="--", label="SPMF")
        ax.set_xlabel("minsup"); ax.set_ylabel("thời gian (s)"); ax.set_yscale("log")
        ax.invert_xaxis(); ax.legend(); ax.set_title(f"Runtime vs minsup - {name}")
        fig.tight_layout(); fig.savefig(f"{a.outdir}/{name}_runtime.png", dpi=150); plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot([r["minsup"] for r in rows], [r["count"] for r in rows], marker="o")
        ax.set_xlabel("minsup"); ax.set_ylabel("số frequent itemset"); ax.set_yscale("log")
        ax.invert_xaxis(); ax.set_title(f"Output size vs minsup - {name}")
        fig.tight_layout(); fig.savefig(f"{a.outdir}/{name}_count.png", dpi=150); plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        for i, an in enumerate(ALGOS, start=1):
            ax.plot([r[0] for r in srows], [r[i] for r in srows], marker="o", label=an)
        ax.set_xlabel("kích thước CSDL (%)"); ax.set_ylabel("thời gian (s)")
        ax.legend(); ax.set_title(f"Scalability - {name}")
        fig.tight_layout(); fig.savefig(f"{a.outdir}/{name}_scalability.png", dpi=150); plt.close(fig)

        if lrows:
            fig, ax = plt.subplots(figsize=(6, 4))
            for i, an in enumerate(ALGOS, start=1):
                ax.plot([r[0] for r in lrows], [r[i] for r in lrows], marker="o", label=an)
            ax.set_xlabel("độ dài giao dịch TB"); ax.set_ylabel("thời gian (s)")
            ax.legend(); ax.set_title("Ảnh hưởng độ dài giao dịch")
            fig.tight_layout(); fig.savefig(f"{a.outdir}/{name}_length.png", dpi=150); plt.close(fig)
        print(f"\nĐã lưu biểu đồ PNG vào {a.outdir}/")


if __name__ == "__main__":
    main()
