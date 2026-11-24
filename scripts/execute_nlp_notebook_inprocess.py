"""Execute notebook code cells in one Python process when kernels are unavailable."""
import contextlib
import io
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "NLP_Final.ipynb"


def main():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    namespace = {"__name__": "__main__"}
    count = 0
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        count += 1
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(cell.source, f"{NOTEBOOK.name}:cell{count}", "exec"), namespace)
        cell.execution_count = count
        cell.outputs = [nbformat.v4.new_output("stream", name="stdout", text=output.getvalue())]
    nbformat.write(notebook, NOTEBOOK)
    print(f"Executed {count} code cells in process; HTTP and kernel launch were not tested")


if __name__ == "__main__":
    main()
