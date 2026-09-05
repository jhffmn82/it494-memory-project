"""notebooks/factledger-extractor.py -> notebooks/factledger-extractor.ipynb, and back again to
prove the two are the same file in two containers. Run from the repository root.

The script is the thing to edit; the notebook is generated from it. Cells are "# %%" markers,
"# %% [markdown]" for a markdown cell whose lines carry a "# " prefix.
"""
import json
import re
from pathlib import Path

PY = Path("notebooks/factledger-extractor.py")
NB = Path("notebooks/factledger-extractor.ipynb")

old = json.loads(NB.read_text(encoding="utf-8"))
meta, nbformat, minor = old["metadata"], old["nbformat"], old["nbformat_minor"]


def split_cells(text):
    """[(kind, source)] from a '# %%' script; markdown cells lose their '# ' prefix."""
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
    return "\n\n".join(out)


def to_source(text):
    """nbformat's list of lines: every line keeps its newline except the last."""
    lines = text.splitlines(keepends=True)
    if lines and lines[-1].endswith("\n"):
        lines[-1] = lines[-1][:-1]
    return lines


cells = split_cells(PY.read_text(encoding="utf-8"))
nb_cells = []
for i, (kind, src) in enumerate(cells):
    cell = {"cell_type": kind, "id": f"block-{i}", "metadata": {}, "source": to_source(src)}
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    nb_cells.append(cell)
NB.write_text(json.dumps({"cells": nb_cells, "metadata": meta, "nbformat": nbformat, "nbformat_minor": minor},
                         indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

back = json.loads(NB.read_text(encoding="utf-8"))
same = join_cells([(c["cell_type"], "".join(c["source"])) for c in back["cells"]]) == PY.read_text(encoding="utf-8")
print(f"cells: {len(nb_cells)} ({sum(k == 'markdown' for k, _ in cells)} markdown, {sum(k == 'code' for k, _ in cells)} code)"
      f"  kernel: {meta.get('kernelspec', {}).get('name')}  nbformat {nbformat}.{minor}")
print("round trip ipynb -> py identical to the script:", same)
if not same:
    raise SystemExit("round trip differs")
