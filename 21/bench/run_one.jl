# Chạy MỘT lần đo (một thuật toán, một CSDL, một minsup) trong tiến trình riêng
# để peak RAM (Sys.maxrss) không bị lẫn giữa các lần chạy.
#
#   julia --project=. bench/run_one.jl <input> <minsup> <algo> [output]
#
# In ra đúng một dòng JSON ở cuối stdout. Thời gian chỉ tính phần thuật toán
# (không gồm đọc file và biên dịch JIT: đã warm-up trên CSDL toy trước khi đo).

include(joinpath(@__DIR__, "..", "src", "Apriori.jl"))
using .Apriori

const ALGOS = Dict("basic" => apriori_basic, "optimized" => apriori_optimized,
                   "tid" => apriori_tid, "hybrid" => apriori_hybrid)

function main(args)
    length(args) >= 3 || error("cần: <input> <minsup> <algo> [output]")
    input, ms, algo = args[1], parse(Float64, args[2]), args[3]
    f = ALGOS[algo]

    toy = read_spmf(joinpath(@__DIR__, "..", "data", "toy", "toy.txt"))
    f(toy, 2)                                   # warm-up: ép JIT biên dịch trước khi đo

    tx = read_spmf(input)
    n = length(tx)
    minsup_abs = ms > 1 ? round(Int, ms) : ceil(Int, ms * n)
    avg_len = sum(length, tx) / n

    GC.gc()
    rss_before = Sys.maxrss()                   # đỉnh RSS trước khi chạy thuật toán
    t = @timed f(tx, minsup_abs)
    rss_peak = Sys.maxrss()
    res = t.value

    length(args) >= 4 && write_spmf(args[4], res)

    maxk = isempty(res) ? 0 : maximum(length, keys(res))
    mb(x) = round(x / 2^20, digits = 2)
    println("{\"algo\":\"$algo\",\"n\":$n,\"avg_len\":$(round(avg_len, digits=3)),",
            "\"minsup\":$ms,\"minsup_abs\":$minsup_abs,\"count\":$(length(res)),",
            "\"max_k\":$maxk,\"time\":$(round(t.time, digits=5)),",
            "\"gc_time\":$(round(t.gctime, digits=5)),\"alloc_mb\":$(mb(t.bytes)),",
            "\"rss_before_mb\":$(mb(rss_before)),\"rss_peak_mb\":$(mb(rss_peak))}")
end

main(ARGS)
