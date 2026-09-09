"""Does every cell only use names the cells before it have defined?

The offline battery execs the whole script into one namespace, so definition order is invisible
to it: a function defined in block 3 may call one defined in block 4 and nothing complains. In
the notebook the cells run in order, and a cell that CALLS such a function dies with NameError
before any document is read. That is how 0.8 shipped with generate() keying its reply cache on
h(), which lived two cells later, and the connection test failed on the first run.

The rule this enforces is the one that actually matters: a cell's top-level statements may only
reach names defined in that cell or an earlier one, following calls transitively. A function that
merely mentions a later name is fine, as long as nothing calls it before that name exists.

    python scripts/check_cell_order.py notebooks/threadatlas-ingestor.py
"""
import ast
import builtins
import sys
from pathlib import Path

BUILTIN = set(dir(builtins))


def cells_of(source):
    """The source split on the cell markers py_to_ipynb writes, in order."""
    out, current = [], []
    for line in source.splitlines():
        if line.startswith("# %%"):
            out.append("\n".join(current))
            current = []
        else:
            current.append(line)
    out.append("\n".join(current))
    return out


def bound_names(node):
    """Every module-level name a cell binds: defs, classes, assignments, imports."""
    names = set()
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(item.name)
        elif isinstance(item, (ast.Import, ast.ImportFrom)):
            for alias in item.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(item, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = item.targets if isinstance(item, ast.Assign) else [item.target]
            for target in targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
        elif isinstance(item, (ast.For, ast.While, ast.If, ast.Try, ast.With)):
            for sub in ast.walk(item):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    names.add(sub.id)
                elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(sub.name)
    return names


def free_names(node):
    """The names a function body reads that it does not bind itself. An over-approximation of its
    globals: a shadowed local is counted, which can only make this stricter, never laxer."""
    local, used = set(), set()
    for arg in getattr(node, "args", ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], defaults=[], kw_defaults=[])).args:
        local.add(arg.arg)
    for sub in ast.walk(node):
        if isinstance(sub, ast.arg):
            local.add(sub.arg)
        elif isinstance(sub, ast.Name):
            (local if isinstance(sub.ctx, ast.Store) else used).add(sub.id)
        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and sub is not node:
            local.add(sub.name)
    return {n for n in used - local - BUILTIN}


def offences(source):
    """Every (cell, name) a cell's top level can reach before that name is defined."""
    cells = [ast.parse(c) for c in cells_of(source)]
    first_cell, reads = {}, {}
    for index, tree in enumerate(cells):
        for name in bound_names(tree):
            first_cell.setdefault(name, index)
        for item in ast.walk(tree):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                reads[item.name] = free_names(item)

    def reachable(names, seen=None):
        """Those names, plus everything the functions among them read, transitively."""
        seen = seen if seen is not None else set()
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            if name in reads:
                reachable(reads[name], seen)
        return seen

    bad = []
    for index, tree in enumerate(cells):
        top = set()
        for item in tree.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue                       # defining a function reads nothing yet
            for sub in ast.walk(item):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                    top.add(sub.id)
        for name in sorted(reachable(top)):
            if name in first_cell and first_cell[name] > index:
                bad.append((index, name, first_cell[name]))
    return bad


def main(path):
    bad = offences(Path(path).read_text(encoding="utf-8"))
    for cell, name, defined in bad:
        print(f"cell {cell} reaches {name!r}, which cell {defined} defines")
    print(f"{path}: {len(bad)} forward reference(s) a cell can reach at run time")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "notebooks/threadatlas-ingestor.py"))
