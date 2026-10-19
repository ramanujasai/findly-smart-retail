
from pathlib import Path
import pandas as pd

# Locate the dataset
project_dir = Path(__file__).resolve().parent.parent
data_path = project_dir / "data" / "raw" / "Online Retail.xlsx"

if not data_path.exists():
    print("Dataset not found!")
    print(f"Expected location: {data_path}")
    raise SystemExit(1)

# Load the dataset
df = pd.read_excel(data_path)

# Inspect the data
print("\n--- DATASET SHAPE ---")
print(df.shape)

print("\n--- COLUMN NAMES ---")
print(df.columns.tolist())

print("\n--- FIRST 5 ROWS ---")
print(df.head())

print("\n--- MISSING VALUES ---")
print(df.isnull().sum())

print("\n--- DUPLICATE ROWS ---")
print(df.duplicated().sum())

print("\n--- DATA TYPES ---")
print(df.dtypes)