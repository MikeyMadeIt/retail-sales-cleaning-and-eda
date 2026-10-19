# Retail Store Sales: Data Cleaning Pipeline

Reproducible cleaning of the Kaggle *Retail Store Sales: Dirty for Data Cleaning* dataset.

## Run it

```bash
pip install -r requirements.txt
make all      # raw CSV -> data/clean/*.csv, output/rejected_rows.csv, reports/data_quality_report.md
make test
```

The raw file is checked against `data/raw/SHA256.txt` before anything runs. The output is
deterministic: two runs produce byte-identical clean CSVs.

## Layout

| Path | Purpose |
|---|---|
| `data/raw/` | Untouched source file and its checksum |
| `src/clean.py` | One function per cleaning step |
| `src/pipeline.py` | Orders the steps, states the rationale for each, asserts pre-conditions |
| `src/ledger.py` | Records rows in/out per step; fails if any dropped row is not logged |
| `src/profile.py` | Before/after column profile |
| `src/report.py` | Generates the report from the ledger, so docs cannot drift from code |
| `output/rejected_rows.csv` | Every dropped row, with the step that dropped it |
| `reports/data_quality_report.md` | Generated data quality report |

## Provenance

Source: Kaggle (add the dataset URL, author and licence here, and the date you downloaded it).
The file is included as `data/raw/retail_store_sales.csv`.
