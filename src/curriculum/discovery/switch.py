"""The discovery switch (ADR 0110). Off by default so the frozen 0.83 baseline
and every existing measurement are untouched. An environment variable, so
worker processes inherit it; it is part of the per-task cache key."""
import os

ENV_VAR = "CURRICULUM_DISCOVERY"


def generated_enabled() -> bool:
    return os.environ.get(ENV_VAR, "") == "1"


def walk_cache_key() -> str:
    return "derived_walk_gen" if generated_enabled() else "derived_walk"
