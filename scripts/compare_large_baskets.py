
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "transactions.csv"
OUTPUT_DIR = ROOT / "results"

MIN_SUPPORT = 0.01
MIN_CONFIDENCE = 0.30
MAX_PRODUCTS = 50


def mine_rules(transactions, label):
    """Mine frequent itemsets and association rules."""
    basket = pd.crosstab(
        transactions["InvoiceNo"],
        transactions["StockCode"]
    ).gt(0)

    frequent = fpgrowth(
        basket,
        min_support=MIN_SUPPORT,
        use_colnames=True
    )

    if frequent.empty or not (frequent["itemsets"].map(len) >= 2).any():
        rules = pd.DataFrame()
    else:
        rules = association_rules(
            frequent,
            metric="confidence",
            min_threshold=MIN_CONFIDENCE
        )

    print(f"\n--- {label} ---")
    print(f"Invoices: {len(basket):,}")
    print(f"Products: {basket.shape[1]:,}")
    print(f"Frequent itemsets: {len(frequent):,}")
    print(f"Association rules: {len(rules):,}")

    if rules.empty:
        return frequent, rules

    print(f"Rules with lift > 1: {(rules['lift'] > 1).sum():,}")
    print(f"Maximum lift: {rules['lift'].max():.3f}")

    return frequent, rules


def readable_rules(rules, descriptions, label):
    """Create readable rule output."""
    if rules.empty:
        return pd.DataFrame()

    result = rules.copy()

    def describe(itemset):
        names = []
        for code in sorted(itemset):
            names.append(
                descriptions.get(str(code), f"Unknown ({code})")
            )
        return " + ".join(names)

    result["antecedents_text"] = result["antecedents"].apply(describe)
    result["consequents_text"] = result["consequents"].apply(describe)
    result["experiment"] = label

    columns = [
        "experiment",
        "antecedents_text",
        "consequents_text",
        "support",
        "confidence",
        "lift",
    ]

    return result[columns].sort_values(
        ["lift", "confidence", "support"],
        ascending=False
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    transactions = pd.read_csv(
        DATA_FILE,
        dtype={"InvoiceNo": str, "StockCode": str}
    )

    required = {"InvoiceNo", "StockCode", "Description"}
    missing = required - set(transactions.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    transactions["InvoiceNo"] = transactions["InvoiceNo"].astype(str)
    transactions["StockCode"] = transactions["StockCode"].astype(str)

    descriptions = (
        transactions.dropna(subset=["Description"])
        .drop_duplicates("StockCode")
        .set_index("StockCode")["Description"]
        .astype(str)
        .to_dict()
    )

    # Count distinct products in each invoice.
    invoice_sizes = transactions.groupby("InvoiceNo")["StockCode"].nunique()

    normal_invoice_ids = invoice_sizes[
        invoice_sizes <= MAX_PRODUCTS
    ].index

    filtered = transactions[
        transactions["InvoiceNo"].isin(normal_invoice_ids)
    ].copy()

    print("=" * 65)
    print("FINDLY: LARGE-BASKET SENSITIVITY EXPERIMENT")
    print("=" * 65)
    print(f"Original invoices: {len(invoice_sizes):,}")
    print(f"Invoices with <= {MAX_PRODUCTS} products: "
          f"{len(normal_invoice_ids):,}")
    print(f"Excluded invoices: "
          f"{len(invoice_sizes) - len(normal_invoice_ids):,}")
    print(f"Minimum support: {MIN_SUPPORT:.1%}")
    print(f"Minimum confidence: {MIN_CONFIDENCE:.0%}")

    # Baseline: all invoices.
    _, all_rules = mine_rules(transactions, "all_invoices")

    # Sensitivity check: remove large invoices.
    _, filtered_rules = mine_rules(
        filtered, f"at_most_{MAX_PRODUCTS}_products"
    )

    # Save the strongest readable rules from each experiment.
    readable_all = readable_rules(
        all_rules, descriptions, "all_invoices"
    )
    readable_filtered = readable_rules(
        filtered_rules,
        descriptions,
        f"at_most_{MAX_PRODUCTS}_products"
    )

    combined = pd.concat(
        [readable_all, readable_filtered],
        ignore_index=True
    )

    combined.to_csv(
        OUTPUT_DIR / "large_basket_rule_comparison.csv",
        index=False
    )

    # Summarize each experiment for easy reporting.
    summary = []

    for label, rules in [
        ("all_invoices", all_rules),
        (f"at_most_{MAX_PRODUCTS}_products", filtered_rules),
    ]:
        summary.append({
            "experiment": label,
            "invoice_count": (
                len(invoice_sizes)
                if label == "all_invoices"
                else len(normal_invoice_ids)
            ),
            "rule_count": len(rules),
            "rules_with_lift_over_1": (
                int((rules["lift"] > 1).sum())
                if not rules.empty else 0
            ),
            "maximum_lift": (
                round(float(rules["lift"].max()), 3)
                if not rules.empty else None
            ),
        })

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(
        OUTPUT_DIR / "large_basket_experiment_summary.csv",
        index=False
    )

    print("\n" + "=" * 65)
    print("EXPERIMENT COMPARISON")
    print("=" * 65)
    print(summary_df.to_string(index=False))

    print("\nSaved:")
    print(OUTPUT_DIR / "large_basket_experiment_summary.csv")
    print(OUTPUT_DIR / "large_basket_rule_comparison.csv")


if __name__ == "__main__":
    main()