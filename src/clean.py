"""Cleaning steps. Each returns (clean_df, dropped_df_or_None, cells_changed) and is
registered in pipeline.py with a rationale string that ends up in the report."""
import numpy as np
import pandas as pd

RENAME = {
    "Transaction ID": "transaction_id", "Customer ID": "customer_id", "Category": "category",
    "Item": "item", "Price Per Unit": "price_per_unit", "Quantity": "quantity",
    "Total Spent": "total_spent", "Payment Method": "payment_method", "Location": "location",
    "Transaction Date": "transaction_date", "Discount Applied": "discount_applied",
}
AMOUNTS = ["price_per_unit", "quantity", "total_spent"]


def load_raw(path):
    # Everything as string: no silent type inference; blanks stay visible until we decide.
    return pd.read_csv(path, dtype=str, keep_default_na=False).rename(columns=RENAME)


def standardise_blanks(df):
    """Trim whitespace; turn blank strings into real nulls."""
    out, changed = df.copy(), 0
    for c in out.columns:
        s = out[c].str.strip()
        s = s.mask(s == "", np.nan)
        changed += int((s.fillna("<NA>") != out[c].fillna("<NA>")).sum())
        out[c] = s
    return out, None, changed


def cast_types(df):
    """Explicit parsing. Rows that fail to parse are rejected, never coerced silently."""
    out = df.copy()
    for c in AMOUNTS:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["transaction_date"] = pd.to_datetime(out["transaction_date"], format="%Y-%m-%d", errors="coerce")
    out["discount_applied"] = out["discount_applied"].map({"True": True, "False": False}).astype("boolean")
    bad = pd.Series(False, index=df.index)
    for c in AMOUNTS + ["transaction_date", "discount_applied"]:
        bad |= df[c].notna() & out[c].isna()
    out["quantity"] = out["quantity"].astype("Int64")
    return out[~bad], df[bad], 0


def drop_invalid_values(df):
    """Impossible values: non-positive money/quantity, malformed IDs, null dates."""
    bad = (
        (df["price_per_unit"] <= 0) | (df["quantity"] <= 0) | (df["total_spent"] <= 0)
        | ~df["transaction_id"].str.match(r"^TXN_\d{7}$", na=False)
        | ~df["customer_id"].str.match(r"^CUST_\d{2}$", na=False)
        | df["transaction_date"].isna()
    ).fillna(False)
    return df[~bad], df[bad], 0


def drop_duplicates(df):
    """Exact duplicates, then conflicting duplicates on the primary key (keep first)."""
    dup = df.duplicated(keep="first") | df.duplicated(subset="transaction_id", keep="first")
    return df[~dup], df[dup], 0


def recover_by_arithmetic(df):
    """total_spent == price_per_unit * quantity holds on every complete row (asserted in
    pipeline.py), so a single missing value among the three is recoverable, not guessed."""
    out = df.copy()
    for c in AMOUNTS:
        out[f"{c}_was_imputed"] = False
    one = out[AMOUNTS].isna().sum(axis=1) == 1

    price = out["price_per_unit"].astype(float)
    qty = out["quantity"].astype(float)      # NaN-aware float working copies
    total = out["total_spent"].astype(float)

    m_total = (one & total.isna()).to_numpy()
    m_price = (one & price.isna()).to_numpy()
    m_qty = (one & qty.isna()).to_numpy()
    total[m_total] = (price * qty)[m_total]
    price[m_price] = (total / qty)[m_price]
    qty[m_qty] = (total / price)[m_qty]
    assert (qty[m_qty].round() == qty[m_qty]).all(), "recovered quantity is not an integer"

    out["price_per_unit"], out["total_spent"] = price, total
    out["quantity"] = qty.round().astype("Int64")
    out["total_spent_was_imputed"] = m_total
    out["price_per_unit_was_imputed"] = m_price
    out["quantity_was_imputed"] = m_qty
    return out, None, int(one.sum())


def infer_item(df):
    """(category, price_per_unit) -> item is strictly 1:1 on complete rows (asserted),
    so a missing item is looked up from that mapping, not guessed."""
    known = df.dropna(subset=["item", "price_per_unit"])
    assert (known.groupby(["category", "price_per_unit"])["item"].nunique() == 1).all(), \
        "ambiguous (category, price) -> item mapping"
    lookup = known.drop_duplicates(["category", "price_per_unit"]).set_index(
        ["category", "price_per_unit"])["item"]
    out = df.copy()
    out["item_was_inferred"] = False
    m = out["item"].isna() & out["price_per_unit"].notna()
    keys = pd.MultiIndex.from_frame(out.loc[m, ["category", "price_per_unit"]])
    vals = lookup.reindex(keys).to_numpy()
    out.loc[m, "item"] = vals
    out.loc[m, "item_was_inferred"] = pd.notna(vals)
    return out, None, int(out["item_was_inferred"].sum())


def drop_unrecoverable_amounts(df):
    """Rows still missing quantity/total/price after arithmetic recovery. Quantity cannot be
    derived from anything else, and imputing it would fabricate transactions."""
    bad = df[AMOUNTS].isna().any(axis=1)
    return df[~bad], df[bad], 0
