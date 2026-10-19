
from pathlib import Path
import ast
import re

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules


# --------------------------------------------------
# 1. Project paths and settings
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

TRANSACTIONS_FILE = ROOT / "data" / "processed" / "transactions.csv"
RULES_FILE = ROOT / "results" / "association_rules.csv"
OUTPUT_DIR = ROOT / "results"

SUPPORT_THRESHOLDS = [0.01, 0.015, 0.02]
MIN_CONFIDENCE = 0.30
TOP_RULES = 20


# --------------------------------------------------
# 2. Helpers
# --------------------------------------------------

def parse_itemset(value):
    """Read stock codes from mlxtend's frozenset text."""
    if pd.isna(value):
        return set()

    # Stock codes are stored as quoted strings in the CSV.
    return set(re.findall(r"""['"]([^'"]+)['"]""", str(value)))


def describe_items(items, descriptions):
    """Convert stock codes into readable product descriptions."""
    names = []

    for code in sorted(items):
        name = descriptions.get(code, f"Unknown product ({code})")
        names.append(f"{name} [{code}]")

    return " + ".join(names)


def load_descriptions(transactions):
    """Build a stock-code-to-description dictionary."""
    result = {}

    for _, row in transactions[["StockCode", "Description"]].dropna().iterrows():
        code = str(row["StockCode"]).strip()
        description = str(row["Description"]).strip()

        if code and description and code not in result:
            result[code] = description

    return result


# --------------------------------------------------
# 3. Load the existing data
# --------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not TRANSACTIONS_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {TRANSACTIONS_FILE}"
        )

    if not RULES_FILE.exists():
        raise FileNotFoundError(
            f"Association rules file not found: {RULES_FILE}"
        )

    transactions = pd.read_csv(
        TRANSACTIONS_FILE,
        dtype={"InvoiceNo": str, "StockCode": str}
    )

    rules = pd.read_csv(RULES_FILE)

    required_columns = {
        "InvoiceNo", "StockCode", "Description"
    }

    missing = required_columns - set(transactions.columns)

    if missing:
        raise ValueError(
            f"Missing columns in transactions.csv: {sorted(missing)}"
        )

    descriptions = load_descriptions(transactions)

    print("=" * 65)
    print("FINDLY: ASSOCIATION PATTERN INSPECTION")
    print("=" * 65)
    print(f"Transaction-product rows: {len(transactions):,}")
    print(f"Unique invoices: {transactions['InvoiceNo'].nunique():,}")
    print(f"Unique products: {transactions['StockCode'].nunique():,}")
    print(f"Existing association rules: {len(rules):,}")

    # --------------------------------------------------
    # 4. Inspect the strongest existing rules
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("TOP RULES AFTER REMOVING DISPLAY DUPLICATES")
    print("=" * 65)

    rules["antecedent_items"] = rules["antecedents"].apply(parse_itemset)
    rules["consequent_items"] = rules["consequents"].apply(parse_itemset)

    # Discard malformed rules and rules whose product codes
    # are no longer present in the processed dataset.
    known_codes = set(transactions["StockCode"].dropna().astype(str))

    rules = rules[
        rules["antecedent_items"].map(bool)
        & rules["consequent_items"].map(bool)
    ].copy()

    rules = rules[
        rules.apply(
            lambda row: (
                row["antecedent_items"] | row["consequent_items"]
            ).issubset(known_codes),
            axis=1
        )
    ].copy()

    rules["all_items"] = rules.apply(
        lambda row: tuple(sorted(
            row["antecedent_items"] | row["consequent_items"]
        )),
        axis=1
    )

    rules = rules.sort_values(
        ["lift", "confidence", "support"],
        ascending=False
    )

    # Keep the strongest direction for each identical group of
    # products so the terminal is easier to read.
    display_rules = rules.drop_duplicates(
        subset=["all_items"], keep="first"
    ).head(TOP_RULES).copy()

    display_rules["IF_PRODUCTS"] = display_rules.apply(
        lambda row: describe_items(
            row["antecedent_items"], descriptions
        ),
        axis=1
    )

    display_rules["THEN_RECOMMEND"] = display_rules.apply(
        lambda row: describe_items(
            row["consequent_items"], descriptions
        ),
        axis=1
    )

    display_rules["support_percent"] = (
        display_rules["support"] * 100
    ).round(3)

    display_rules["confidence_percent"] = (
        display_rules["confidence"] * 100
    ).round(2)

    display_rules["lift"] = display_rules["lift"].round(2)

    for index, (_, row) in enumerate(display_rules.iterrows(), start=1):
        print(f"\n{index}. IF: {row['IF_PRODUCTS']}")
        print(f"   THEN: {row['THEN_RECOMMEND']}")
        print(f"   Support: {row['support_percent']}%")
        print(f"   Confidence: {row['confidence_percent']}%")
        print(f"   Lift: {row['lift']}")

    export_columns = [
        "IF_PRODUCTS",
        "THEN_RECOMMEND",
        "support",
        "confidence",
        "lift",
    ]

    display_rules[export_columns].to_csv(
        OUTPUT_DIR / "pattern_review_top_rules.csv",
        index=False
    )

    print("\nSaved readable rules:")
    print(OUTPUT_DIR / "pattern_review_top_rules.csv")

    # --------------------------------------------------
    # 5. Investigate large invoices
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("LARGE INVOICE INVESTIGATION")
    print("=" * 65)

    invoice_sizes = (
        transactions.groupby("InvoiceNo")["StockCode"]
        .nunique()
        .sort_values(ascending=False)
        .rename("unique_products")
        .reset_index()
    )

    invoice_sizes["is_large_50"] = (
        invoice_sizes["unique_products"] > 50
    )

    invoice_sizes["is_large_100"] = (
        invoice_sizes["unique_products"] > 100
    )

    total_invoices = len(invoice_sizes)

    print(f"Invoices with more than 50 products: "
          f"{invoice_sizes['is_large_50'].sum():,} "
          f"({invoice_sizes['is_large_50'].mean() * 100:.2f}%)")

    print(f"Invoices with more than 100 products: "
          f"{invoice_sizes['is_large_100'].sum():,} "
          f"({invoice_sizes['is_large_100'].mean() * 100:.2f}%)")

    print("\nLargest 10 invoices:")
    print(invoice_sizes.head(10).to_string(index=False))

    invoice_sizes.to_csv(
        OUTPUT_DIR / "large_invoice_summary.csv",
        index=False
    )

    # --------------------------------------------------
    # 6. Support-threshold sensitivity experiment
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("SUPPORT-THRESHOLD SENSITIVITY")
    print("=" * 65)

    # One row per invoice, one column per product.
    basket = pd.crosstab(
        transactions["InvoiceNo"],
        transactions["StockCode"]
    ).gt(0)

    print(f"Basket matrix: {basket.shape[0]:,} invoices x "
          f"{basket.shape[1]:,} products")

    sensitivity_results = []

    for min_support in SUPPORT_THRESHOLDS:
        print(f"\nTesting minimum support = {min_support:.3f}...")

        frequent = fpgrowth(
            basket,
            min_support=min_support,
            use_colnames=True
        )

        if frequent.empty:
            print("No frequent itemsets found at this threshold.")
            sensitivity_results.append({
                "min_support": min_support,
                "frequent_itemsets": 0,
                "association_rules": 0,
                "rules_with_lift_over_1": 0,
                "max_lift": None,
            })
            continue

        frequent["itemset_size"] = frequent["itemsets"].apply(len)

        multi_itemsets = frequent[
            frequent["itemset_size"] >= 2
        ]

        if multi_itemsets.empty:
            generated_rules = pd.DataFrame()
        else:
            generated_rules = association_rules(
                frequent,
                metric="confidence",
                min_threshold=MIN_CONFIDENCE
            )

        if generated_rules.empty:
            rules_over_one = 0
            max_lift = None
        else:
            rules_over_one = int(
                (generated_rules["lift"] > 1).sum()
            )
            max_lift = round(
                float(generated_rules["lift"].max()), 3
            )

        result = {
            "min_support": min_support,
            "frequent_itemsets": len(frequent),
            "association_rules": len(generated_rules),
            "rules_with_lift_over_1": rules_over_one,
            "max_lift": max_lift,
        }

        sensitivity_results.append(result)

        print(f"Frequent itemsets: {len(frequent):,}")
        print(f"Association rules: {len(generated_rules):,}")
        print(f"Rules with lift > 1: {rules_over_one:,}")
        print(f"Maximum lift: {max_lift}")

    sensitivity = pd.DataFrame(sensitivity_results)

    sensitivity.to_csv(
        OUTPUT_DIR / "support_sensitivity.csv",
        index=False
    )

    print("\nSensitivity results:")
    print(sensitivity.to_string(index=False))

    print("\nSaved support comparison:")
    print(OUTPUT_DIR / "support_sensitivity.csv")

    print("\n" + "=" * 65)
    print("INSPECTION COMPLETE")
    print("Review all three CSV files in the results folder.")
    print("=" * 65)


if __name__ == "__main__":
    main()