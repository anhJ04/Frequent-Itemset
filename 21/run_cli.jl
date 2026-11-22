using Pkg
Pkg.activate(@__DIR__)

include(joinpath(@__DIR__, "src", "Apriori.jl"))
using .Apriori

const USAGE = """
Cách dùng:
  julia --project=. run_cli.jl --input <file|tên dataset> --minsup <0..1> [--algo basic|optimized|tid|hybrid] [--output <đường dẫn>] [--maxlen <k>]
  julia --project=. run_cli.jl <file|tên dataset> <minsup> [algo]

Ví dụ:
  julia --project=. run_cli.jl --input data/benchmark/chess.txt --minsup 0.8 --algo hybrid
  julia --project=. run_cli.jl mushrooms 0.5 optimized -o results/mushrooms_out.txt"""

const BENCH_DIR   = joinpath(@__DIR__, "data", "benchmark")
const RESULTS_DIR = joinpath(@__DIR__, "results")

const ALGOS = Dict("basic"     => apriori_basic,
                   "optimized" => apriori_optimized,
                   "tid"       => apriori_tid,
                   "hybrid"    => apriori_hybrid)

function fail(msg)
    println(msg)
    exit(1)
end

function parse_args(args)
    params = Dict{String,Any}("input" => "", "minsup" => "0.05",
                              "algo" => "optimized", "output" => "", "maxlen" => "")
    flags = Dict("--input" => "input", "-i" => "input",
                 "--minsup" => "minsup", "-s" => "minsup",
                 "--algo" => "algo", "-a" => "algo",
                 "--output" => "output", "-o" => "output",
                 "--maxlen" => "maxlen")
    given = Set{String}()
    positional = String[]

    i = 1
    while i <= length(args)
        a = args[i]
        if haskey(flags, a)
            i == length(args) && fail("Thiếu giá trị cho $a\n\n$USAGE")
            params[flags[a]] = args[i + 1]
            push!(given, flags[a])
            i += 2
        else
            push!(positional, a)
            i += 1
        end
    end
    # tham số không có cờ: theo thứ tự dataset, minsup, algo (cờ, nếu có, được ưu tiên)
    for (key, val) in zip(("input", "minsup", "algo"), positional)
        key in given || (params[key] = val)
    end

    m = tryparse(Float64, string(params["minsup"]))
    (m === nothing || !(0 < m <= 1)) &&
        fail("minsup phải là số trong khoảng (0, 1], nhận được: $(params["minsup"])\n\n$USAGE")
    params["minsup"] = m
    params["maxlen"] = isempty(params["maxlen"]) ? nothing : parse(Int, params["maxlen"])
    return params
end

function resolve_input(name::AbstractString)
    isfile(name) && return name
    file = endswith(name, ".txt") ? name : name * ".txt"
    path = joinpath(BENCH_DIR, file)
    isfile(path) && return path
    available = isdir(BENCH_DIR) ?
        sort([splitext(f)[1] for f in readdir(BENCH_DIR) if endswith(f, ".txt")]) : String[]
    fail("Không tìm thấy dữ liệu '$name'. Dataset có sẵn trong data/benchmark: " *
         join(available, ", "))
end

function write_stats(path, res, info) #Thống kê
    by_len = Dict{Int,Int}()
    for itemset in keys(res)
        by_len[length(itemset)] = get(by_len, length(itemset), 0) + 1
    end
    open(path, "w") do f
        println(f, "Dataset: ", info.dataset)
        println(f, "Thuật toán: ", info.algo)
        println(f, "Minsup tương đối: ", info.minsup,
                " (tối thiểu ", info.minsup_abs, " / ", info.num_trans, " giao dịch)")
        println(f, "Thời gian chạy (s): ", round(info.seconds, digits = 4))
        println(f, "Bộ nhớ cấp phát (MB): ", round(info.memory_mb, digits = 2))
        println(f, "Bộ nhớ cấp phát (bytes): ", info.memory_bytes)
        println(f)
        println(f, "Tổng số tập phổ biến: ", length(res))
        println(f, "Số tập theo kích thước k:")
        for k in sort(collect(keys(by_len)))
            println(f, "  k = ", k, ": ", by_len[k])
        end
    end
end

args = parse_args(ARGS)
if isempty(args["input"])
    fail(USAGE)
end
haskey(ALGOS, args["algo"]) ||
    fail("--algo phải là một trong: $(join(sort(collect(keys(ALGOS))), ", "))")

input_path = resolve_input(args["input"])
dataset = splitext(basename(input_path))[1]
base = isempty(args["output"]) ?
    joinpath(RESULTS_DIR, "$(dataset)_$(args["algo"])_$(args["minsup"])") :
    replace(args["output"], r"\.txt$" => "")
list_path = base * "_list.txt"
stat_path = base * "_stat.txt"

println("[1/3] Đang đọc CSDL từ: ", input_path)
transactions = read_spmf(input_path)
num_trans = length(transactions)
minsup_abs = ceil(Int, args["minsup"] * num_trans)

println("[2/3] Đang chạy thuật toán Apriori (", args["algo"], ") | Minsup tương đối: ",
        args["minsup"], " (Tối thiểu ", minsup_abs, " giao dịch)")

timed_result = @timed ALGOS[args["algo"]](transactions, minsup_abs; max_len = args["maxlen"])

res = timed_result.value          # Kết quả trả về của thuật toán
t_elapsed = timed_result.time     # Thời gian chạy (giây)
memory_bytes = timed_result.bytes # Tổng bộ nhớ cấp phát (bytes)
memory_mb = memory_bytes / 1024 / 1024 # Quy đổi ra Megabytes (MB)

println("[3/3] Hoàn thành trong: ", round(t_elapsed, digits = 4), "s | Bộ nhớ cấp phát: ", 
        round(memory_mb, digits = 2), " MB. Tìm thấy ", length(res), " frequent itemsets.")
mkpath(dirname(abspath(base)))
println("Đang ghi danh sách tập phổ biến ra: ", list_path)
write_spmf(list_path, res)
println("Đang ghi thống kê ra: ", stat_path)
write_stats(stat_path, res,
            (dataset = dataset, algo = args["algo"], minsup = args["minsup"],
             minsup_abs = minsup_abs, num_trans = num_trans, seconds = t_elapsed,memory_mb = memory_mb, memory_bytes = memory_bytes))