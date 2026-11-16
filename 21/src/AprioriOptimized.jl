module OptimizedApriori

using DataStructures

export apriori_optimized

function build_item_bitsets(transactions::Vector{Vector{Int}})
    num_trans = length(transactions)
    item_bits = Dict{Int, BitVector}()
    
    for (tid, t) in enumerate(transactions)
        for item in t
            if !haskey(item_bits, item)
                item_bits[item] = BitVector(zeros(Bool, num_trans))
            end
            item_bits[item][tid] = true
        end
    end
    return item_bits
end

"""
Apriori Tối Ưu bằng BitVector Dọc trong Julia.
"""
function apriori_optimized(transactions::Vector{Vector{Int}}, minsup_abs::Int; max_len::Union{Int, Nothing}=nothing)
    num_trans = length(transactions)
    item_bits = build_item_bitsets(transactions)
    
    frequent = Dict{Vector{Int}, Int}()
    current_level = Dict{Vector{Int}, BitVector}()
    
    # Mức 1
    for (item, bitset) in item_bits
        sup = sum(bitset) 
        if sup >= minsup_abs
            itemset = [item]
            current_level[itemset] = bitset
            frequent[itemset] = sup
        end
    end
    
    # Giải phóng memory của item_bits ban đầu
    empty!(item_bits)
    
    k = 2
    while !isempty(current_level) && (isnothing(max_len) || k <= max_len)
        # Nhóm theo Prefix (k-2 item đầu)
        sorted_itemsets = sort(collect(keys(current_level)))
        groups = Dict{Vector{Int}, Vector{Vector{Int}}}()
        
        for itemset in sorted_itemsets
            prefix = itemset[1:end-1]
            if !haskey(groups, prefix)
                groups[prefix] = Vector{Vector{Int}}()
            end
            push!(groups[prefix], itemset)
        end
        
        next_level = Dict{Vector{Int}, BitVector}()
        
        for (prefix, group) in groups
            m = length(group)
            for i in 1:m
                a = group[i]
                bs_a = current_level[a]
                for j in (i + 1):m
                    b = group[j]
                    cand = vcat(a, b[end])
                    
                    # Prune (Tỉa nhánh bằng tập con)
                    if k > 2
                        is_valid = true
                        for idx in 1:(k-2) # Chỉ cần check các tập con không chứa 2 item cuối
                            sub = cand[1:end .!= idx]
                            if !haskey(current_level, sub)
                                is_valid = false
                                break
                            end
                        end
                        !is_valid && continue
                    end
                    
                    # Phép AND Bitwise cực nhanh trên BitVector
                    bs_cand = bs_a .& current_level[b]
                    sup = sum(bs_cand)
                    
                    if sup >= minsup_abs
                        next_level[cand] = bs_cand
                        frequent[cand] = sup
                    end
                end
            end
        end
        
        # Giải phóng bộ nhớ level cũ (giảm Peak RAM)
        current_level = next_level
        k += 1
    end
    
    return frequent
end

end # module OptimizedApriori