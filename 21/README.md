# Apriori – khai thác tập phổ biến (Frequent Itemset Mining)

Project Python thuần (chỉ cần `matplotlib` nếu muốn vẽ biểu đồ). Yêu cầu Python ≥ 3.10.

## Cấu trúc

```
apriori_project/
├── apriori_fim/
│   ├── apriori_basic.py      # Apriori cơ bản (baseline): join + prune, quét CSDL mỗi mức
│   ├── apriori_optimized.py  # Bản tối ưu: vertical bitset, support = popcount(AND)
│   ├── rules.py              # Sinh luật kết hợp (support, confidence, lift) cho Ứng dụng 1
│   └── io_utils.py           # Đọc CSDL / đọc-ghi định dạng SPMF
├── run_apriori.py            # CLI chạy thuật toán
├── compare_spmf.py           # Kiểm tra Correctness so với SPMF
├── experiments.py            # Thí nghiệm: runtime, #itemset, RAM, scalability, độ dài giao dịch
├── gen_data.py               # Sinh CSDL tổng hợp
├── tests/test_apriori.py     # Unit test (đối chiếu brute force)
├── data/                     # toy.txt, synthetic.txt (đặt Retail/Accidents... vào đây)
└── results/                  # CSV, PNG, output SPMF
```

## Định dạng dữ liệu

Mỗi dòng là một giao dịch, các item cách nhau bằng khoảng trắng (định dạng SPMF):
```
1 3 4
2 3 5
```
CSV chữ (ví dụ Groceries): dùng `--delimiter ,`.
Bộ Retail, Accidents, Chess, Mushroom… tải ở trang Datasets của SPMF (hoặc mirror Hugging Face/Kaggle theo đề).

## Chạy nhanh

```bash
# Chạy + ghi kết quả dạng SPMF (`1 2 #SUP: 5`)
python run_apriori.py data/toy.txt --minsup 0.5 -o results/toy_out.txt

# Bản cơ bản vs bản tối ưu, đo RAM
python run_apriori.py data/retail.txt --minsup 0.02 --algo basic
python run_apriori.py data/retail.txt --minsup 0.02 --algo optimized --memory

# Ứng dụng 1: Market Basket – top-10 luật theo lift
python run_apriori.py data/retail.txt --minsup 0.01 --rules --minconf 0.3 --top 10
```
`--minsup`: ≤ 1 là tỉ lệ (0.02 = 2%), > 1 là số giao dịch tuyệt đối. Ngưỡng tuyệt đối = `ceil(minsup × N)` (giống SPMF).

## Kiểm tra đúng đắn với SPMF

```bash
# Cách 1: đã chạy SPMF (Apriori) và có file output
python compare_spmf.py data/retail.txt --minsup 0.02 --spmf-output results/retail_spmf.txt

# Cách 2: tự gọi SPMF (cần Java + spmf.jar)
python compare_spmf.py data/retail.txt --minsup 0.02 --spmf-jar /duong/dan/spmf.jar
```
Báo cáo tỉ lệ itemset khớp hoàn toàn (itemset + support) và liệt kê sai lệch.

## Thí nghiệm cho báo cáo (Chương 2)

```bash
python experiments.py data/retail.txt --name retail \
    --minsups 0.05 0.03 0.02 0.01 0.005 --mid-minsup 0.02 --length-exp
```
Xuất vào `results/`: `*_runtime_count.csv`, `*_memory.csv`, `*_scalability.csv`, `*_length.csv` và các PNG.
Bản `basic` rất chậm khi minsup nhỏ → dùng `--skip-basic-below 0.01` để bỏ qua.
Muốn có đường cong SPMF trên cùng đồ thị: ghi `results/<name>_spmf_time.csv` (cột `minsup,time`).

## Test

```bash
python -m unittest discover -s tests -v
```

## Ý tưởng tối ưu (dùng cho phần "đề xuất tối ưu" trong báo cáo)

| Bản cơ bản | Bản tối ưu |
|---|---|
| Quét lại toàn bộ CSDL ở mỗi mức k | Bitset TID, support = `popcount(tid(X) & tid(Y))`, không quét lại |
| Kiểm tra `candidate ⊆ transaction` O(T·C) | Phép AND trên số nguyên lớn (C-speed) |
| Giữ CSDL dạng tập trong RAM | Chỉ giữ bitset của mức hiện tại |

Hướng cải tiến tiếp theo có thể đề xuất: sắp thứ tự item theo support tăng dần, dùng diffset (dEclat-style), hash-tree/trie cho đếm ứng viên, song song hóa theo nhóm prefix.

## Lưu ý

- Item trùng trong một giao dịch được gộp lại.
- Với `--rules`, mọi tập con của tập phổ biến đều phổ biến nên tra support trực tiếp từ kết quả.
- Ứng dụng 2 (log hệ thống / sinh học / ảnh) cần bước chuyển dữ liệu → giao dịch riêng (xem đề); sau đó đưa file vào `run_apriori.py` như bình thường.
