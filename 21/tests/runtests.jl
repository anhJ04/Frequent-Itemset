# Bộ kiểm thử tự động cho Apriori / AprioriTid / AprioriHybrid / Apriori-bitset.
#
#   julia --project=. tests/runtests.jl            # 5 CSDL so với SPMF (nhanh)
#   FULL=1 julia --project=. tests/runtests.jl     # thêm chess minsup 0.5 (1.27 triệu itemset, chậm)
#
# Mỗi file tham chiếu trong tests/ref/ được sinh bằng SPMF (Apriori) trên cùng input.
# Tên file: <dataset>_<minsup>.txt  (minsup ≤ 1: tỉ lệ, > 1: số giao dịch tuyệt đối).

using Test
using Printf
include(joinpath(@__DIR__, "..", "src", "Apriori.jl"))
using .Apriori

const ROOT  = joinpath(@__DIR__, "..")
const REF   = joinpath(@__DIR__, "ref")
const ALGOS = [("basic", apriori_basic), ("optimized", apriori_optimized),
               ("tid", apriori_tid), ("hybrid", apriori_hybrid)]

"Đọc output định dạng SPMF (`1 2 3 #SUP: 5`) thành Dict itemset => support."
function read_spmf_output(path::AbstractString)
    d = Dict{Vector{Int},Int}()
    for line in eachline(path)
        line = strip(line)
        (isempty(line) || startswith(line, "@")) && continue
        items, sup = split(line, "#SUP:")
        d[sort!(parse.(Int, split(items)))] = parse(Int, strip(sup))
    end
    return d
end

"Tỉ lệ itemset khớp hoàn toàn (cùng itemset và cùng support) so với tham chiếu."
function match_stats(ref::Dict, mine::Dict)
    exact   = count(k -> get(mine, k, -1) == ref[k], keys(ref))
    extra   = count(k -> !haskey(ref, k), keys(mine))
    denom   = length(ref) + extra
    return (exact = exact, ref = length(ref), mine = length(mine), extra = extra,
            rate = denom == 0 ? 1.0 : exact / denom)
end

"Brute force: duyệt mọi tập con của từng giao dịch (chỉ dùng cho CSDL rất nhỏ)."
function brute_force(transactions, minsup_abs)
    cnt = Dict{Vector{Int},Int}()
    for t in transactions
        n = length(t)
        for mask in 1:(2^n - 1)
            s = [t[i] for i in 1:n if (mask >> (i - 1)) & 1 == 1]
            cnt[s] = get(cnt, s, 0) + 1
        end
    end
    return Dict(k => v for (k, v) in cnt if v >= minsup_abs)
end

# (dataset, minsup, file tham chiếu)
cases = [("toy", 2, "toy_2.txt"), ("chess", 0.8, "chess_0.8.txt"),
         ("mushrooms", 0.5, "mushrooms_0.5.txt"), ("retail", 0.02, "retail_0.02.txt"),
         ("skin", 0.01, "skin_0.01.txt")]
get(ENV, "FULL", "0") == "1" && push!(cases, ("chess", 0.5, "chess_0.5.txt"))

report_rows = Tuple{String,Any,String,Any}[]

@testset "Apriori" begin
    @testset "I/O định dạng SPMF" begin
        tx = read_spmf(joinpath(ROOT, "data", "toy", "toy.txt"))
        @test tx == [[1, 3, 4], [2, 3, 5], [1, 2, 3, 5], [2, 5]]
        tmp = tempname()
        write_spmf(tmp, Dict([1, 3] => 2, [2] => 3))
        @test readlines(tmp) == ["2 #SUP: 3", "1 3 #SUP: 2"]
        @test read_spmf_output(tmp) == Dict([1, 3] => 2, [2] => 3)
    end

    @testset "Đối chiếu brute force (CSDL ngẫu nhiên nhỏ, seed cố định)" begin
        state = UInt64(42)                     # LCG tự viết để không phụ thuộc thư viện Random
        rnd() = (state = state * 6364136223846793005 + 1442695040888963407; state >> 33)
        for trial in 1:20
            tx = [sort!(unique!([Int(rnd() % 8) + 1 for _ in 1:(rnd() % 6 + 1)])) for _ in 1:15]
            for ms in (1, 2, 3, 5)
                expected = brute_force(tx, ms)
                for (name, f) in ALGOS
                    @test f(tx, ms) == expected
                end
            end
        end
    end

    @testset "Luật kết hợp (support, confidence, lift)" begin
        tx = read_spmf(joinpath(ROOT, "data", "toy", "toy.txt"))   # 4 giao dịch
        fr = apriori_hybrid(tx, 2)
        rules = generate_rules(fr, length(tx), 0.0)
        r = only(filter(r -> r.antecedent == [1] && r.consequent == [3], rules))
        @test r.support ≈ 2 / 4                # sup({1,3}) = 2
        @test r.confidence ≈ 1.0               # sup({1,3}) / sup({1}) = 2/2
        @test r.lift ≈ 1.0 / (3 / 4)           # confidence / (sup({3}) / N)
        # số luật = Σ (2^|Z| - 2) trên các tập phổ biến |Z| ≥ 2 khi minconf = 0
        @test length(rules) == sum(2^length(z) - 2 for z in keys(fr) if length(z) >= 2)
        @test issorted(rules, by = r -> -r.lift)
        @test all(r -> r.confidence >= 0.7, generate_rules(fr, length(tx), 0.7))
    end

    @testset "Đối chiếu SPMF: $ds minsup=$ms" for (ds, ms, ref_file) in cases
        tx = read_spmf(joinpath(ROOT, "data", "benchmark", ds * ".txt"))
        minsup_abs = ms > 1 ? Int(ms) : ceil(Int, ms * length(tx))
        ref = read_spmf_output(joinpath(REF, ref_file))
        for (name, f) in ALGOS
            # bản basic quá chậm với 1.27 triệu itemset -> bỏ qua ở ca FULL
            (name == "basic" && length(ref) > 200_000) && continue
            st = match_stats(ref, f(tx, minsup_abs))
            push!(report_rows, (ds, ms, name, st))
            @test st.rate == 1.0
        end
    end
end

println("\nTỉ lệ khớp so với SPMF")
println(rpad("CSDL", 11), rpad("minsup", 8), rpad("thuật toán", 12),
        lpad("SPMF", 9), lpad("nhóm", 9), lpad("khớp", 9), lpad("tỉ lệ", 9))
for (ds, ms, name, st) in report_rows
    println(rpad(ds, 11), rpad(string(ms), 8), rpad(name, 12), lpad(st.ref, 9),
            lpad(st.mine, 9), lpad(st.exact, 9), lpad(@sprintf("%.2f%%", 100st.rate), 9))
end
