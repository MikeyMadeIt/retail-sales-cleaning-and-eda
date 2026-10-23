"""Executes the percent-format analysis script cell by cell and writes a Jupyter notebook with outputs embedded
(Jupyter itself is not required to build it). Run from the repo root:  python notebooks/build_notebook.py"""
import base64, contextlib, io, json, os, re
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
src = (HERE / "01_january_effect.py").read_text()
os.chdir(HERE)
cells, ns = [], {"__name__": "__main__"}
parts = re.split(r"^# %%", src, flags=re.M)[1:]
for n, part in enumerate(parts):
    is_md = part.startswith(" [markdown]")
    body = part[len(" [markdown]"):] if is_md else part
    body = body.strip("\n")
    if is_md:
        text = "\n".join(l[2:] if l.startswith("# ") else l.lstrip("#") for l in body.splitlines())
        cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})
        continue
    buf, outputs = io.StringIO(), []
    with contextlib.redirect_stdout(buf):
        exec(compile(body, f"cell{n}", "exec"), ns)
    if buf.getvalue():
        outputs.append({"output_type": "stream", "name": "stdout", "text": buf.getvalue().splitlines(True)})
    for num in plt.get_fignums():
        b = io.BytesIO(); plt.figure(num).savefig(b, format="png", dpi=110, bbox_inches="tight")
        outputs.append({"output_type": "display_data", "metadata": {}, "data": {"image/png": base64.b64encode(b.getvalue()).decode(), "text/plain": ["<Figure>"]}})
    plt.close("all")
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": n, "source": body.splitlines(True), "outputs": outputs})
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
(HERE / "01_january_effect.ipynb").write_text(json.dumps(nb, indent=1))
print("wrote notebook:", len(cells), "cells")
