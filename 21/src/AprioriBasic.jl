module BasicApriori

using DataStructures

export apriori_basic

"""
Sinh ứng viên C_k từ L_{k-1} bằng quy tắc Join và Prune.
"""
function generate_candidates(prev_level::Vector{Vector{Int}})::Vector{Vector{Int}}
    candidates = Vector{Vector{Int}}()
    n = length(prev_level)
    prev_set = Set(prev_level)

    for i in 1:n
        a = prev_level[i]
        for j in (i + 1):n
            b = prev_level[j]
            
            # Điều kiện Join: k-2 item đầu tiên phải giống nhau
            if a[1:end-1] != b[1:end-1]
                break
            end
            
            cand = vcat(a, b[end])
            
            # Prune: Tất cả các tập con (k-1) của cand phải nằm trong prev_set
            is_valid = true
            k = length(cand)
            for idx in 1:k
                sub = cand[1:end .!= idx] # Bỏ 1 element
                if !(sub in prev_set)
                    is_valid = false
                    break
                end
            end
            
            if is_valid
                push!(candidates, cand)
            end
        end
    end
    return candidates
end

"""
Apriori bản cơ bản: Quét lại CSDL ở mỗi mức.
"""
function apriori_basic(transactions::Vector{Vector{Int}}, minsup_abs::Int; max_len::Union{Int, Nothing}=nothing)
    frequent = Dict{Vector{Int}, Int}()
    
    # Mức 1: Đếm item đơn
    counts = Dict{Int, Int}()
    for t in transactions
        for item in t
            counts[item] = get(counts, item, 0) + 1
        end
    end
    
    level = Vector{Vector{Int}}()
    for (item, count) in counts
        if count >= minsup_abs
            push!(level, [item])
            frequent[[item]] = count
        end
    end
    sort!(level)
    
    # Chuyển transactions sang Set để check issubset nhanh hơn
    tsets = [Set(t) for t in transactions]
    
    k = 2
    while !isempty(level) && (isnothing(max_len) || k <= max_len)
        candidates = generate_candidates(level)
        isempty(candidates) && break
        
        cand_counts = Dict{Vector{Int}, Int}()
        for c in candidates
            cand_counts[c] = 0
        end
        
        # Quét CSDL
        for ts in tsets
            length(ts) < k && continue
            for c in candidates
                if issubset(c, ts)
                    cand_counts[c] += 1
                end
            end
        end
        
        level = Vector{Vector{Int}}()
        for c in candidates
            cnt = cand_counts[c]
            if cnt >= minsup_abs
                push!(level, c)
                frequent[c] = cnt
            end
        end
        sort!(level)
        k += 1
    end
    
    return frequent
end

end # module BasicApriori