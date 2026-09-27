"""Sandboxed subprocess entry point for executing a model-generated
transform(g) program against one grid (ADR 0060).

Run as: python program_sandbox_runner.py < payload.json
payload: {"program_source": str, "grid_input": List[str]}
stdout:  {"result": List[str]} or {"error": str}

Restricted builtins only: no import, no open/exec/eval exposed inside the
candidate's own namespace, no filesystem or network access from within
the executed program. This is a best-effort sandbox for a local,
non-adversarial model, not a hardened security boundary; the hard
timeout and process isolation live in program_sandbox.py, the caller.

Deliberately self-contained (no project imports) so it works as a plain
script regardless of the caller's working directory.
"""
import builtins
import json
import sys

_ALLOWED_BUILTIN_NAMES = (
    "len", "range", "enumerate", "list", "str", "int", "zip", "min", "max",
    "sum", "sorted", "reversed", "set", "dict", "tuple", "bool", "abs",
    "all", "any", "map", "filter", "isinstance", "True", "False", "None",
)


def _safe_globals():
    safe_builtins = {name: getattr(builtins, name) for name in _ALLOWED_BUILTIN_NAMES}
    return {"__builtins__": safe_builtins}


def _run(program_source, grid_input):
    namespace = _safe_globals()
    exec(program_source, namespace)  # noqa: S102 - the sandboxed candidate itself, this is the point
    transform = namespace.get("transform")
    if transform is None:
        return {"error": "program did not define transform(g)"}
    return {"result": transform(grid_input)}


def main():
    payload = json.loads(sys.stdin.read())
    try:
        output = _run(payload["program_source"], payload["grid_input"])
    except Exception as exc:  # noqa: BLE001 - a candidate program error is expected input, not a bug here
        output = {"error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(output))


if __name__ == "__main__":
    main()
