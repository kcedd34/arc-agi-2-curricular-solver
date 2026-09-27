"""Lowering of the shift action (ADR 0107): every region is erased first,
then repainted at its shifted place, so a region never erases another one's
new position."""
from typing import List, Tuple

from src.curriculum.library.derived import expressions as ex
from src.curriculum.library.derived.model import Action
from src.curriculum.spec import vocabulary as vocab

MOVED = "moved"


def shift_exprs(action: Action) -> Tuple[vocab.Expr, vocab.Expr]:
    measures, table = action.param.value
    keys = tuple(ex.element_measure(m, ex.ELEMENT) for m in measures)
    dr_table = tuple((key, shift[0]) for key, shift in table)
    dc_table = tuple((key, shift[1]) for key, shift in table)
    return vocab.TableLookup(keys, dr_table), vocab.TableLookup(keys, dc_table)


def _erase_body(background: int) -> List[vocab.Step]:
    elem = vocab.RegionRef(ex.ELEMENT)
    erased = f"{ex.ELEMENT}_erased"
    return [
        vocab.Transform(region=elem, op=vocab.Erase(background=background), result_name=erased),
        vocab.Emit(region=elem, source=vocab.Copy(source=vocab.Ref(erased))),
    ]


def _paint_body(action: Action) -> List[vocab.Step]:
    dr, dc = shift_exprs(action)
    elem = vocab.RegionRef(ex.ELEMENT)
    return [
        vocab.Transform(region=elem, op=vocab.Translate(dr, dc), result_name=MOVED),
        vocab.Emit(region=vocab.RegionRef(MOVED), source=vocab.Copy(source=vocab.Ref(MOVED))),
    ]


def translate_steps(action: Action, tag: str, background: int) -> List[vocab.Step]:
    regions = vocab.Ref(ex.REGIONS_REF)
    return [
        vocab.ForEach(regions, _erase_body(background), element_name=ex.ELEMENT),
        vocab.ForEach(regions, _paint_body(action), element_name=ex.ELEMENT),
    ]
