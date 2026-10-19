
from pathlib import Path
import pandas as pd

# Locate and load the dataset
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_DIR / "data" / "raw" / "Online Retail.xlsx"

df = pd.read_excel(DATA_PATH)

print("\n--- CANCELLATION INVOICES ---")
cancelled = df["InvoiceNo"].astype(str).str.startswith("C")
print("Cancellation rows:", cancelled.sum())
print("Percentage:", round(cancelled.mean() * 100, 2), "%")

print("\n--- QUANTITY ANALYSIS ---")
print(df["Quantity"].describe())
print("Zero quantity rows:", (df["Quantity"] == 0).sum())
print("Negative quantity rows:", (df["Quantity"] < 0).sum())

print("\n--- PRICE ANALYSIS ---")
print(df["UnitPrice"].describe())
print("Zero or negative price rows:", (df["UnitPrice"] <= 0).sum())

print("\n--- PRODUCT ANALYSIS ---")
print("Unique stock codes:", df["StockCode"].nunique())
print("Unique descriptions:", df["Description"].nunique())

print("\nTop 10 products by transaction-line frequency:")
print(
    df["Description"]
    .value_counts()
    .head(10)
    .to_string()
)

print("\n--- INVOICE ANALYSIS ---")
print("Unique invoices:", df["InvoiceNo"].nunique())
print("Unique customers:", df["CustomerID"].nunique())
print("Countries:", df["Country"].nunique())

print("\n--- ROWS PER INVOICE ---")
basket_sizes = df.groupby("InvoiceNo")["StockCode"].size()
print(basket_sizes.describe())