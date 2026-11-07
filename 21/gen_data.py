#!/usr/bin/env python3
"""Sinh CSDL giao dịch tổng hợp (cho thí nghiệm ảnh hưởng độ dài giao dịch, test nhanh).

  python gen_data.py -n 5000 --items 200 --avg-len 10 -o data/synthetic.txt
Có chèn một số "pattern" ẩn để tồn tại itemset phổ biến dài.
"""
import argparse
import random


def generate(n, n_items, avg_len, n_patterns=20, pattern_len=4, seed=42):
    rng = random.Random(seed)
    patterns = [rng.sample(range(1, n_items + 1), pattern_len) for _ in range(n_patterns)]
    rows = []
    for _ in range(n):
        L = max(1, int(rng.gauss(avg_len, avg_len * 0.25)))
        t = set()
        while len(t) < L:
            if rng.random() < 0.35:
                t.update(rng.choice(patterns))
            else:
                t.add(rng.randint(1, n_items))
        rows.append(sorted(t))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=5000)
    ap.add_argument("--items", type=int, default=200)
    ap.add_argument("--avg-len", type=float, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    rows = generate(a.n, a.items, a.avg_len, seed=a.seed)
    with open(a.output, "w") as f:
        for r in rows:
            f.write(" ".join(map(str, r)) + "\n")
    print(f"Đã ghi {len(rows)} giao dịch -> {a.output}")


if __name__ == "__main__":
    main()
