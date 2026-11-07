using Test
include(joinpath(@__DIR__, "..", "src", "Apriori.jl"))
using .Apriori

@testset "Apriori Correctness Test" begin
    # Toy Data
    toy_transactions = [
        [1, 2, 5],
        [2, 4],
        [2, 3],
        [1, 2, 4],
        [1, 3],
        [2, 3],
        [1, 3],
        [1, 2, 3, 5],
        [1, 2, 3]
    ]
    
    minsup_abs = 2
    
    res_basic = apriori_basic(toy_transactions, minsup_abs)
    res_opt = apriori_optimized(toy_transactions, minsup_abs)
    
    # 1. Kiểm tra hai kết quả trả về đúng cùng số lượng tập phổ biến
    @test length(res_basic) == length(res_opt)
    
    # 2. Kiểm tra chính xác từng itemset và support count
    for (itemset, sup) in res_basic
        @test haskey(res_opt, itemset)
        @test res_opt[itemset] == sup
    end
end