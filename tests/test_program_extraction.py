from src.solvers.neural.program_extraction import build_program_source, extract_program_body


def test_extracts_indented_body_and_stops_at_unindented_line():
    completion = "    return g\n\ndef other_thing():\n    pass\n"
    assert extract_program_body(completion) == "    return g"


def test_stops_at_hallucinated_commentary_after_the_body():
    completion = "    return g\n# this is how the rule works\n"
    assert extract_program_body(completion) == "    return g"


def test_stops_at_a_second_hallucinated_example_block():
    completion = "    return g\nexamples2 = [\n    (\"1\", \"2\"),\n]\n"
    assert extract_program_body(completion) == "    return g"


def test_returns_none_when_no_indented_body_line_exists():
    completion = "not indented at all\n"
    assert extract_program_body(completion) is None


def test_returns_none_on_empty_completion():
    assert extract_program_body("") is None


def test_keeps_blank_lines_inside_the_body_but_trims_trailing_blank_lines():
    completion = "    x = 1\n\n    return x\n\n\ndef unrelated():\n    pass\n"
    assert extract_program_body(completion) == "    x = 1\n\n    return x"


def test_respects_the_max_lines_cap():
    completion = "".join(f"    line_{i} = {i}\n" for i in range(10)) + "    return line_0\n"
    body = extract_program_body(completion, max_lines=3)
    assert body.splitlines() == ["    line_0 = 0", "    line_1 = 1", "    line_2 = 2"]


def test_build_program_source_wraps_the_body_in_a_def_transform_header():
    source = build_program_source("    return g")
    assert source == "def transform(g):\n    return g\n"
