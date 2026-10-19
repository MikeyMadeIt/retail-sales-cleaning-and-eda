"""Every cleaning step runs through Ledger.run(), which records what happened.
The report is generated from this log, so documentation cannot drift from code."""
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class Step:
    name: str
    rationale: str
    rows_before: int
    rows_after: int
    cells_changed: int


@dataclass
class Ledger:
    steps: list = field(default_factory=list)
    dropped: list = field(default_factory=list)

    def run(self, df, name, rationale, fn):
        """fn(df) -> (clean_df, dropped_df | None, cells_changed)."""
        out, dropped, changed = fn(df)
        n_drop = 0 if dropped is None else len(dropped)
        if n_drop:
            self.dropped.append(dropped.assign(drop_step=name))
        # Every row that leaves the table must be in the rejected log.
        assert len(df) - len(out) == n_drop, f"{name}: row count does not reconcile"
        self.steps.append(Step(name, rationale, len(df), len(out), int(changed)))
        return out

    def rejected(self):
        return pd.concat(self.dropped) if self.dropped else pd.DataFrame()
