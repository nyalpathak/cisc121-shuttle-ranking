"""Run from the project folder with python -m unittest discover -s tests -v."""

import unittest
from itertools import product

from app import editing, navigate, start
from display import render_step
from ranking import EXAMPLE, MAX_STOPS, Stop, build_steps, merge_sort, parse_stops


class RankingTests(unittest.TestCase):
    def test_sample_has_a_stable_tie_at_the_top(self):
        final = build_steps(EXAMPLE)[-1]
        self.assertEqual(final.output, [
            Stop("West Campus", 32), Stop("Athletics Centre", 32),
            Stop("Stauffer Library", 18), Stop("Union Street", 7),
        ])
        self.assertIn("Send the extra shuttle to West Campus", final.note)
        self.assertIn("tied for first", final.note)

    def test_one_stop(self):
        steps = build_steps("Pier, 9")
        self.assertEqual([s.kind for s in steps], ["start", "single", "done"])
        self.assertEqual(steps[-1].output, [Stop("Pier", 9)])
        self.assertIn("Send the extra shuttle to Pier", steps[-1].note)

    def test_zero_waiting_at_every_stop(self):
        final = build_steps("Gate, 0\nPier, 0")[-1]
        self.assertEqual(final.output, [Stop("Gate", 0), Stop("Pier", 0)])
        self.assertIn("standby", final.note)

    def test_equal_counts_keep_their_order_across_halves(self):
        text = "Z, 5\nB, 5\nM, 5\nC, 5\nA, 5"
        self.assertEqual(build_steps(text)[-1].output, parse_stops(text))

    def test_already_ranked_and_reverse_order(self):
        ordered = "Gate, 8\nPier, 3\nHall, 0"
        for text in [ordered, "Hall, 0\nPier, 3\nGate, 8"]:
            with self.subTest(text=text):
                self.assertEqual(build_steps(text)[-1].output, parse_stops(ordered))

    def test_twelve_stops(self):
        text = "\n".join(f"Stop {n}, {n}" for n in range(1, MAX_STOPS + 1))
        expected = [Stop(f"Stop {n}", n) for n in range(MAX_STOPS, 0, -1)]
        self.assertEqual(build_steps(text)[-1].output, expected)

    def test_exhaustive_short_lists(self):
        # Only the test uses Python's stable sort as an independent reference.
        for size in range(1, 7):
            for counts in product(range(3), repeat=size):
                stops = [Stop(f"Stop {i}", n) for i, n in enumerate(counts)]
                expected = sorted(stops, key=lambda stop: stop.count, reverse=True)
                self.assertEqual(merge_sort(stops, []), expected, msg=str(counts))


class InputTests(unittest.TestCase):
    def test_blank_lines_whitespace_and_limits(self):
        name = "Q" * 40
        self.assertEqual(parse_stops(f"  Main   Gate , 000\n \n{name}, 999  "),
                         [Stop("Main Gate", 0), Stop(name, 999)])

    def test_missing_input(self):
        for text in [None, "", "  \n \n"]:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "at least one stop"):
                parse_stops(text)

    def test_missing_fields_and_bad_separators(self):
        for line, reason in [("Hall 7", "one comma"), ("Hall, 7, 9", "one comma"),
                             (", 1", "stop name"), ("Hall,", "whole number")]:
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, "Line 3.*" + reason):
                parse_stops("Pier, 2\n\n" + line)

    def test_invalid_counts(self):
        for count in ["-1", "2.5", "many", "3e2", "1000"]:
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, "Line 2.*999"):
                parse_stops("Pier, 2\nHall, " + count)

    def test_duplicate_stop_reports_both_lines(self):
        with self.assertRaisesRegex(ValueError, "Line 3 repeats the stop on line 1"):
            parse_stops("Main Gate, 10\n\n main   GATE , 12")

    def test_oversized_inputs(self):
        too_many = "\n".join(f"Stop {i}, 2" for i in range(13))
        for text, reason in [(too_many, "12 stops"), ("X" * 41 + ", 1", "40 characters"),
                             ("X" * 2001, "2000 characters")]:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                parse_stops(text)


class SimulationTests(unittest.TestCase):
    def test_input_unchanged_and_snapshots_match_real_picks(self):
        rows = parse_stops(EXAMPLE)
        original = rows.copy()
        steps = []
        merge_sort(rows, steps)
        self.assertEqual(rows, original)
        for step in steps:
            if step.kind == "pick":
                left, right = step.left[0], step.right[0]
                expected = left if left.count >= right.count else right
                self.assertEqual(step.output[-1], expected)
            if step.kind == "tail":
                tail = step.left + step.right
                self.assertTrue(tail)
                self.assertFalse(step.left and step.right)
                self.assertEqual(step.output[-len(tail):], tail)
        first_pick = next(step for step in steps if step.kind == "pick")
        self.assertEqual(first_pick.output, [Stop("West Campus", 32)])

    def test_navigation_replay_and_bounds(self):
        state = start(EXAMPLE)[0]
        self.assertEqual(navigate(state, "back")[0][1], 0)
        next_state, split_picture, *_ = navigate(state, "next")
        self.assertIn("Split the group", split_picture)
        self.assertEqual(navigate(next_state, "back")[1], render_step(state[0], 0))
        final_state, final_picture, *_ = navigate(next_state, "result")
        self.assertIn("Final ranking", final_picture)
        self.assertEqual(navigate(final_state, "next")[0], final_state)

    def test_edit_error_and_recovery(self):
        self.assertEqual(editing()[0], ([], 0))
        state, picture, *_ = start("Pier, -2")
        self.assertEqual(state, ([], 0))
        self.assertIn("Check your input", picture)
        fixed = start("Pier, 2")[0]
        self.assertIn("Send the extra shuttle to Pier", navigate(fixed, "result")[1])

    def test_stop_names_are_displayed_as_text(self):
        steps = build_steps("Hall <A>, 8\nGate & Pier, 2")
        for index in range(len(steps)):
            picture = render_step(steps, index)
            self.assertNotIn("Hall <A>", picture)
        self.assertIn("Hall &lt;A&gt;", picture)
        self.assertIn("Gate &amp; Pier", picture)


if __name__ == "__main__":
    unittest.main()
