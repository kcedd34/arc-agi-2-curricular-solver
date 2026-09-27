"""Runs inside the isolated subprocess: executes generated code on grids, standard library only.

Self-contained on purpose (run as `python -I sandbox_child.py`, no project imports). Reads a JSON
request on stdin, writes one JSON line on the real stdout. Not a security boundary against an
adversary: it limits an honest but buggy local model (memory, CPU, files, imports, builtins).
"""
import builtins
import json
import os
import resource
import signal
import sys

ALLOWED_IMPORTS = {"collections", "itertools", "math", "copy", "typing"}
SAFE_NAMES = (
    "abs all any bool dict divmod enumerate filter float frozenset int isinstance issubclass iter "
    "len list map max min next object pow range reversed round set slice sorted str sum tuple zip "
    "hash repr bytes bin hex chr ord property staticmethod classmethod super callable "
    "Exception ValueError TypeError IndexError KeyError ZeroDivisionError StopIteration "
    "AttributeError RuntimeError AssertionError NotImplementedError ArithmeticError LookupError "
    "True False None"
).split()
MEMORY_BYTES = 1 << 30


class CallTimeout(BaseException):
    pass


def _on_alarm(signum, frame):
    raise CallTimeout()


def _limits(cpu_seconds: int) -> None:
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level != 0 or name.split(".")[0] not in ALLOWED_IMPORTS:
        raise ImportError(f"import of {name!r} is not allowed")
    return builtins.__import__(name, globals, locals, fromlist, level)


def _safe_builtins() -> dict:
    table = {name: getattr(builtins, name) for name in SAFE_NAMES if hasattr(builtins, name)}
    table["__import__"] = _restricted_import
    table["__build_class__"] = builtins.__build_class__
    table["__name__"] = "candidate"
    return table


def _valid_grid(value):
    if not isinstance(value, (list, tuple)) or not 0 < len(value) <= 30:
        return None
    rows = [list(row) if isinstance(row, (list, tuple)) else None for row in value]
    if any(r is None or len(r) != len(rows[0]) or not 0 < len(r) <= 30 for r in rows):
        return None
    ok = all(type(v) is int and 0 <= v <= 9 for r in rows for v in r)
    return rows if ok else None


def _call_once(solve, grid, seconds: float) -> dict:
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        out = solve(grid)
    except CallTimeout:
        return {"ok": False, "error": "timeout"}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:120]}"}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    rows = _valid_grid(out)
    return {"ok": True, "grid": rows} if rows is not None else {"ok": False, "error": "malformed output"}


def _compile(code: str):
    namespace = {"__builtins__": _safe_builtins()}
    exec(compile(code, "<candidate>", "exec"), namespace)
    solve = namespace.get("solve")
    if not callable(solve):
        raise NameError("solve is not defined")
    return solve


def _run(request: dict) -> list:
    try:
        solve = _compile(request["code"])
    except BaseException as exc:
        failure = {"ok": False, "error": f"load {type(exc).__name__}: {str(exc)[:120]}"}
        return [failure for _ in request["grids"]]
    return [_call_once(solve, json.loads(json.dumps(g)), request["seconds"]) for g in request["grids"]]


def main() -> None:
    request = json.loads(sys.stdin.read())
    out_fd = os.dup(1)
    os.dup2(2, 1)
    _limits(int(request["seconds"] * len(request["grids"])) + 5)
    signal.signal(signal.SIGALRM, _on_alarm)
    results = _run(request)
    os.write(out_fd, (json.dumps(results) + "\n").encode())


if __name__ == "__main__":
    main()
