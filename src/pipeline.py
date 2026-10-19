"""One command: python -m src.pipeline   (or `make all`)."""
import hashlib
from pathlib import Path
import pandas as pd

from . import clean as C
from .ledger import Ledger
from .profile import profile
from .report import render

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/retail_store_sales.csv"
SHA = ROOT / "data/raw/SHA256.txt"


def main():
    sha = hashlib.sha256(RAW.read_bytes()).hexdigest()
    assert sha == SHA.read_text().strip(), "raw file changed; checksum mismatch"

    raw = C.load_raw(RAW)
    before = profile(C.standardise_blanks(raw)[0], "transaction_id")  # blanks counted as missing

    # Pre-condition checks that justify the recovery steps below.
    typed = C.cast_types(C.standardise_blanks(raw)[0])[0]
    full = typed.dropna(subset=C.AMOUNTS)
    n_mismatch = int(((full.price_per_unit * full.quantity - full.total_spent).abs() > 1e-9).sum())
    assert n_mismatch == 0, "price * quantity != total on complete rows"
    checks = [f"`price_per_unit * quantity == total_spent` on all {len(full):,} complete rows "
              f"({n_mismatch} mismatches).",
              "(`category`, `price_per_unit`) maps to exactly one `item` on all complete rows "
              "(asserted in `infer_item`).",
              "Every `transaction_date` parses with the single format `%Y-%m-%d` (parse failures are rejected, not coerced)."]

    L = Ledger()
    df = raw
    steps = [
        ("Standardise blanks", "Trim whitespace and convert empty strings to real nulls so that 'missing' means one thing "
         "everywhere. Raw file stores missing values as empty strings.", C.standardise_blanks),
        ("Parse types", "Dates parsed with one explicit format; numbers via `to_numeric`; discount mapped from "
         "'True'/'False'. Anything non-null that fails to parse would be rejected rather than silently nulled.",
         C.cast_types),
        ("Reject impossible values", "Non-positive price/quantity/total, malformed IDs or missing dates cannot be valid "
         "retail transactions. None found in this file, but the rule is enforced on every run.", C.drop_invalid_values),
        ("Remove duplicates", "Exact duplicate rows and repeated transaction IDs (first kept). Transaction ID is the "
         "primary key. None found, and no rows are identical apart from their ID.", C.drop_duplicates),
        ("Recover price/quantity/total by arithmetic", "Where exactly one of the three is missing, it is computed from "
         "the other two using `total = price * quantity` (verified exact on every complete row). Flags "
         "`*_was_imputed` mark these cells. Nothing is estimated.", C.recover_by_arithmetic),
        ("Infer missing item", "`(category, price_per_unit)` determines `item` uniquely, so missing items are looked up "
         "from complete rows, after price recovery. Flag `item_was_inferred` marks them.", C.infer_item),
        ("Drop rows with unrecoverable amounts", "Rows missing both quantity and total cannot be completed: price alone "
         "does not determine either. Imputing a median quantity would fabricate transaction values, so these rows are "
         "dropped and kept in `output/rejected_rows.csv`.", C.drop_unrecoverable_amounts),
    ]
    for name, why, fn in steps:
        df = L.run(df, name, why, fn)

    # Decision 7 (no step): discount_applied stays null where unknown. Documented in the report.
    L.steps.append(type(L.steps[0])("Leave discount_applied null where unknown",
        "About a third of values are missing and nothing in the row determines them (total is price*quantity regardless "
        "of discount). Imputing True/False would invent a signal, so the column is kept as a nullable boolean and "
        "the limitation is reported.", len(df), len(df), 0))

    out = df.sort_values("transaction_date").reset_index(drop=True)
    assert out["transaction_id"].is_unique and not out[C.AMOUNTS + ["item"]].isna().any().any()

    rejected = L.rejected()
    assert len(raw) - len(rejected) == len(out), "raw - dropped != clean"

    bias = None
    if len(rejected):
        kept = out["category"].value_counts(normalize=True).rename("kept")
        drop = rejected["category"].value_counts(normalize=True).rename("dropped")
        bias = (pd.concat([kept, drop], axis=1).fillna(0) * 100).round(1).astype(str) + "%"

    after = profile(out, "transaction_id")
    (ROOT / "data/clean").mkdir(exist_ok=True); (ROOT / "output").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    out.to_csv(ROOT / "data/clean/retail_store_sales_clean.csv", index=False)
    rejected.to_csv(ROOT / "output/rejected_rows.csv", index=False)
    (ROOT / "reports/data_quality_report.md").write_text(
        render({"sha": sha}, before, after, L, rejected, bias, checks))
    print(f"raw {len(raw):,} -> clean {len(out):,} rows; {len(rejected):,} rejected. Report written.")


if __name__ == "__main__":
    main()
