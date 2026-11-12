#!/usr/bin/env python3
"""Minimal stdlib notebook checker/executor (no Jupyter required).

  python3 tools/run_notebook.py notebooks/X.ipynb [--out build/X.executed.ipynb]

1. Validates the nbformat-4 structure used here (top-level keys, cell types,
   ids, source lists, clean outputs/execution counts in the committed file).
2. Executes code cells in order in one namespace with the notebook's directory
   as the working directory and records real stdout/stderr/errors as nbformat
   stream/error outputs in a separate executed copy.

This is not a Jupyter kernel: rich display objects are not rendered and
IPython magics are unsupported. With Jupyter installed you can run the same
notebook normally (e.g. ``jupyter nbconvert --to notebook --execute``).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import traceback
from pathlib import Path


def validate(nb: dict, require_clean: bool = True) -> list[str]:
    errs = []
    for key in ("cells", "metadata", "nbformat", "nbformat_minor"):
        if key not in nb:
            errs.append(f"missing top-level key {key}")
    if nb.get("nbformat") != 4:
        errs.append("nbformat must be 4")
    ids = set()
    for i, c in enumerate(nb.get("cells", [])):
        ct = c.get("cell_type")
        if ct not in ("code", "markdown", "raw"):
            errs.append(f"cell {i}: bad cell_type {ct}")
        if not isinstance(c.get("source"), (list, str)):
            errs.append(f"cell {i}: source must be list or str")
        cid = c.get("id")
        if nb.get("nbformat_minor", 0) >= 5:
            if not cid or cid in ids:
                errs.append(f"cell {i}: missing/duplicate id")
            ids.add(cid)
        if ct == "code":
            for k in ("outputs", "execution_count", "metadata"):
                if k not in c:
                    errs.append(f"cell {i}: missing {k}")
            if require_clean and (c.get("outputs") or c.get("execution_count") is not None):
                errs.append(f"cell {i}: committed notebook should be clean (no outputs)")
    return errs


def execute(nb: dict, workdir: Path) -> tuple[dict, bool]:
    ns: dict = {"__name__": "__main__"}
    ok = True
    count = 0
    old = os.getcwd()
    os.chdir(workdir)
    sys.path.insert(0, str(workdir))
    try:
        for c in nb["cells"]:
            if c["cell_type"] != "code":
                continue
            count += 1
            src = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            out, err = io.StringIO(), io.StringIO()
            outputs = []
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    exec(compile(src, f"<cell {count}>", "exec"), ns)
            except Exception as e:  # record as nbformat error output
                ok = False
                outputs.append({"output_type": "error", "ename": type(e).__name__, "evalue": str(e),
                                "traceback": traceback.format_exc().splitlines()})
            if out.getvalue():
                outputs.insert(0, {"output_type": "stream", "name": "stdout", "text": out.getvalue().splitlines(True)})
            if err.getvalue():
                outputs.insert(1 if out.getvalue() else 0,
                               {"output_type": "stream", "name": "stderr", "text": err.getvalue().splitlines(True)})
            c["outputs"] = outputs
            c["execution_count"] = count
            if not ok:
                break
    finally:
        os.chdir(old)
    return nb, ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    nb = json.loads(args.notebook.read_text())
    errs = validate(nb)
    if errs:
        print("INVALID:", *errs, sep="\n  ")
        return 2
    print(f"structure OK: {args.notebook} ({len(nb['cells'])} cells)")
    executed, ok = execute(nb, args.notebook.resolve().parent)
    out = args.out or args.notebook.with_suffix(".executed.ipynb")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(executed, indent=1) + "\n")
    print(("executed OK" if ok else "EXECUTION FAILED") + f" -> {out}")
    for c in executed["cells"]:
        for o in c.get("outputs", []):
            if o["output_type"] == "error":
                print("\n".join(o["traceback"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
