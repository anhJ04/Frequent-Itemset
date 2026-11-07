module Utils

export read_spmf, write_spmf

"""
Đọc file CSDL định dạng SPMF.
Trả về: Array{Vector{Int}, 1} (danh sách các giao dịch).
"""
function read_spmf(filepath::String)::Vector{Vector{Int}}
    transactions = Vector{Vector{Int}}()
    open(filepath, "r") do f
        for line in eachline(f)
            line = strip(line)
            isempty(line) && continue
            # Đọc các item integer và sắp xếp
            items = parse.(Int, split(line))
            sort!(items)
            unique!(items)
            push!(transactions, items)
        end
    end
    return transactions
end

"""
Ghi tập phổ biến ra file chuẩn định dạng SPMF.
Itemset dạng Vector{Int}, support dạng Int.
"""
function write_spmf(filepath::String, frequent_itemsets::Dict{Vector{Int}, Int})
    open(filepath, "w") do f
        # Sắp xếp các tập phổ biến theo độ dài và theo item
        sorted_keys = sort(collect(keys(frequent_itemsets)), by = x -> (length(x), x))
        for itemset in sorted_keys
            sup = frequent_itemsets[itemset]
            line_str = join(itemset, " ") * " #SUP: " * string(sup)
            println(f, line_str)
        end
    end
end

end # module Utils