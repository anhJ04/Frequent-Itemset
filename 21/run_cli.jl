using Pkg
Pkg.activate(@__DIR__)

include("src/Apriori.jl")
using .Apriori

function parse_args(args)
    params = Dict(
        "input" => "",
        "minsup" => 0.05,
        "algo" => "optimized",
        "output" => "output.txt"
    )
    i = 1
    while i <= length(args)
        if args[i] == "--input" || args[i] == "-i"
            params["input"] = args[i+1]
            i += 2
        elseif args[i] == "--minsup" || args[i] == "-s"
            params["minsup"] = parse(Float64, args[i+1])
            i += 2
        elseif args[i] == "--algo" || args[i] == "-a"
            params["algo"] = args[i+1]
            i += 2
        elseif args[i] == "--output" || args[i] == "-o"
            params["output"] = args[i+1]
            i += 2
        else
            i += 1
        end
    end
    return params
end

# Main Execution
args = parse_args(ARGS)
if isempty(args["input"])
    println("Cách dùng: julia run_cli.jl --input data/retail.txt --minsup 0.02 --algo optimized --output results.txt")
    exit(1)
end

println("[1/3] Đang đọc CSDL từ: ", args["input"])
transactions = read_spmf(args["input"])
num_trans = length(transactions)
minsup_abs = ceil(Int, args["minsup"] * num_trans)

println("[2/3] Đang chạy thuật toán Apriori (", args["algo"], ") | Minsup tương đối: ", args["minsup"], " (Tối thiểu ", minsup_abs, " giao dịch)")

t_start = time()
if args["algo"] == "basic"
    res = apriori_basic(transactions, minsup_abs)
else
    res = apriori_optimized(transactions, minsup_abs)
end
t_elapsed = time() - t_start

println("[3/3] Hoàn thành trong: ", round(t_elapsed, digits=4), "s. Tìm thấy ", length(res), " frequent itemsets.")
println("Đang ghi kết quả ra: ", args["output"])
write_spmf(args["output"], res)