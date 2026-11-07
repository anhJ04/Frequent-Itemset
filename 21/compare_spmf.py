#!/usr/bin/env python3
"""Kiểm tra tính đúng đắn (Correctness) so với SPMF.

Cách 1 - đã có file output của SPMF:
  python compare_spmf.py data/retail.txt --minsup 0.02 --spmf-output results/retail_spmf.txt

Cách 2 - tự gọi SPMF (cần Java và spmf.jar tải từ trang SPMF):
  python compare_spmf.py data/retail.txt --minsup 0.02 --spmf-jar path/to/spmf.jar

Báo cáo: số itemset hai bên, tỉ lệ khớp hoàn toàn (itemset + support), danh sách sai lệch.
(Output SPMF phải là `Apriori` với định dạng `items #SUP: n`.)
"""
import argparse
import subprocess
from pathlib import Path

from apriori_fim import (apriori_optimized, read_spmf_output, read_transactions,
                         resolve_minsup)


def run_spmf(jar, data, minsup, out):
    # SPMF nhận minsup dạng phần trăm, ví dụ "2%"
    cmd = ["java", "-jar", jar, "run", "Apriori", data, out, f"{minsup * 100}%"]
    print("[spmf]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--minsup", type=float, required=True, help="tỉ lệ (0..1)")
    ap.add_argument("--spmf-output")
    ap.add_argument("--spmf-jar")
    ap.add_argument("--delimiter", default=None)
    ap.add_argument("--show", type=int, default=10, help="số sai lệch tối đa in ra")
    args = ap.parse_args()

    spmf_out = args.spmf_output
    if not spmf_out:
        if not args.spmf_jar:
            ap.error("cần --spmf-output hoặc --spmf-jar")
        spmf_out = str(Path("results") / (Path(args.input).stem + f"_spmf_{args.minsup}.txt"))
        Path("results").mkdir(exist_ok=True)
        run_spmf(args.spmf_jar, args.input, args.minsup, spmf_out)

    transactions = read_transactions(args.input, args.delimiter)
    ours = apriori_optimized(transactions, resolve_minsup(args.minsup, len(transactions)))
    ref = read_spmf_output(spmf_out)

    both = set(ours) & set(ref)
    exact = sum(1 for s in both if ours[s] == ref[s])
    union = set(ours) | set(ref)
    print(f"\nNhóm: {len(ours)} itemset | SPMF: {len(ref)} itemset")
    print(f"Khớp hoàn toàn (itemset + support): {exact}/{len(union)} = "
          f"{100 * exact / max(1, len(union)):.2f}%")

    only_ours = sorted(set(ours) - set(ref))
    only_ref = sorted(set(ref) - set(ours))
    diff_sup = sorted(s for s in both if ours[s] != ref[s])
    for name, lst in (("Chỉ có ở nhóm", only_ours), ("Chỉ có ở SPMF", only_ref),
                      ("Khác support", diff_sup)):
        if lst:
            print(f"\n{name}: {len(lst)}")
            for s in lst[:args.show]:
                print("  ", s, "ours=", ours.get(s), "spmf=", ref.get(s))
    if exact == len(union):
        print("\n✓ Kết quả giống hệt SPMF.")


if __name__ == "__main__":
    main()
