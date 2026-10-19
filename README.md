# Findly - Smart Retail Product Discovery

Findly is a small data-mining project built to make exploring a retail catalogue a little more useful. It brings product search, a simple store map, and basket management into one Streamlit web app.

The data-mining part looks at products that appeared together in historical orders. These patterns can help identify items that shoppers may want to explore together. The project is a demonstration, so the suggestions are based on past associations rather than live customer activity or guaranteed future purchases.

## What you can do

- **Product Discovery:** Search the catalogue and view product details.
- **Interactive Store Map:** Browse simulated floors, rows, and shelves and locate products.
- **Basket:** Add or remove products and manage a shopping basket.
- **Project overview:** See basic dataset and association-rule statistics on the home page.

> **A note about the store map:** The dataset does not contain real shelf coordinates. Findly assigns consistent demo locations to products so the map can be explored, but these are not real store locations.

## How it works

1. Product and invoice records are loaded from the processed retail dataset.
2. Frequent itemsets and association rules are mined from historical baskets.
3. The app uses those learned patterns as a data-mining demonstration.
4. Product locations shown in the map are generated for the demo.

The project uses the UCI **Online Retail** dataset, which contains transactions from a UK-based online retailer between December 2010 and December 2011. It is historical data, so the results should not be treated as a description of current shopping behaviour.

## Tech used

- Python
- Streamlit
- pandas
- Association-rule mining
- Git and GitHub

## Run it locally

You will need Python installed.

1. Clone the repository:

   ```bash
   git clone https://github.com/ramanujasai/findly-smart-retail.git
   cd findly-smart-retail
   ```

2. (Recommended) Create and activate a virtual environment:

   **Windows PowerShell**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

If the processed transaction data or association-rule output is missing, the related statistics or features may not work until those files are available. The app expects the processed data and results in the paths used by the source code.

## Project structure

```text
findly-smart-retail/
├── app.py
├── pages/
│   ├── 1_Product_Search.py
│   ├── 2_Store_Map.py
│   └── 3_Basket_Recommendations.py
├── ui/
│   ├── __init__.py
│   └── theme.py
├── data/
│   └── processed/
│       └── transactions.csv
└── results/
    └── association_rules.csv
```

Other folders, such as scripts used for data preparation and experiments, may also be present in the repository.

## Limitations

- The dataset is historical and comes from an online retailer, not a live physical shop.
- The map's floor, row, and shelf assignments are simulated.
- Association rules show relationships in the observed baskets; they do not prove that one product causes another to be purchased.
- Recommendation quality depends on the data, preprocessing choices, and evaluation setup.

## Dataset

Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository.  
https://doi.org/10.24432/C5BW33

## Project status

Findly is an academic project and a work in progress. The goal is to connect data-mining concepts with a small interface that is easy to demonstrate and explore.
