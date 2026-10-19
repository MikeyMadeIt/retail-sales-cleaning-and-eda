"""Renders reports/data_quality_report.md from the ledger and the two profiles."""
import pandas as pd


def _profile_table(before, after):
    rows = ["| Column | Missing before | Missing after | Distinct before | Distinct after |",
            "|---|---:|---:|---:|---:|"]
    for c, b in before["cols"].items():
        a = after["cols"][c]
        rows.append(f"| {c} | {b['missing']} ({b['missing_pct']}%) | {a['missing']} ({a['missing_pct']}%) "
                    f"| {b['distinct']} | {a['distinct']} |")
    return "\n".join(rows)


def render(meta, before, after, ledger, rejected, bias_table, checks):
    L = []
    L += ["# Data Quality Report: Retail Store Sales", ""]
    L += ["## 1. Provenance", "",
          f"- Source: Kaggle, *Retail Store Sales: Dirty for Data Cleaning* (`retail_store_sales.csv`)",
          f"- Raw file SHA-256: `{meta['sha']}` (verified on every run)",
          f"- Raw rows: {before['rows']:,}; clean rows: {after['rows']:,}",
          "- Raw file is never modified; all changes are made by `src/pipeline.py`.", ""]

    L += ["## 2. Before / after summary", "",
          "| Metric | Before | After |", "|---|---:|---:|",
          f"| Rows | {before['rows']:,} | {after['rows']:,} |",
          f"| Columns | {before['columns']} | {after['columns']} (adds provenance flags) |",
          f"| Exact duplicate rows | {before['duplicate_rows']} | {after['duplicate_rows']} |",
          f"| Duplicate transaction IDs | {before['duplicate_keys']} | {after['duplicate_keys']} |", "",
          _profile_table(before, after), "",
          "`discount_applied` is deliberately left null where unknown (see decision 8)."
          " 'Distinct' counts exclude nulls; the raw profile treats blank strings as missing.", ""]

    L += ["## 3. Cleaning log (generated from the ledger)", "",
          "| # | Step | Rows in | Rows out | Dropped | Cells changed |", "|---|---|---:|---:|---:|---:|"]
    for i, s in enumerate(ledger.steps, 1):
        L.append(f"| {i} | {s.name} | {s.rows_before:,} | {s.rows_after:,} | "
                 f"{s.rows_before - s.rows_after:,} | {s.cells_changed:,} |")
    L += ["", "### Decisions and justifications", ""]
    for i, s in enumerate(ledger.steps, 1):
        L += [f"**{i}. {s.name}.** {s.rationale}", ""]

    L += ["## 4. Rows dropped", ""]
    if len(rejected):
        t = rejected.groupby("drop_step").size().rename("rows").reset_index()
        L += ["| Reason (step) | Rows |", "|---|---:|"]
        L += [f"| {r.drop_step} | {r.rows:,} |" for r in t.itertuples()]
        L += [f"| **Total** | **{len(rejected):,}** ({100*len(rejected)/before['rows']:.1f}% of raw) |", "",
              "Every dropped row, with its reason, is in `output/rejected_rows.csv`. "
              "Row counts reconcile: raw rows - dropped = clean rows "
              f"({before['rows']:,} - {len(rejected):,} = {after['rows']:,}).", ""]
    else:
        L += ["No rows were dropped.", ""]

    if bias_table is not None:
        L += ["### Is the dropped set biased?", "",
              "Share of rows by category, kept vs dropped (a large gap would mean dropping skews analysis):", "",
              bias_table.to_markdown(), ""]

    L += ["## 5. Pre-condition checks (asserted on every run)", ""]
    L += [f"- {c}" for c in checks]
    L += ["", "## 6. Known limitations", "",
          "- **Discount is unreliable.** `discount_applied` is missing for about a third of raw rows and "
          "cannot be recovered. Also, `total_spent == price_per_unit * quantity` exactly, even when "
          "discount is `True`, so `total_spent` appears to be pre-discount or the discount is not recorded in it. "
          "Do not use it to estimate discounted revenue.",
          "- **Recovered values are exact but still derived.** They are flagged (`*_was_imputed`, `item_was_inferred`) "
          "so analyses can exclude them.",
          "- **Dropping rows with unrecoverable amounts is a judgment call.** See the bias table above; if quantities are needed for "
          "these transactions, they are not in the source.",
          "- Dates span 2022-01-01 to 2025-01-18; no outlier or future-date check beyond format validity was "
          "needed. The dataset looks synthetic (uniform category sizes, 25 prices per category), so findings "
          "describe the file, not a real retailer.", ""]
    return "\n".join(L)
