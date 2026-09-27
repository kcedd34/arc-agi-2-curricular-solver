"""Extracts code cell sources from a Jupyter notebook, in execution order."""
import json
from pathlib import Path
from typing import List


def extract_code_cells(notebook_path: Path) -> List[str]:
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)
    return [
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]
