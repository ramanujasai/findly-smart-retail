
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = ROOT / "data" / "raw" / "Online Retail.xlsx"
PROCESSED_FILE = ROOT / "data" / "processed" / "transactions.csv"
OUTPUT_FILE = ROOT / "data" / "processed" / "transactions_with_dates.csv"


def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Original Excel file not found: {RAW_FILE}")

    if not PROCESSED_FILE.exists():
        raise FileNotFoundError(
            f"Processed CSV not found: {PROCESSED_FILE}"
        )

    print("Loading original Excel dataset...")
    original = pd.read_excel(
        RAW_FILE,
        usecols=["InvoiceNo", "InvoiceDate"]
    )

    original["InvoiceNo"] = original["InvoiceNo"].astype(str)
    original["InvoiceDate"] = pd.to_datetime(
        original["InvoiceDate"], errors="coerce"
    )

    # An invoice should have one invoice date. Use its earliest
    # recorded timestamp and report any invoices with inconsistent dates.
    date_counts = original.groupby("InvoiceNo")["InvoiceDate"].nunique()
    inconsistent = int((date_counts > 1).sum())

    invoice_dates = (
        original.dropna(subset=["InvoiceDate"])
        .groupby("InvoiceNo", as_index=False)["InvoiceDate"]
        .min()
    )

    transactions = pd.read_csv(
        PROCESSED_FILE,
        dtype={"InvoiceNo": str, "StockCode": str}
    )

    transactions["InvoiceNo"] = transactions["InvoiceNo"].astype(str)

    # Validate that each processed invoice can be matched to the source.
    merged = transactions.merge(
        invoice_dates,
        on="InvoiceNo",
        how="left",
        validate="many_to_one"
    )

    unmatched_rows = int(merged["InvoiceDate"].isna().sum())

    if unmatched_rows:
        raise ValueError(
            f"{unmatched_rows:,} rows could not be matched to an invoice date. "
            "No output was saved; investigate the invoice IDs first."
        )

    merged.to_csv(OUTPUT_FILE, index=False)

    print("\nDATE RESTORATION COMPLETE")
    print(f"Processed rows: {len(merged):,}")
    print(f"Matched invoice dates: {merged['InvoiceDate'].nunique():,} "
          "distinct timestamps")
    print(f"Invoices with inconsistent source dates: {inconsistent:,}")
    print(f"Saved to: {OUTPUT_FILE}")
    print("\nYour original transactions.csv was not modified.")


if __name__ == "__main__":
    main()