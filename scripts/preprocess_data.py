
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_DIR / "data" / "raw" / "Online Retail.xlsx"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "transactions.csv"

# Load original data
df = pd.read_excel(INPUT_PATH)

print("Original rows:", len(df))

# 1. Remove exact duplicate records
df = df.drop_duplicates().copy()
print("After removing exact duplicates:", len(df))

# 2. Remove cancellation invoices
is_cancellation = df["InvoiceNo"].astype(str).str.startswith("C")
df = df.loc[~is_cancellation].copy()
print("After removing cancellation invoices:", len(df))

# 3. Keep positive purchase quantities
df = df.loc[df["Quantity"] > 0].copy()
print("After removing non-positive quantities:", len(df))

# 4. Keep valid product identifiers and descriptions
df["Description"] = df["Description"].fillna("").astype(str).str.strip()
df["StockCode"] = df["StockCode"].astype(str).str.strip()

df = df.loc[
    (df["Description"] != "") &
    (df["StockCode"] != "")
].copy()
print("After removing missing product details:", len(df))

# 5. Normalize descriptions
df["Description"] = (
    df["Description"]
    .str.upper()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

# 6. Create invoice-product transaction pairs
# Duplicate invoice/product pairs are collapsed for basket mining.
transactions = (
    df[["InvoiceNo", "StockCode", "Description"]]
    .drop_duplicates(subset=["InvoiceNo", "StockCode"])
    .sort_values(["InvoiceNo", "StockCode"])
    .reset_index(drop=True)
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
transactions.to_csv(OUTPUT_PATH, index=False)

print("\n--- PREPROCESSING SUMMARY ---")
print("Clean transaction-product pairs:", len(transactions))
print("Unique invoices:", transactions["InvoiceNo"].nunique())
print("Unique products:", transactions["StockCode"].nunique())
print("Saved to:", OUTPUT_PATH)

basket_sizes = transactions.groupby("InvoiceNo")["StockCode"].nunique()
print("\nProducts per invoice:")
print(basket_sizes.describe())