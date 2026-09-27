import ast
import base64
import hashlib
import importlib.util
import io
import json
import zipfile
from pathlib import Path

BUILDER = Path("notebooks/curricular/build_notebook.py")


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_notebook", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_zip_contains_solver_and_submission_layer_but_no_tests():
    names = zipfile.ZipFile(io.BytesIO(_load_builder()._zip_source())).namelist()
    assert "src/__init__.py" in names
    assert "src/curriculum/submission/build.py" in names
    assert not any(n.startswith("tests/") for n in names)


def test_notebook_cells_parse_and_embedded_hash_matches(tmp_path):
    module = _load_builder()
    module.OUT = tmp_path / "nb.ipynb"
    nb = json.loads(module.build().read_text(encoding="utf-8"))
    code_cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    for source in code_cells:
        ast.parse(source)
    ns = {}
    for line in code_cells[0].splitlines():
        if line.startswith(("CODE_SHA256", "CODE_B64")):
            exec(line, ns)
    assert hashlib.sha256(base64.b64decode(ns["CODE_B64"])).hexdigest() == ns["CODE_SHA256"]
    assert "submission.json" in "".join(code_cells) or "submission.json" in nb["cells"][0]["source"][-1]
