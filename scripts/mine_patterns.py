
from pathlib import Path
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_DIR / "data" / "processed" / "transactions.csv"
OUTPUT_DIR = PROJECT_DIR / "results"

# Initial experiment settings
MIN_SUPPORT = 0.01
MIN_CONFIDENCE = 0.30

print("Loading preprocessed transactions...")
df = pd.read_csv(INPUT_PATH, dtype={"InvoiceNo": str, "StockCode": str})

# Inspect unusually large invoices before interpreting results.
basket_sizes = df.groupby("InvoiceNo")["StockCode"].nunique()
print("\nInvoice basket-size summary:")
print(basket_sizes.describe())

print("\nLargest 10 invoices:")
print(basket_sizes.nlargest(10).to_string())

# Build invoice-product binary matrix.
# A True value means the product appeared in that invoice.
print("\nBuilding basket matrix...")
basket = (
    df.assign(present=1)
    .pivot_table(
        index="InvoiceNo",
        columns="StockCode",
        values="present",
        aggfunc="max",
        fill_value=0,
    )
    .astype(bool)
)

print("Basket matrix shape:", basket.shape)

# Mine frequent itemsets using FP-Growth.
print(f"\nRunning FP-Growth with min_support={MIN_SUPPORT}...")
itemsets = fpgrowth(
    basket,
    min_support=MIN_SUPPORT,
    use_colnames=True,
)

print("Frequent itemsets found:", len(itemsets))

if itemsets.empty:
    print("No itemsets found. Lower the support threshold for another experiment.")
    raise SystemExit(0)

itemsets["itemset_size"] = itemsets["itemsets"].apply(len)
itemsets = itemsets.sort_values(
    ["support", "itemset_size"], ascending=[False, False]
)

print("\nTop frequent itemsets:")
print(itemsets.head(15).to_string(index=False))

# Generate association rules.
rules = association_rules(
    itemsets,
    metric="confidence",
    min_threshold=MIN_CONFIDENCE,
)

if rules.empty:
    print("\nNo rules found at this confidence threshold.")
else:
    rules = rules.sort_values(
        ["lift", "confidence", "support"],
        ascending=False,
    )

    print("\nTop 15 rules by lift:")
    print(
        rules[
            ["antecedents", "consequents", "support", "confidence", "lift"]
        ].head(15).to_string(index=False)
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
itemsets.to_csv(OUTPUT_DIR / "frequent_itemsets.csv", index=False)

if not rules.empty:
    rules.to_csv(OUTPUT_DIR / "association_rules.csv", index=False)

print("\nSaved frequent itemsets to results/frequent_itemsets.csv")
if not rules.empty:
    print("Saved association rules to results/association_rules.csv")