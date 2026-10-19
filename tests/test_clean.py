import unittest
import pandas as pd
from src import clean as C
from src.ledger import Ledger


def frame(**kw):
    base = dict(transaction_id=["TXN_1111111"], customer_id=["CUST_01"], category=["Food"],
                item=["Item_1_FOOD"], price_per_unit=[10.0], quantity=[3], total_spent=[30.0])
    base.update(kw)
    return pd.DataFrame(base).astype({"quantity": "Int64"})


class T(unittest.TestCase):
    def test_recover_each_field(self):
        for col, val in [("total_spent", None), ("price_per_unit", None), ("quantity", None)]:
            df = frame(**{col: [val]}).astype({"quantity": "Int64"})
            out, _, n = C.recover_by_arithmetic(df)
            self.assertEqual(n, 1)
            self.assertEqual((out.price_per_unit[0], int(out.quantity[0]), out.total_spent[0]), (10.0, 3, 30.0))
            self.assertTrue(out[f"{col}_was_imputed"][0])

    def test_two_missing_not_recovered(self):
        out, _, n = C.recover_by_arithmetic(frame(quantity=[None], total_spent=[None]))
        self.assertEqual(n, 0)

    def test_ledger_reconciles(self):
        df = pd.concat([frame(), frame()], ignore_index=True)
        L = Ledger()
        out = L.run(df, "dups", "x", lambda d: (d.iloc[:1], d.iloc[1:], 0))
        self.assertEqual(len(out) + len(L.rejected()), 2)

    def test_ledger_rejects_unaccounted_drop(self):
        with self.assertRaises(AssertionError):
            Ledger().run(pd.concat([frame(), frame()]), "bad", "x", lambda d: (d.iloc[:1], None, 0))


if __name__ == "__main__":
    unittest.main()
