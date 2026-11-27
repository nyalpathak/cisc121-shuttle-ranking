"""Run from the project folder with python -m unittest discover -s tests -v."""

import unittest
from itertools import product

from app import editing, next_step, previous_step, show_result, start
from display import render_step
from ranking import EXAMPLE, MAX_STOPS, build_steps, merge_sort, parse_stops


def test_sample_tie():
    final = build_steps(EXAMPLE)[-1]
    assert final["output"] == [
        {"name": "West Campus", "count": 32},
        {"name": "Athletics Centre", "count": 32},
        {"name": "Stauffer Library", "count": 18},
        {"name": "Union Street", "count": 7},
    ]
    assert "Send the extra shuttle to West Campus" in final["note"]
    assert "tied for first" in final["note"]


def test_stauffer_edit():
    original = build_steps(EXAMPLE)
    edited = build_steps(EXAMPLE.replace("Stauffer Library, 18", "Stauffer Library, 40"))
    assert len(original) == 17
    assert len(edited) == 16
    assert edited[-1]["output"] == [
        {"name": "Stauffer Library", "count": 40},
        {"name": "West Campus", "count": 32},
        {"name": "Athletics Centre", "count": 32},
        {"name": "Union Street", "count": 7},
    ]
    assert "Send the extra shuttle to Stauffer Library" in edited[-1]["note"]
    assert original[-1]["output"][2] == {"name": "Stauffer Library", "count": 18}


def test_one_stop():
    steps = build_steps("Pier, 9")
    assert [step["kind"] for step in steps] == ["start", "single", "done"]
    assert steps[-1]["output"] == [{"name": "Pier", "count": 9}]
    assert "Send the extra shuttle to Pier" in steps[-1]["note"]


def test_all_zero():
    final = build_steps("Gate, 0\nPier, 0")[-1]
    assert final["output"] == [{"name": "Gate", "count": 0}, {"name": "Pier", "count": 0}]
    assert "standby" in final["note"]


def test_equal_counts_across_halves():
    text = "Z, 5\nB, 5\nM, 5\nC, 5\nA, 5"
    assert build_steps(text)[-1]["output"] == parse_stops(text)


def test_already_ranked_and_reverse_order():
    ordered = "Gate, 8\nPier, 3\nHall, 0"
    for text in [ordered, "Hall, 0\nPier, 3\nGate, 8"]:
        assert build_steps(text)[-1]["output"] == parse_stops(ordered), text


def test_twelve_stops():
    lines = []
    expected = []
    for count in range(1, MAX_STOPS + 1):
        lines.append(f"Stop {count}, {count}")
    for count in range(MAX_STOPS, 0, -1):
        expected.append({"name": f"Stop {count}", "count": count})
    assert build_steps("\n".join(lines))[-1]["output"] == expected


def crowd_count(stop):
    return stop["count"]


def test_exhaustive_short_lists():
    # Python's stable sort provides an independent answer for each test case.
    for size in range(1, 7):
        for counts in product(range(3), repeat=size):
            stops = []
            for index, count in enumerate(counts):
                stops.append({"name": f"Stop {index}", "count": count})
            expected = sorted(stops, key=crowd_count, reverse=True)
            assert merge_sort(stops, []) == expected, counts


def expect_invalid(text, message_parts):
    """Check that the correction message explains the failed input."""
    try:
        parse_stops(text)
    except ValueError as error:
        for part in message_parts:
            assert part in str(error), str(error)
    else:
        raise AssertionError(f"Accepted invalid input: {text!r}")


def test_whitespace_and_limits():
    name = "Q" * 40
    assert parse_stops(f"  Main   Gate , 000\n \n{name}, 999  ") == [
        {"name": "Main Gate", "count": 0}, {"name": name, "count": 999},
    ]


def test_missing_input():
    for text in [None, "", "  \n \n"]:
        expect_invalid(text, ["at least one stop"])


def test_bad_rows():
    cases = [
        ("Hall 7", "one comma"), ("Hall, 7, 9", "one comma"),
        (", 1", "stop name"), ("Hall,", "whole number"),
    ]
    for line, reason in cases:
        expect_invalid("Pier, 2\n\n" + line, ["Line 3", reason])


def test_invalid_counts():
    for count in ["-1", "2.5", "many", "3e2", "1000"]:
        expect_invalid("Pier, 2\nHall, " + count, ["Line 2", "999"])


def test_duplicate_stop():
    expect_invalid("Main Gate, 10\n\n main   GATE , 12", ["Line 3 repeats the stop on line 1"])


def test_oversized_inputs():
    lines = [f"Stop {index}, 2" for index in range(13)]
    expect_invalid("\n".join(lines), ["12 stops"])
    expect_invalid("X" * 41 + ", 1", ["40 characters"])
    expect_invalid("X" * 2001, ["2000 characters"])


def test_saved_steps():
    rows = parse_stops(EXAMPLE)
    steps = []
    merge_sort(rows, steps)
    assert rows == parse_stops(EXAMPLE)
    picks = []
    for step in steps:
        if step["kind"] == "pick":
            left = step["left"][0]
            right = step["right"][0]
            if left["count"] >= right["count"]:
                assert step["output"][-1] == left
            else:
                assert step["output"][-1] == right
            picks.append(step)
        elif step["kind"] == "tail":
            tail = step["left"] + step["right"]
            assert len(tail) > 0
            assert not (step["left"] and step["right"])
            assert step["output"][-len(tail):] == tail
    # Later appends must leave the first pick with just one stop.
    assert picks[0]["output"] == [{"name": "West Campus", "count": 32}]


def test_navigation():
    state = start(EXAMPLE)[0]
    assert previous_step(state)[0] == state
    second = next_step(state)
    assert "Split the group" in second[1]
    assert previous_step(second[0])[1] == render_step(state[0], 0)
    final = show_result(second[0])
    assert "Final ranking" in final[1]
    assert next_step(final[0])[0] == final[0]


def test_edit_and_recovery():
    assert editing()[0] == ([], 0)
    invalid = start("Pier, -2")
    assert invalid[0] == ([], 0)
    assert "Check your input" in invalid[1]
    fixed = start("Pier, 2")[0]
    assert "Send the extra shuttle to Pier" in show_result(fixed)[1]


def test_names_display_as_text():
    steps = build_steps("Hall <A>, 8\nGate & Pier, 2")
    for index in range(len(steps)):
        picture = render_step(steps, index)
        assert "Hall <A>" not in picture
    final_picture = render_step(steps, len(steps) - 1)
    assert "Hall &lt;A&gt;" in final_picture
    assert "Gate &amp; Pier" in final_picture


def load_tests(loader, suite, pattern):
    """Let the standard unittest command run these ordinary test functions."""
    checks = [
        test_sample_tie, test_stauffer_edit, test_one_stop, test_all_zero,
        test_equal_counts_across_halves, test_already_ranked_and_reverse_order,
        test_twelve_stops, test_exhaustive_short_lists, test_whitespace_and_limits,
        test_missing_input, test_bad_rows, test_invalid_counts, test_duplicate_stop,
        test_oversized_inputs, test_saved_steps, test_navigation, test_edit_and_recovery,
        test_names_display_as_text,
    ]
    for check in checks:
        suite.addTest(unittest.FunctionTestCase(check))
    return suite


if __name__ == "__main__":
    unittest.main()
