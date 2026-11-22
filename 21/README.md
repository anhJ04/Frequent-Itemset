# Khai thác tập phổ biến bằng họ thuật toán Apriori (Julia)

Đồ án **Khai thác tập phổ biến (Frequent Itemset Mining)**, nhóm 21. Nhóm cài đặt lại từ bài báo gốc
*R. Agrawal & R. Srikant, "Fast Algorithms for Mining Association Rules", VLDB 1994* ba thuật toán
**Apriori, AprioriTid, AprioriHybrid**, cùng một biến thể tối ưu dùng tidset dạng `BitVector`.
Toàn bộ viết bằng Julia, không dùng thư viện FIM có sẵn.

| | |
|---|---|
| **Thành viên** | Thành viên 1 – MSSV · Thành viên 2 – MSSV · Thành viên 3 – MSSV |
| **Demo Colab** | <https://colab.research.google.com/github/TEN_GITHUB/Frequent-Itemset/blob/main/21/notebooks/demo.ipynb> |
| **Báo cáo** | [`docs/Report.pdf`](docs/Report.pdf) |
| **Dữ liệu** | có sẵn trong `data/` (mỗi file < 100 MB); nguồn gốc: [SPMF datasets](https://www.philippe-fournier-viger.com/spmf/index.php?link=datasets.php), [FIMI](http://fimi.uantwerpen.be/data/) |

## Kết quả chính

- **Tính đúng đắn:** 103/103 lần so sánh với SPMF khớp 100% (cùng itemset và cùng support) trên Chess, Mushroom, Retail và T10I4D100K × 7 mức minsup × 4 biến thể. Unit test so với SPMF trên 5 CSDL đều đạt.
- **Tối ưu hoá:** bản `BitVector` nhanh hơn bản cơ bản **18–80 lần** trên dữ liệu dày. Trên T10I4D100K ở minsup 0.005 nó **nhanh hơn SPMF 5 lần** (0.51 s so với 2.57 s).
- **Ứng dụng 1, Market Basket (Groceries):** 125 luật, top-10 theo lift có diễn giải kinh doanh.
- **Ứng dụng 2, Sinh học (genome SARS-CoV-2):** frequent itemset trên 3-mer tái phát hiện hiện tượng **ức chế CpG**. Cả 8 bộ ba chứa CG đều nằm trong nhóm 10 bộ ba hiếm nhất.

## Cài đặt môi trường

Yêu cầu Julia ≥ 1.9 (đã chạy với 1.11/1.12). Python ≥ 3.9 kèm `matplotlib` và `pandas` chỉ dùng cho script thực nghiệm và notebook. SPMF cần Java ≥ 25 (`tools/spmf.jar`).

```bash
# Windows:  winget install --name Julia --id 9NJNWW8PVKMN -e -s msstore
# Linux/Mac: curl -fsSL https://install.julialang.org | sh
julia --project=. -e 'using Pkg; Pkg.instantiate()'
pip install -r requirements.txt
```

Mọi lệnh dưới đây chạy trong thư mục `21/`.

## Cách chạy

### CLI (định dạng SPMF)

```bash
julia --project=. run_cli.jl --input data/benchmark/chess.txt --minsup 0.8 --algo hybrid -o results/chess_0.8
julia --project=. run_cli.jl mushrooms 0.5 optimized          # dạng rút gọn: <dataset> <minsup> [algo]
```

| Tham số | Ý nghĩa |
|---|---|
| `--input`, `-i` | file SPMF (mỗi dòng một giao dịch, item cách nhau dấu cách) hoặc tên dataset trong `data/benchmark/` |
| `--minsup`, `-s` | ngưỡng tương đối trong (0, 1]; ngưỡng tuyệt đối = ⌈minsup·N⌉ (giống SPMF) |
| `--algo`, `-a` | `basic` · `optimized` (BitVector) · `tid` · `hybrid` |
| `--output`, `-o` | tiền tố file ra: `<o>_list.txt` (định dạng SPMF `1 3 5 #SUP: 42`) và `<o>_stat.txt` |
| `--maxlen` | giới hạn kích thước itemset (tuỳ chọn) |

So sánh với file output của SPMF:

```bash
python compare_outputs.py tests/ref/chess_0.8.txt results/chess_0.8_list.txt
```

### Luật kết hợp (Ứng dụng 1)

```bash
julia --project=. apps/app_rules.jl data/processed/groceries.txt 0.01 0.3 results/app1/groceries_rules.csv hybrid
```

File `data/processed/groceries.txt` được sinh từ `data/raw/groceries.csv` trong notebook.

### Unit test

```bash
julia --project=. tests/runtests.jl            # 5 CSDL so với SPMF + brute force + luật kết hợp
FULL=1 julia --project=. tests/runtests.jl     # thêm chess minsup 0.5 (1.27 triệu itemset)
```

Output lần chạy cuối:

```text
(DÁN OUTPUT CỦA LỆNH TEST VÀO ĐÂY)
```

### Thực nghiệm (Chương 2)

```bash
python bench/run_experiments.py --cap 30        # thêm --java <đường dẫn java 25> nếu cần, hoặc --no-spmf
python bench/plot_results.py                    # biểu đồ + bảng LaTeX -> results/exp/fig/
```

Mỗi lần đo chạy trong một tiến trình Julia riêng, đã warm-up JIT, và giới hạn 30 s. Các thí nghiệm gồm: thời gian, số itemset, bộ nhớ theo minsup (kèm correctness so với SPMF), scalability trên Retail (10–100%, seed 42) và ảnh hưởng của độ dài giao dịch (dữ liệu tổng hợp, seed 42). Kết quả của nhóm nằm trong `results/exp/`.

## Cấu trúc thư mục

```
21/
├── README.md
├── Project.toml              # môi trường Julia
├── requirements.txt          # Python cho script thực nghiệm / notebook
├── run_cli.jl                # CLI
├── compare_outputs.py        # so sánh output với SPMF
├── gen_data.py               # sinh CSDL tổng hợp (seed cố định)
├── src/
│   ├── Apriori.jl            # module chính
│   ├── utils.jl              # đọc/ghi định dạng SPMF
│   ├── AprioriBasic.jl       # Apriori cơ bản
│   ├── AprioriTid.jl         # AprioriTid
│   ├── AprioriHybrid.jl      # AprioriHybrid
│   ├── AprioriOptimized.jl   # biến thể BitVector (tối ưu)
│   └── rules.jl              # sinh luật kết hợp
├── apps/app_rules.jl         # Ứng dụng 1
├── tests/
│   ├── runtests.jl
│   └── ref/                  # kết quả tham chiếu từ SPMF
├── bench/                    # run_one.jl, run_experiments.py, plot_results.py, plot_levels.py
├── data/
│   ├── toy/                  # CSDL nhỏ để kiểm thử
│   ├── benchmark/            # chess, mushrooms, retail, T10I4D100K, skin, MT745584 (genome)
│   ├── raw/groceries.csv     # Groceries
│   └── processed/            # giao dịch sinh ra trong notebook
├── results/exp/              # CSV + biểu đồ thực nghiệm
├── notebooks/demo.ipynb      # demo Colab
├── tools/spmf.jar            # SPMF (chỉ dùng làm tham chiếu)
└── docs/Report.pdf           # báo cáo
```

## Tài liệu tham khảo chính

- R. Agrawal, R. Srikant. *Fast Algorithms for Mining Association Rules*. VLDB 1994. (bài báo gốc)
- P. Fournier-Viger et al. *The SPMF Open-Source Data Mining Library Version 2*. ECML PKDD 2016.
