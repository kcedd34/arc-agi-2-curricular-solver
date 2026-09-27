"""Pull the Python source out of a raw model completion."""
import re
from typing import Optional

FENCE_RE = re.compile(r"```[a-zA-Z0-9_]*\n(.*?)(?:```|\Z)", re.DOTALL)


def _fenced_block(text: str) -> Optional[str]:
    match = FENCE_RE.search(text)
    return match.group(1) if match else None


def extract_code(text: str) -> Optional[str]:
    """The first fenced block (or the whole text if unfenced); None when no `def solve`."""
    block = _fenced_block(text)
    code = block if block is not None else text
    if "def solve" not in code:
        return None
    return code.strip("\n") + "\n"


def rule_line(code: Optional[str]) -> str:
    """The guided-reasoning comment ('# Rule...') if the program starts with one."""
    for line in (code or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and "ule" in stripped:
            return stripped
        if stripped and not stripped.startswith("#"):
            return ""
    return ""
