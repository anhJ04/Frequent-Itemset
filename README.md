# Đồ án Khai thác tập phổ biến - Nhóm 21

Nhóm gồm Nguyễn Thanh Trọng (24127136) và Nguyễn Lê Thanh An (24127269).

Nhóm chọn thuật toán Apriori và cài đặt lại bằng Julia theo bài báo "Fast Algorithms for Mining Association Rules" (Agrawal & Srikant, 1994). Có 4 phiên bản: Apriori cơ bản, AprioriTid, Apriori Hybrid và một bản tối ưu dùng BitVector.

- Notebook Colab: https://colab.research.google.com/github/anhJ04/Frequent-Itemset/blob/main/21/notebooks/demo.ipynb
- Báo cáo: `docs/Report.pdf`

## Cài đặt

Cần Julia 1.9 trở lên. Python (matplotlib, pandas) dùng để vẽ biểu đồ và chạy notebook. Nếu muốn chạy SPMF để so sánh thì cần thêm Java 25.

```
julia --project=. -e "using Pkg; Pkg.instantiate()"
pip install -r requirements.txt
```

## Cách chạy

Tất cả lệnh chạy trong thư mục `21`.

Tìm tập phổ biến, đầu vào và đầu ra theo định dạng SPMF:

```
julia --project=. run_cli.jl --input data/benchmark/chess.txt --minsup 0.8 --algo hybrid -o results/chess
```

`--algo` chọn một trong `basic`, `optimized`, `tid`, `hybrid`. Kết quả nằm ở `results/chess_list.txt`, thống kê ở `results/chess_stat.txt`.

Sinh luật kết hợp (dùng cho ứng dụng giỏ hàng):

```
julia --project=. apps/app_rules.jl data/processed/groceries.txt 0.01 0.3 results/app1/rules.csv
```

Chạy test:

```
julia --project=. tests/runtests.jl
```

Chạy lại thực nghiệm ở chương 2 rồi vẽ biểu đồ:

```
python bench/run_experiments.py --cap 30
python bench/plot_results.py
```

## Kết quả test lần chạy cuối

```text
Test Summary: | Pass  Total  Time
Apriori       |  349    349  8.2s

Tỉ lệ khớp so với SPMF
CSDL       minsup  thuật toán       SPMF     nhóm     khớp    tỉ lệ
toy        2       basic               9        9        9  100.00%
toy        2       optimized           9        9        9  100.00%
toy        2       tid                 9        9        9  100.00%
toy        2       hybrid              9        9        9  100.00%
chess      0.8     basic            8227     8227     8227  100.00%
chess      0.8     optimized        8227     8227     8227  100.00%
chess      0.8     tid              8227     8227     8227  100.00%
chess      0.8     hybrid           8227     8227     8227  100.00%
mushrooms  0.5     basic             163      163      163  100.00%
mushrooms  0.5     optimized         163      163      163  100.00%
mushrooms  0.5     tid               163      163      163  100.00%
mushrooms  0.5     hybrid            163      163      163  100.00%
retail     0.02    basic              55       55       55  100.00%
retail     0.02    optimized          55       55       55  100.00%
retail     0.02    tid                55       55       55  100.00%
retail     0.02    hybrid             55       55       55  100.00%
skin       0.01    basic             114      114      114  100.00%
skin       0.01    optimized         114      114      114  100.00%
skin       0.01    tid               114      114      114  100.00%
skin       0.01    hybrid            114      114      114  100.00%
```

## Các thư mục

- `src/`: code các thuật toán
- `tests/`: unit test; `tests/ref/` là kết quả của SPMF dùng để so sánh
- `bench/`: script chạy thực nghiệm và vẽ biểu đồ
- `apps/`: code sinh luật kết hợp
- `data/benchmark/`: các bộ dữ liệu benchmark (Chess, Mushroom, Retail, T10I4D100K, Skin) và genome MT745584
- `data/raw/`: dữ liệu Groceries gốc
- `data/processed/`: dữ liệu sau khi chuyển thành giao dịch
- `results/`: các file tập phổ biến và kết quả thực nghiệm (`results/exp/`)
- `notebooks/demo.ipynb`: notebook chạy trên Colab
- `docs/Report.pdf`: báo cáo
