#!/usr/bin/env python3
"""Chạy Apriori trên một CSDL giao dịch.

Ví dụ:
  python run_apriori.py data/toy.txt --minsup 0.4
  python run_apriori.py data/retail.txt --minsup 0.02 --algo optimized -o results/retail_out.txt
  python run_apriori.py data/groceries.csv --delimiter , --minsup 0.01 --rules --minconf 0.3 --top 10
"""
import argparse
import time
import tracemalloc

from apriori_fim import (apriori_basic, apriori_optimized, generate_rules,
                         read_transactions, resolve_minsup, write_spmf)

ALGOS = {"basic": apriori_basic, "optimized": apriori_optimized}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("input", help="file CSDL giao dịch")
    ap.add_argument("--minsup", type=float, required=True,
                    help="<=1: tỉ lệ (0.02 = 2%%); >1: số giao dịch tuyệt đối")
    ap.add_argument("--algo", choices=ALGOS, default="optimized")
    ap.add_argument("--delimiter", default=None, help="ví dụ ',' cho CSV (mặc định: khoảng trắng)")
    ap.add_argument("--max-len", type=int, default=None, help="giới hạn kích thước itemset")
    ap.add_argument("-o", "--output", help="ghi kết quả theo định dạng SPMF")
    ap.add_argument("--memory", action="store_true", help="đo peak memory (chậm hơn)")
    ap.add_argument("--rules", action="store_true", help="sinh luật kết hợp")
    ap.add_argument("--minconf", type=float, default=0.5)
    ap.add_argument("--top", type=int, default=10, help="in top-N luật theo lift")
    args = ap.parse_args()

    transactions = read_transactions(args.input, args.delimiter)
    n = len(transactions)
    minsup_abs = resolve_minsup(args.minsup, n)
    print(f"[data] {n} giao dịch | độ dài TB {sum(map(len, transactions)) / n:.2f} | "
          f"minsup = {minsup_abs} giao dịch")

    if args.memory:
        tracemalloc.start()
    t0 = time.perf_counter()
    frequent = ALGOS[args.algo](transactions, minsup_abs, args.max_len)
    elapsed = time.perf_counter() - t0
    peak = tracemalloc.get_traced_memory()[1] if args.memory else None
    if args.memory:
        tracemalloc.stop()

    by_len = {}
    for s in frequent:
        by_len[len(s)] = by_len.get(len(s), 0) + 1
    print(f"[{args.algo}] {len(frequent)} frequent itemset | {elapsed:.3f}s"
          + (f" | peak {peak / 2**20:.1f} MiB" if peak else ""))
    print("        theo kích thước:", dict(sorted(by_len.items())))

    if args.output:
        write_spmf(frequent, args.output)
        print(f"[out] đã ghi {args.output}")

    if args.rules:
        rules = generate_rules(frequent, n, args.minconf)
        print(f"\n[rules] {len(rules)} luật (minconf={args.minconf}). Top {args.top} theo lift:")
        for r in rules[:args.top]:
            print(f"  {set(r['antecedent'])} -> {set(r['consequent'])}  "
                  f"sup={r['support']:.4f} conf={r['confidence']:.3f} lift={r['lift']:.3f}")


if __name__ == "__main__":
    main()
