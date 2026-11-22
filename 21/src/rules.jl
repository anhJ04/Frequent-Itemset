module Rules

export AssociationRule, generate_rules

"""
Luật kết hợp X ⇒ Y sinh từ tập phổ biến (dùng cho Ứng dụng 1: Market Basket Analysis).

    support(X ⇒ Y)    = sup(X ∪ Y) / N
    confidence(X ⇒ Y) = sup(X ∪ Y) / sup(X)
    lift(X ⇒ Y)       = confidence(X ⇒ Y) / (sup(Y) / N)
"""
struct AssociationRule
    antecedent::Vector{Int}
    consequent::Vector{Int}
    support::Float64
    confidence::Float64
    lift::Float64
end

"""
    generate_rules(frequent, n, minconf) -> Vector{AssociationRule}

Với mỗi tập phổ biến Z (|Z| ≥ 2), duyệt mọi cách chia Z = X ∪ Y (X, Y khác rỗng, rời nhau)
bằng bitmask. Theo tính chất Apriori, mọi tập con của Z đều phổ biến nên sup(X), sup(Y)
luôn tra được trực tiếp trong `frequent` mà không cần quét lại CSDL.
Kết quả sắp theo lift giảm dần, rồi confidence giảm dần (thứ tự xác định).
"""
function generate_rules(frequent::Dict{Vector{Int},Int}, n::Int, minconf::Float64)
    rules = AssociationRule[]
    for (itemset, sup_xy) in frequent
        k = length(itemset)
        k < 2 && continue
        for mask in 1:((1 << k) - 2)
            in_x = [((mask >> (i - 1)) & 1) == 1 for i in 1:k]
            x = itemset[in_x]                    # giữ thứ tự tăng dần của itemset
            y = itemset[.!in_x]
            conf = sup_xy / frequent[x]
            conf < minconf && continue
            lift = conf / (frequent[y] / n)
            push!(rules, AssociationRule(x, y, sup_xy / n, conf, lift))
        end
    end
    sort!(rules, by = r -> (-r.lift, -r.confidence, r.antecedent, r.consequent))
    return rules
end

end # module Rules
