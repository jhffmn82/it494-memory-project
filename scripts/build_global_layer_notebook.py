"""Assemble the global-layer Kaggle notebook from the threadatlas modules.

    python scripts/build_global_layer_notebook.py

Writes notebooks/threadatlas-global-layer.py (the '# %%' script) and, through
scripts/py_to_ipynb.py, notebooks/threadatlas-global-layer.ipynb. The modules are the source;
the notebook is generated: each module becomes one cell with its package imports and its
command-line tail removed, and a run cell at the end builds the store, the sidecar and the
parents from the Step 1 and Step 0 datasets attached to the kernel. Nothing is edited by hand
in the notebook.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODULES = ["model", "embed", "store", "attach"]
OUT = REPO / "notebooks" / "threadatlas-global-layer.py"

HEAD = '''# %% [markdown]
# # ThreadAtlas global layer
#
# The store, the embedding sidecar and the parents over a Step 1 dataset (`docs/global-layer.md`).
# Attach `it494-threadatlas-step1` and `it494-threadatlas-step0`, add an `OPENAI_API_KEY`
# secret, turn Internet on (fastembed fetches its model once), and run all. Outputs in
# `/kaggle/working`: `threadatlas.sqlite`, `threadatlas.npy`, `attach-calls.jsonl`.
#
# Generated from `threadatlas/*.py` by `scripts/build_global_layer_notebook.py`; edit the
# modules, not this file.

# %%
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "fastembed"], check=True)
import os
if not os.environ.get("OPENAI_API_KEY"):
    try:
        from kaggle_secrets import UserSecretsClient
        os.environ["OPENAI_API_KEY"] = UserSecretsClient().get_secret("OPENAI_API_KEY")
    except Exception:
        print("no OPENAI_API_KEY secret attached: the store and the sidecar will build, the attach step will not")
'''

RUN = '''# %%
# Run: the store, the sidecar, the parents, the sidecar again with the parents' summaries.
from pathlib import Path
STEP1 = Path("/kaggle/input/it494-threadatlas-step1")
STEP0 = Path("/kaggle/input/it494-threadatlas-step0/documents.jsonl")
STORE = Path("/kaggle/working/threadatlas.sqlite")
SIGNALS = {"lexical", "vector", "cast", "identity"}     # the arm; drop names to run an ablation arm

build(STEP1, STEP0, STORE)
build_sidecar(STORE)
if os.environ.get("OPENAI_API_KEY"):
    KEY = os.environ["OPENAI_API_KEY"]
    run(STORE, SIGNALS)
    build_sidecar(STORE)
'''


def cell(name):
    src = (REPO / "threadatlas" / f"{name}.py").read_text(encoding="utf-8")
    src = re.sub(r"^from threadatlas[^\n]*\n", "", src, flags=re.M)
    src = re.sub(r'\nif __name__ == "__main__":.*\Z', "\n", src, flags=re.S)
    if name == "attach":
        src = "import sys\nllm = sys.modules[__name__]\n" + src
    if name == "embed":
        src = src.replace("\ndef build(store):", "\ndef build_sidecar(store):")
    return f"# %% [markdown]\n# ## threadatlas/{name}.py\n\n# %%\n{src.rstrip()}\n"


def main():
    text = HEAD + "\n" + "\n".join(cell(m) for m in MODULES) + "\n" + RUN
    OUT.write_text(text, encoding="utf-8", newline="\n")
    subprocess.run([sys.executable, str(REPO / "scripts" / "py_to_ipynb.py"), str(OUT)], check=True)
    print(f"wrote {OUT.name} and {OUT.with_suffix('.ipynb').name}")


if __name__ == "__main__":
    main()
