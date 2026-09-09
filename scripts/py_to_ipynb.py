"""A '# %%' script -> its notebook, and back again to prove the two are the same file in two
containers. Generalised from log/2026-09-05/py_to_ipynb.py, which was fixed to the extractor.

    python scripts/py_to_ipynb.py notebooks/threadatlas-ingestor.py

The script is the thing to edit; the notebook is generated from it. Cells are "# %%" markers,
"# %% [markdown]" for a markdown cell whose lines carry a "# " prefix. Kaggle's importer needs
nbformat 4.5 cell ids, so every cell gets one.
"""
import json
import re
import sys
from pathlib import Path

PY = Path(sys.argv[1])
NB = PY.with_suffix(".ipynb")
META = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}}


def split_cells(text):
    parts = re.split(r"^# %%( \[markdown\])?\n", text, flags=re.M)
    assert parts[0].strip() == "", "text before the first cell marker"
    cells = []
    for marker, body in zip(parts[1::2], parts[2::2]):
        body = body.rstrip("\n") + "\n"
        if marker:
            lines = [(l[2:] if l.startswith("# ") else l[1:] if l == "#" else l) for l in body.splitlines()]
            cells.append(("markdown", "\n".join(lines).rstrip("\n") + "\n"))
        else:
            cells.append(("code", body))
    return cells


def join_cells(cells):
    out = []
    for kind, src in cells:
        if kind == "markdown":
            out.append("# %% [markdown]\n" + "\n".join(("# " + l) if l.strip() else "#" for l in src.rstrip("\n").splitlines()) + "\n")
        else:
            out.append("# %%\n" + src.rstrip("\n") + "\n")
    return "\n".join(out)


def to_source(text):
    lines = text.splitlines(keepends=True)
    if lines and lines[-1].endswith("\n"):
        lines[-1] = lines[-1][:-1]
    return lines


text = PY.read_text(encoding="utf-8")
cells = split_cells(text)
meta = json.loads(NB.read_text(encoding="utf-8"))["metadata"] if NB.exists() else META
nb_cells = []
for i, (kind, src) in enumerate(cells):
    cell = {"cell_type": kind, "id": f"block-{i}", "metadata": {}, "source": to_source(src)}
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    nb_cells.append(cell)
NB.write_text(json.dumps({"cells": nb_cells, "metadata": meta, "nbformat": 4, "nbformat_minor": 5},
                         indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

back = json.loads(NB.read_text(encoding="utf-8"))
rebuilt = join_cells([(c["cell_type"], "".join(c["source"])) for c in back["cells"]])
same = rebuilt.rstrip("\n") == text.rstrip("\n")
# the last gate before the notebook leaves this machine: the battery execs the script as one
# namespace and cannot see cell ordering, and that is what shipped a NameError to Kaggle in 0.8
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_cell_order import offences
forward = offences(text)
for cell, name, defined in forward:
    print(f"  cell {cell} reaches {name!r}, which cell {defined} defines")
print(f"{NB}: {len(nb_cells)} cells; round trip {'identical' if same else 'DIFFERS'}"
      f"; {len(forward)} forward reference(s)")
sys.exit(0 if same and not forward else 1)
