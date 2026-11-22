# Ứng dụng 1: khai thác tập phổ biến bằng cài đặt của nhóm rồi sinh luật kết hợp.
#
#   julia --project=. apps/app_rules.jl <input.txt> <minsup> <minconf> <rules.csv> [algo]
#
# Ghi: <rules.csv> (mọi luật đạt minconf, đã sắp theo lift) và
#      <rules>_itemsets.txt (tập phổ biến, định dạng SPMF).

include(joinpath(@__DIR__, "..", "src", "Apriori.jl"))
using .Apriori
using Printf

const ALGOS = Dict("basic" => apriori_basic, "optimized" => apriori_optimized,
                   "tid" => apriori_tid, "hybrid" => apriori_hybrid)

function main(args)
    length(args) >= 4 ||
        error("cần: <input.txt> <minsup> <minconf> <rules.csv> [basic|optimized|tid|hybrid]")
    input, minsup, minconf, out = args[1], parse(Float64, args[2]), parse(Float64, args[3]), args[4]
    algo = length(args) >= 5 ? args[5] : "hybrid"

    tx = read_spmf(input)
    n = length(tx)
    minsup_abs = ceil(Int, minsup * n)
    t = @elapsed frequent = ALGOS[algo](tx, minsup_abs)
    rules = generate_rules(frequent, n, minconf)

    mkpath(dirname(abspath(out)))
    write_spmf(replace(out, r"\.csv$" => "") * "_itemsets.txt", frequent)
    open(out, "w") do io
        println(io, "antecedent,consequent,support,confidence,lift")
        for r in rules
            @printf(io, "%s,%s,%.6f,%.6f,%.6f\n", join(r.antecedent, " "),
                    join(r.consequent, " "), r.support, r.confidence, r.lift)
        end
    end
    @printf("%d giao dịch | minsup=%g (%d) | %s: %d tập phổ biến trong %.3f s | %d luật (minconf=%g) -> %s\n",
            n, minsup, minsup_abs, algo, length(frequent), t, length(rules), minconf, out)
end

main(ARGS)
