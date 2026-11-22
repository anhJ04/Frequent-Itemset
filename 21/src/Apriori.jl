module Apriori

include(joinpath(@__DIR__, "utils.jl"))
include(joinpath(@__DIR__, "AprioriBasic.jl"))
include(joinpath(@__DIR__, "AprioriOptimized.jl"))
include(joinpath(@__DIR__, "AprioriTid.jl"))
include(joinpath(@__DIR__, "AprioriHybrid.jl"))
include(joinpath(@__DIR__, "rules.jl"))
using .Utils
using .BasicApriori
using .OptimizedApriori
using .TidApriori
using .HybridApriori
using .Rules

export read_spmf, write_spmf,
       apriori_basic, apriori_optimized, apriori_tid, apriori_hybrid,
       AssociationRule, generate_rules
end
