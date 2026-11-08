module HybridApriori

import ..TidApriori: generate_candidates_with_parents, tid_pass, finish_pass!

export apriori_hybrid

function apriori_pass(tsets::Vector{Set{Int}}, cands::Vector{Vector{Int}},
                      k::Int, budget::Int)
    counts = zeros(Int, length(cands))
    newbar::Union{Nothing,Vector{Vector{Int32}}} = Vector{Vector{Int32}}()
    recorded = 0

    for ts in tsets
        length(ts) < k && continue
        found = Int32[]
        for ci in eachindex(cands)
            if issubset(cands[ci], ts)
                counts[ci] += 1
                newbar !== nothing && push!(found, Int32(ci))
            end
        end
        if newbar !== nothing && !isempty(found)
            push!(newbar, found)
            recorded += length(found)
            if recorded > budget
                newbar = nothing           # C̄_k quá lớn, không giữ nữa
            end
        end
    end
    return counts, newbar
end

function apriori_hybrid(transactions::Vector{Vector{Int}}, minsup_abs::Int;
                        max_len::Union{Int,Nothing} = nothing,
                        cbar_budget::Int = 10_000_000)
    frequent = Dict{Vector{Int},Int}()

    counts1 = Dict{Int,Int}()
    for t in transactions, item in t
        counts1[item] = get(counts1, item, 0) + 1
    end
    level = Vector{Vector{Int}}()
    for (item, c) in counts1
        if c >= minsup_abs
            push!(level, [item])
            frequent[[item]] = c
        end
    end
    sort!(level)

    tsets = [Set(t) for t in transactions]
    use_tid = false
    cbar = Vector{Vector{Int32}}()

    k = 2
    while !isempty(level) && (isnothing(max_len) || k <= max_len)
        cands, p1, p2 = generate_candidates_with_parents(level, k)
        isempty(cands) && break

        if use_tid
            counts, newbar = tid_pass(cbar, p1, p2, length(cands), length(level))
        else
            counts, newbar = apriori_pass(tsets, cands, k, cbar_budget)
        end

        new_level, new_cbar = finish_pass!(frequent, cands, counts, newbar, minsup_abs;
                                           want_cbar = use_tid || newbar !== nothing)

        if !use_tid && newbar !== nothing && length(new_level) < length(level)
            use_tid = true                 # chuyển sang AprioriTid từ mức k+1
            empty!(tsets)                  # CSDL gốc không còn cần nữa
        end
        use_tid && (cbar = new_cbar)

        level = new_level
        k += 1
    end
    return frequent
end

end # module HybridApriori