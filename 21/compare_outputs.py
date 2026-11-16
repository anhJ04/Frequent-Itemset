import sys

def load(path):
    d = {}
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("@"):   # bỏ header SPMF
                continue
            items, sep, sup = line.partition("#SUP:")
            if not sep:
                raise ValueError(f"{path}:{ln}: thiếu '#SUP:' -> {line!r}")
            key = tuple(sorted(int(x) for x in items.split()))
            if key in d:
                print(f"[CẢNH BÁO] trùng itemset {key} ở {path}:{ln}")
            d[key] = int(sup)
    return d

def main(ref_path, my_path):
    ref, mine = load(ref_path), load(my_path)
    missing  = ref.keys() - mine.keys()          # SPMF có, của bạn thiếu
    extra    = mine.keys() - ref.keys()          # của bạn có, SPMF không có
    bad_sup  = [k for k in ref.keys() & mine.keys() if ref[k] != mine[k]]

    print(f"SPMF: {len(ref)} tập | Tự cài đặt: {len(mine)} tập")
    print(f"Thiếu: {len(missing)} | Thừa: {len(extra)} | Sai support: {len(bad_sup)}")
    for name, items in (("Thiếu", missing), ("Thừa", extra)):
        for k in list(items)[:10]:
            print(f"  {name}: {k}")
    for k in bad_sup[:10]:
        print(f"  Sai support: {k} SPMF={ref[k]} Tự cài đặt={mine[k]}")

    ok = not (missing or extra or bad_sup)
    print("KẾT QUẢ: KHỚP HOÀN TOÀN" if ok else "KẾT QUẢ: KHÁC NHAU")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])