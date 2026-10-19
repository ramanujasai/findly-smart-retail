
from pathlib import Path
import random

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "transactions_with_dates.csv"
OUTPUT_DIR = ROOT / "results"

TRAIN_RATIO = 0.80
MIN_SUPPORT = 0.01
MIN_CONFIDENCE = 0.30
TOP_K = 5
HOLDOUT_RATIO = 0.20
RANDOM_SEED = 42


def build_basket(data):
    return pd.crosstab(
        data["InvoiceNo"], data["StockCode"]
    ).gt(0)


def mine_rules(basket):
    itemsets = fpgrowth(
        basket, min_support=MIN_SUPPORT, use_colnames=True
    )

    if itemsets.empty or not (itemsets["itemsets"].map(len) >= 2).any():
        return pd.DataFrame()

    return association_rules(
        itemsets, metric="confidence",
        min_threshold=MIN_CONFIDENCE
    )


def recommend(rules, context, known_products):
    scores = {}

    if rules.empty:
        return []

    for _, rule in rules.iterrows():
        antecedents = set(rule["antecedents"])
        consequents = set(rule["consequents"])

        if antecedents and antecedents.issubset(context):
            for product in consequents - context:
                if product in known_products:
                    score = (
                        float(rule["confidence"]),
                        float(rule["lift"])
                    )
                    if product not in scores or score > scores[product]:
                        scores[product] = score

    ranked = sorted(
        scores.items(),
        key=lambda entry: (entry[1][0], entry[1][1]),
        reverse=True
    )
    return [product for product, _ in ranked[:TOP_K]]


def main():
    data = pd.read_csv(
        DATA_FILE,
        dtype={"InvoiceNo": str, "StockCode": str},
        parse_dates=["InvoiceDate"]
    ).dropna(subset=["InvoiceNo", "StockCode", "InvoiceDate"])

    invoice_dates = (
        data.groupby("InvoiceNo")["InvoiceDate"]
        .min()
        .sort_values()
    )

    split = int(len(invoice_dates) * TRAIN_RATIO)
    train_ids = set(invoice_dates.iloc[:split].index)
    test_ids = set(invoice_dates.iloc[split:].index)

    train = data[data["InvoiceNo"].isin(train_ids)]
    test = data[data["InvoiceNo"].isin(test_ids)]

    train_basket = build_basket(train)
    test_basket = build_basket(test)
    rules = mine_rules(train_basket)

    known_products = set(train_basket.columns)
    popularity = train_basket.sum().sort_values(ascending=False).index.tolist()
    rng = random.Random(RANDOM_SEED)

    evaluated = 0
    total_hits = 0
    total_recommended = 0
    total_relevant = 0
    baskets_with_hits = 0
    reciprocal_rank_sum = 0.0

    baseline_hits = 0
    baseline_recommended = 0
    baseline_baskets_with_hits = 0

    association_covered = 0
    baseline_covered = 0
    detail_rows = []

    for invoice_id in test_basket.index:
        actual = set(test_basket.columns[test_basket.loc[invoice_id]])
        eligible = sorted(actual & known_products)

        if len(eligible) < 2:
            continue

        rng.shuffle(eligible)
        target_count = max(1, round(len(eligible) * HOLDOUT_RATIO))
        target_count = min(target_count, len(eligible) - 1)

        target = set(eligible[:target_count])
        context = set(eligible[target_count:])

        recommendations = recommend(rules, context, known_products)

        # Compare the baseline at the same recommendation-list length.
        # This avoids penalizing either method for a shorter list.
        baseline = [
            product for product in popularity if product not in context
        ][:len(recommendations)]

        if recommendations:
            association_covered += 1
        if baseline:
            baseline_covered += 1

        hits = set(recommendations) & target
        baseline_hit_items = set(baseline) & target

        evaluated += 1
        total_hits += len(hits)
        total_relevant += len(target)
        total_recommended += len(recommendations)

        if hits:
            baskets_with_hits += 1
            first_rank = next(
                rank for rank, product in enumerate(recommendations, 1)
                if product in target
            )
            reciprocal_rank_sum += 1 / first_rank

        baseline_hits += len(baseline_hit_items)
        baseline_recommended += len(baseline)

        if baseline_hit_items:
            baseline_baskets_with_hits += 1

        detail_rows.append({
            "InvoiceNo": invoice_id,
            "context_products": len(context),
            "heldout_products": len(target),
            "recommendations": " | ".join(recommendations),
            "hits": len(hits),
            "baseline_recommendations": " | ".join(baseline),
            "baseline_hits": len(baseline_hit_items),
        })

    summary = {
        "train_invoices": len(train_basket),
        "test_invoices": len(test_basket),
        "rules_learned": len(rules),
        "evaluated_invoices": evaluated,
        "k": TOP_K,
        "precision_at_k": total_hits / total_recommended
            if total_recommended else 0.0,
        "recall_at_k": total_hits / total_relevant
            if total_relevant else 0.0,
        "hit_rate_at_k": baskets_with_hits / evaluated
            if evaluated else 0.0,
        "mean_reciprocal_rank": reciprocal_rank_sum / evaluated
            if evaluated else 0.0,
        "popularity_baseline_precision": baseline_hits / baseline_recommended
            if baseline_recommended else 0.0,
        "popularity_baseline_hit_rate": baseline_baskets_with_hits / evaluated
            if evaluated else 0.0,
        "association_coverage": association_covered / evaluated
            if evaluated else 0.0,
        "baseline_coverage": baseline_covered / evaluated
            if evaluated else 0.0,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summary]).to_csv(
        OUTPUT_DIR / "recommendation_evaluation_summary.csv",
        index=False
    )
    pd.DataFrame(detail_rows).to_csv(
        OUTPUT_DIR / "recommendation_evaluation_details.csv",
        index=False
    )

    print("=" * 65)
    print("FINDLY: FAIRER RECOMMENDATION EVALUATION")
    print("=" * 65)
    print(f"Training invoices: {len(train_basket):,}")
    print(f"Testing invoices: {len(test_basket):,}")
    print(f"Rules learned: {len(rules):,}")
    print("\nEVALUATION RESULTS")
    print(pd.DataFrame([summary]).to_string(index=False))
    print("\nResults saved in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()