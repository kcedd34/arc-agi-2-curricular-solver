"""Tests for the PrimitiveRegistry mechanics (independent of any real primitive)."""
import pytest

from src.curriculum.library.registry import Primitive, PrimitiveRegistry
from src.curriculum.spec import vocabulary as vocab


def _dummy_builder(color: int):
    return [vocab.Compose(default_color=color)]


def test_register_and_build():
    registry = PrimitiveRegistry()
    registry.register(
        Primitive(
            name="dummy",
            params=("color",),
            builder=_dummy_builder,
            description="test-only dummy primitive",
        )
    )
    assert registry.names() == ["dummy"]
    steps = registry.build("dummy", color=5)
    assert steps == [vocab.Compose(default_color=5)]


def test_register_duplicate_name_raises():
    registry = PrimitiveRegistry()
    primitive = Primitive(
        name="dummy", params=(), builder=lambda: [], description="d"
    )
    registry.register(primitive)
    with pytest.raises(ValueError):
        registry.register(primitive)


def test_get_unknown_name_raises():
    registry = PrimitiveRegistry()
    with pytest.raises(KeyError):
        registry.get("does_not_exist")


def test_build_missing_param_raises():
    registry = PrimitiveRegistry()
    registry.register(
        Primitive(
            name="dummy",
            params=("color",),
            builder=_dummy_builder,
            description="test-only dummy primitive",
        )
    )
    with pytest.raises(ValueError):
        registry.build("dummy")
