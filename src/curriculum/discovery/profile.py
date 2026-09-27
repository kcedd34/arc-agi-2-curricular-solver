"""Task profile for the utility registry (ADR 0110): five inventory bits, so
tasks with the same broad shape of change share what discovery learned."""
from src.curriculum.loader import Task
from src.curriculum.perception.change_inventory import build_task_inventory

PROFILE_BITS = (
    "same_shape",
    "few_cells_change",
    "no_new_colors",
    "new_color_always_added",
    "object_count_preserved",
)


def profile_key(task: Task) -> str:
    inventory = build_task_inventory(task)
    return "".join("1" if getattr(inventory, bit) else "0" for bit in PROFILE_BITS)
