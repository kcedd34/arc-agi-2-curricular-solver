from src.evaluation.color_augmentation_diagnostics import render_comparison_markdown
from src.evaluation.shape_constraint_diagnostics import ShapeConstraintPairRow


def _row(**overrides) -> ShapeConstraintPairRow:
    defaults = dict(
        task_id="fixture",
        rule_holds=True,
        split="evaluation",
        pair_index=0,
        attempts_tried=1,
        num_kept=1,
        unconstrained_shape_match=False,
        unconstrained_exact_match=False,
        constrained_shape_match=True,
        constrained_exact_match=False,
        constrained_best_cell_accuracy=0.5,
    )
    defaults.update(overrides)
    return ShapeConstraintPairRow(**defaults)


def test_render_comparison_markdown_includes_both_config_names():
    rows_by_config = {
        "geometric_only": [_row()],
        "geometric_plus_color": [_row(constrained_best_cell_accuracy=0.7)],
    }
    markdown = render_comparison_markdown(rows_by_config)
    assert "geometric_only" in markdown
    assert "geometric_plus_color" in markdown


def test_render_comparison_markdown_formats_cell_accuracy():
    rows_by_config = {"geometric_only": [_row(constrained_best_cell_accuracy=0.856)]}
    markdown = render_comparison_markdown(rows_by_config)
    assert "0.86" in markdown


def test_render_comparison_markdown_handles_none_cell_accuracy_as_not_available():
    rows_by_config = {"geometric_only": [_row(constrained_best_cell_accuracy=None)]}
    markdown = render_comparison_markdown(rows_by_config)
    assert "n/a" in markdown


def test_render_comparison_markdown_marks_exact_match_yes():
    rows_by_config = {"geometric_only": [_row(constrained_exact_match=True)]}
    markdown = render_comparison_markdown(rows_by_config)
    lines = [line for line in markdown.splitlines() if "fixture" in line]
    assert any("yes" in line for line in lines)
