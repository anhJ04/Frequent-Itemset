module TidApriori

export apriori_tid

function generate_candidates_with_parents(prev_level::Vector{Vector{Int}}, k::Int)
    prev_set = Set(prev_level)
    cands = Vector{Vector{Int}}()
    p1 = Int[]
    p2 = Int[]
    n = length(prev_level)
    for i in 1:n
        a = prev_level[i]
        for j in (i + 1):n
            b = prev_level[j]
            a[1:end-1] != b[1:end-1] && break
            cand = vcat(a, b[end])
            ok = true
            for idx in 1:(k - 2)          # hai tập con bỏ 2 item cuối đã thuộc L_{k-1}
                if !(cand[1:end .!= idx] in prev_set)
                    ok = false
                    break
                end
            end
            if ok
                push!(cands, cand)
                push!(p1, i)
                push!(p2, j)
            end
        end
    end
    return cands, p1, p2
end


function tid_pass(cbar::Vector{Vector{Int32}}, p1::Vector{Int}, p2::Vector{Int},
                  ncand::Int, nprev::Int)
    by_p1 = [Int[] for _ in 1:nprev]
    for ci in 1:ncand
        push!(by_p1[p1[ci]], ci)
    end

    counts = zeros(Int, ncand)
    mark = zeros(Int, nprev)               
    newbar = Vector{Vector{Int32}}()

    for (t, entry) in enumerate(cbar)
        for id in entry
            mark[id] = t
        end
        found = Int32[]
        for g in entry
            for ci in by_p1[g]
                if mark[p2[ci]] == t
                    counts[ci] += 1
                    push!(found, Int32(ci))
                end
            end
        end
        isempty(found) || push!(newbar, found)
    end
    return counts, newbar
end

function finish_pass!(frequent::Dict{Vector{Int},Int}, cands::Vector{Vector{Int}},
                      counts::Vector{Int},
                      newbar::Union{Nothing,Vector{Vector{Int32}}},
                      minsup_abs::Int; want_cbar::Bool = true)
    newidx = zeros(Int32, length(cands))
    level = Vector{Vector{Int}}()
    for ci in eachindex(cands)
        if counts[ci] >= minsup_abs
            push!(level, cands[ci])
            newidx[ci] = Int32(length(level))
            frequent[cands[ci]] = counts[ci]
        end
    end

    cbar = Vector{Vector{Int32}}()
    if want_cbar && newbar !== nothing
        for entry in newbar
            kept = Int32[newidx[c] for c in entry if newidx[c] != 0]
            isempty(kept) || push!(cbar, kept)
        end
    end
    return level, cbar
end

function apriori_tid(transactions::Vector{Vector{Int}}, minsup_abs::Int;
                     max_len::Union{Int,Nothing} = nothing)
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
    isempty(level) && return frequent

    # C̄_1: với mỗi giao dịch, các 1-itemset phổ biến có trong nó
    idx1 = Dict{Int,Int32}(level[i][1] => Int32(i) for i in eachindex(level))
    cbar = Vector{Vector{Int32}}()
    for t in transactions
        e = Int32[idx1[x] for x in t if haskey(idx1, x)]
        isempty(e) || push!(cbar, e)
    end

    k = 2
    while !isempty(level) && (isnothing(max_len) || k <= max_len)
        cands, p1, p2 = generate_candidates_with_parents(level, k)
        isempty(cands) && break
        counts, newbar = tid_pass(cbar, p1, p2, length(cands), length(level))
        level, cbar = finish_pass!(frequent, cands, counts, newbar, minsup_abs)
        k += 1
    end
    return frequent
end

end # module TidApriori