module Apriori

include(joinpath(@__DIR__, "utils.jl"))
include(joinpath(@__DIR__, "basic.jl"))
include(joinpath(@__DIR__, "optimized.jl"))
using .Utils
using .BasicApriori
using .OptimizedApriori

export read_spmf, write_spmf, apriori_basic, apriori_optimized

end