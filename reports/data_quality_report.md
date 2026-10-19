# Data Quality Report: Retail Store Sales

## 1. Provenance

- Source: Kaggle, *Retail Store Sales: Dirty for Data Cleaning* (`retail_store_sales.csv`)
- Raw file SHA-256: `79181a5ac74a35dbf65063c3850c05183fdb7a15734859b2d8ac272c8b204a93` (verified on every run)
- Raw rows: 12,575; clean rows: 11,971
- Raw file is never modified; all changes are made by `src/pipeline.py`.

## 2. Before / after summary

| Metric | Before | After |
|---|---:|---:|
| Rows | 12,575 | 11,971 |
| Columns | 11 | 15 (adds provenance flags) |
| Exact duplicate rows | 0 | 0 |
| Duplicate transaction IDs | 0 | 0 |

| Column | Missing before | Missing after | Distinct before | Distinct after |
|---|---:|---:|---:|---:|
| transaction_id | 0 (0.0%) | 0 (0.0%) | 12575 | 11971 |
| customer_id | 0 (0.0%) | 0 (0.0%) | 25 | 25 |
| category | 0 (0.0%) | 0 (0.0%) | 8 | 8 |
| item | 1213 (9.65%) | 0 (0.0%) | 200 | 200 |
| price_per_unit | 609 (4.84%) | 0 (0.0%) | 25 | 25 |
| quantity | 604 (4.8%) | 0 (0.0%) | 10 | 10 |
| total_spent | 604 (4.8%) | 0 (0.0%) | 227 | 227 |
| payment_method | 0 (0.0%) | 0 (0.0%) | 3 | 3 |
| location | 0 (0.0%) | 0 (0.0%) | 2 | 2 |
| transaction_date | 0 (0.0%) | 0 (0.0%) | 1114 | 1114 |
| discount_applied | 4199 (33.39%) | 3988 (33.31%) | 2 | 2 |

`discount_applied` is deliberately left null where unknown (see decision 8). 'Distinct' counts exclude nulls; the raw profile treats blank strings as missing.

## 3. Cleaning log (generated from the ledger)

| # | Step | Rows in | Rows out | Dropped | Cells changed |
|---|---|---:|---:|---:|---:|
| 1 | Standardise blanks | 12,575 | 12,575 | 0 | 7,229 |
| 2 | Parse types | 12,575 | 12,575 | 0 | 0 |
| 3 | Reject impossible values | 12,575 | 12,575 | 0 | 0 |
| 4 | Remove duplicates | 12,575 | 12,575 | 0 | 0 |
| 5 | Recover price/quantity/total by arithmetic | 12,575 | 12,575 | 0 | 609 |
| 6 | Infer missing item | 12,575 | 12,575 | 0 | 1,213 |
| 7 | Drop rows with unrecoverable amounts | 12,575 | 11,971 | 604 | 0 |
| 8 | Leave discount_applied null where unknown | 11,971 | 11,971 | 0 | 0 |

### Decisions and justifications

**1. Standardise blanks.** Trim whitespace and convert empty strings to real nulls so that 'missing' means one thing everywhere. Raw file stores missing values as empty strings.

**2. Parse types.** Dates parsed with one explicit format; numbers via `to_numeric`; discount mapped from 'True'/'False'. Anything non-null that fails to parse would be rejected rather than silently nulled.

**3. Reject impossible values.** Non-positive price/quantity/total, malformed IDs or missing dates cannot be valid retail transactions. None found in this file, but the rule is enforced on every run.

**4. Remove duplicates.** Exact duplicate rows and repeated transaction IDs (first kept). Transaction ID is the primary key. None found, and no rows are identical apart from their ID.

**5. Recover price/quantity/total by arithmetic.** Where exactly one of the three is missing, it is computed from the other two using `total = price * quantity` (verified exact on every complete row). Flags `*_was_imputed` mark these cells. Nothing is estimated.

**6. Infer missing item.** `(category, price_per_unit)` determines `item` uniquely, so missing items are looked up from complete rows, after price recovery. Flag `item_was_inferred` marks them.

**7. Drop rows with unrecoverable amounts.** Rows missing both quantity and total cannot be completed: price alone does not determine either. Imputing a median quantity would fabricate transaction values, so these rows are dropped and kept in `output/rejected_rows.csv`.

**8. Leave discount_applied null where unknown.** About a third of values are missing and nothing in the row determines them (total is price*quantity regardless of discount). Imputing True/False would invent a signal, so the column is kept as a nullable boolean and the limitation is reported.

## 4. Rows dropped

| Reason (step) | Rows |
|---|---:|
| Drop rows with unrecoverable amounts | 604 |
| **Total** | **604** (4.8% of raw) |

Every dropped row, with its reason, is in `output/rejected_rows.csv`. Row counts reconcile: raw rows - dropped = clean rows (12,575 - 604 = 11,971).

### Is the dropped set biased?

Share of rows by category, kept vs dropped (a large gap would mean dropping skews analysis):

| category                           | kept   | dropped   |
|:-----------------------------------|:-------|:----------|
| Furniture                          | 12.7%  | 10.9%     |
| Electric household essentials      | 12.7%  | 12.4%     |
| Milk Products                      | 12.6%  | 11.8%     |
| Food                               | 12.6%  | 13.4%     |
| Beverages                          | 12.5%  | 11.8%     |
| Butchers                           | 12.5%  | 11.9%     |
| Computers and electric accessories | 12.3%  | 13.4%     |
| Patisserie                         | 12.0%  | 14.4%     |

## 5. Pre-condition checks (asserted on every run)

- `price_per_unit * quantity == total_spent` on all 11,362 complete rows (0 mismatches).
- (`category`, `price_per_unit`) maps to exactly one `item` on all complete rows (asserted in `infer_item`).
- Every `transaction_date` parses with the single format `%Y-%m-%d` (parse failures are rejected, not coerced).

## 6. Known limitations

- **Discount is unreliable.** `discount_applied` is missing for about a third of raw rows and cannot be recovered. Also, `total_spent == price_per_unit * quantity` exactly, even when discount is `True`, so `total_spent` appears to be pre-discount or the discount is not recorded in it. Do not use it to estimate discounted revenue.
- **Recovered values are exact but still derived.** They are flagged (`*_was_imputed`, `item_was_inferred`) so analyses can exclude them.
- **Dropping rows with unrecoverable amounts is a judgment call.** See the bias table above; if quantities are needed for these transactions, they are not in the source.
- Dates span 2022-01-01 to 2025-01-18; no outlier or future-date check beyond format validity was needed. The dataset looks synthetic (uniform category sizes, 25 prices per category), so findings describe the file, not a real retailer.
