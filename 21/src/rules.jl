"""Sinh luật kết hợp từ tập phổ biến (dùng cho Ứng dụng 1: Market Basket Analysis)."""
from itertools import combinations


def generate_rules(frequent, n_transactions, min_conf=0.5):
    """Trả về list dict: antecedent, consequent, support, confidence, lift.

    support(X->Y)    = sup(X ∪ Y) / N
    confidence(X->Y) = sup(X ∪ Y) / sup(X)
    lift(X->Y)       = confidence / (sup(Y)/N)
    Mọi tập con của tập phổ biến đều phổ biến (tính chất Apriori) nên luôn tra được sup.
    """
    rules = []
    for itemset, sup_xy in frequent.items():
        if len(itemset) < 2:
            continue
        for r in range(1, len(itemset)):
            for ante in combinations(itemset, r):
                cons = tuple(i for i in itemset if i not in ante)
                conf = sup_xy / frequent[ante]
                if conf >= min_conf:
                    lift = conf / (frequent[cons] / n_transactions)
                    rules.append({
                        "antecedent": ante,
                        "consequent": cons,
                        "support": sup_xy / n_transactions,
                        "confidence": conf,
                        "lift": lift,
                    })
    rules.sort(key=lambda r: (-r["lift"], -r["confidence"]))
    return rules
