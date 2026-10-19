"""Column-level data quality profile, applied identically before and after cleaning."""
import pandas as pd


def profile(df: pd.DataFrame, key: str) -> dict:
    cols = {}
    for c in df.columns:
        s = df[c]
        blank = s.isna() | (s.astype(str).str.strip() == "")
        cols[c] = {
            "dtype": str(s.dtype),
            "missing": int(blank.sum()),
            "missing_pct": round(100 * blank.mean(), 2),
            "distinct": int(s[~blank].nunique()),
        }
    return {
        "rows": len(df),
        "columns": df.shape[1],
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_keys": int(df[key].duplicated().sum()),
        "cols": cols,
    }
