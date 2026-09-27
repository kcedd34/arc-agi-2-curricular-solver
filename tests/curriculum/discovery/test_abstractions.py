from src.curriculum.discovery.abs_composite import Folded, composite_name, fold, from_mined, unfold
from src.curriculum.discovery.abs_mine import mine
from src.curriculum.discovery.abs_rebuild import rebuild
from src.curriculum.discovery.abs_tokens import base_length, chain_of
from src.curriculum.library.derived.model import Action, DerivedComposition, ParamSource, RegionSpec
from src.curriculum.library.panels.panel_composition import PanelComposition
from src.curriculum.search.compose import Composition
from src.curriculum.search.sequence.composition import SequenceComposition


def _main(selector="largest_object", colour=1):
    return Composition("identity_canvas", {}, selector, {}, "recolor", {"color": colour}, "keep", {})


def _derived(name="stamp"):
    region = RegionSpec("objects", 8, True, 0)
    return DerivedComposition(region, (Action(name, ParamSource("literal", 3), None),))


def test_chain_rebuild_is_identity_for_every_family():
    sequence = SequenceComposition(_main(), PanelComposition("swap", "row", 0))
    for candidate in (_main(), _derived(), PanelComposition("summary", "row", 2), sequence):
        assert rebuild(chain_of(candidate)) == candidate


def test_base_length_ignores_sequence_marker():
    sequence = SequenceComposition(_main(), _derived())
    assert base_length(chain_of(sequence)) == 4 + 2


def test_mine_needs_two_distinct_tasks():
    chains = {"a": chain_of(_main(colour=1)), "b": chain_of(_main(colour=5)), "c": chain_of(_derived())}
    mined = mine(chains)
    assert mined and all(len(m.tasks) >= 2 for m in mined)
    assert all("c" not in m.tasks for m in mined)


def test_fold_unfold_returns_identical_chain_with_free_parameters():
    chains = {"a": chain_of(_main(colour=1)), "b": chain_of(_main(colour=5))}
    composites = from_mined(mine(chains))
    for chain in chains.values():
        nodes = fold(chain, composites)
        assert any(isinstance(n, Folded) for n in nodes)
        assert unfold(nodes) == chain
        assert rebuild(unfold(nodes)) == rebuild(chain)


def test_composite_name_is_deterministic():
    parts = (("main", "layout", "identity_canvas"), ("main", "selector", "largest_object"))
    assert composite_name(parts) == composite_name(parts)
