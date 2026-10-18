"""volume.py: fractional hard-set counting on a hand-computed program, the P-2 table and the P-3 to P-7 bands."""
import unittest
from unittest import mock

try:
    from tests.program_designer import _path  # noqa: F401  (puts scripts/ on sys.path)
except ImportError:  # discovered with -s tests: the tests dir itself is on sys.path
    import _path  # noqa: F401

from lib import library, model, volume

R = model.Row
Day = model.Day
Week = model.Week


def acc(exercise, sets, rir="2", role="accessory"):
    return R(exercise=exercise, role=role, sets=sets, reps="10-12", rir=rir)


def program(weeks, primary_type=None, departures=None):
    return model.Program(client="Sample lifter", block=1, primary_type=primary_type,
                         departures=departures or [], weeks=weeks)


def profile(status=None, **kw):
    return model.Profile(client="Sample lifter", training_status=status, **kw)


def by(result, rule):
    return [c for c in result if c.rule == rule]


def statuses(result, rule):
    return [c.status for c in by(result, rule)]


# --- the hand-computed program ------------------------------------------------------------
#
# Week 1, Day 1                         counted (primary 1, others 0.5, per hard set)
#   Squat 3 x RIR 3-5 (hard)            quadriceps 3, glutes 1.5, hamstrings 1.5
#   Leg Extension 3 x RIR 2             quadriceps 3
#   Romanian Deadlift 3 x RIR 5         nothing: not hard
#   Leg Curl 3 x RIR "6, 4, 2"          hamstrings 2 (sets 2 and 3 are hard)
#   Power Clean 3 x RIR 3               nothing: full_body, reported
#   Plank 2 x RIR 3-5                   abs 2
# Week 1, Day 2
#   Bench Press 4 x RIR 1-2             chest 4, triceps 2, shoulders 2
#   Close Grip Bench Press 2 x RIR 2    triceps 2, chest 1
#   Lateral Raise 3 x RIR 0-1           shoulders 3
#   Lat Pulldown 3 x RIR 4-6 (hard)     lats 3, biceps 1.5
#   Tibialis Raise 2 x RIR 2            nothing: not in the library, reported
# Week 2 (deload), Day 1
#   Squat 2 x RIR 3-5                   quadriceps 2, glutes 1, hamstrings 1
#   Leg Extension 2 x RIR 3             quadriceps 2

W1D1 = {"quadriceps": 6, "glutes": 1.5, "hamstrings": 3.5, "abs": 2}
W1D2 = {"chest": 5, "triceps": 4, "shoulders": 5, "lats": 3, "biceps": 1.5}
W2D1 = {"quadriceps": 4, "glutes": 1, "hamstrings": 1}


def hand_program(**kw):
    return program([
        Week(1, days=[
            Day(1, "Squat", [
                R("Squat", "main", 3, "5", "3-5", 70, basis="65% TM"),
                acc("Leg Extension", 3, "2"),
                acc("Romanian Deadlift", 3, "5"),
                acc("Leg Curl", 3, "6, 4, 2"),
                acc("Power Clean", 3, "3"),
                acc("Plank", 2, "3-5"),
            ]),
            Day(2, "Bench", [
                R("Bench Press", "main", 4, "5", "1-2", 60, basis="75% TM"),
                acc("Close Grip Bench Press", 2, "2"),
                acc("Lateral Raise", 3, "0-1"),
                acc("Lat Pulldown", 3, "4-6"),
                acc("Tibialis Raise", 2, "2"),
            ]),
        ]),
        Week(2, deload=True, days=[
            Day(1, "Squat", [R("Squat", "main", 2, "5", "3-5", 70), acc("Leg Extension", 2, "3")]),
        ]),
    ], **kw)


class Hardness(unittest.TestCase):
    def test_hard_forms(self):
        for rir in ("2", "1-2", "3-5", "2, 2, 1", "4", "4-6", "0", "0-1", "6, 4", 3):
            self.assertTrue(volume.is_hard(acc("Leg Extension", 3, rir)), rir)

    def test_not_hard(self):
        for rir in ("5", "5-6", "6, 5", "", None, "RPE 8", "2 to 3"):
            self.assertFalse(volume.is_hard(acc("Leg Extension", 3, rir)), rir)

    def test_per_set_list_counts_set_by_set(self):
        self.assertEqual(volume.row_sets(acc("Leg Curl", 3, "6, 4, 2")), {"hamstrings": 2})
        self.assertEqual(volume.row_sets(acc("Leg Curl", 3, "2, 6")), {"hamstrings": 1})  # set 3 takes the last entry
        self.assertEqual(volume.row_sets(acc("Leg Curl", 3, "2, 2, 1")), {"hamstrings": 3})


class Counting(unittest.TestCase):
    def test_row_sets(self):
        self.assertEqual(volume.row_sets(R("Squat", "main", 3, "5", "3-5", 70)),
                         {"quadriceps": 3, "glutes": 1.5, "hamstrings": 1.5})
        self.assertEqual(volume.row_sets(acc("Bench Press", 4, "1-2")), {"chest": 4, "triceps": 2, "shoulders": 2})
        self.assertEqual(volume.row_sets(acc("Close Grip Bench Press", 2)), {"triceps": 2, "chest": 1})
        self.assertEqual(volume.row_sets(acc("Romanian Deadlift", 3, "5")), {})
        self.assertEqual(volume.row_sets(acc("Power Clean", 3, "3")), {})
        self.assertEqual(volume.row_sets(acc("Tibialis Raise", 2)), {})
        self.assertEqual(volume.row_sets(acc("Leg Extension", 0)), {})

    def test_full_body_secondary_is_skipped_but_the_rest_counts(self):
        self.assertEqual(volume.row_sets(acc("Thruster", 4)), {"quadriceps": 4, "shoulders": 2})
        self.assertEqual(volume.row_sets(acc("Farmer's Walk", 2)), {"forearms": 2, "traps": 1})

    def test_primary_is_muscle_groups_zero(self):
        for name in ("Bench Press", "Close Grip Bench Press", "Lat Pulldown", "Squat"):
            counted = volume.row_sets(acc(name, 2))
            self.assertEqual(counted[library.muscles(name)[0]], 2, name)

    def test_weekly(self):
        weekly = volume.weekly_sets(hand_program())
        self.assertEqual(weekly[1], {**W1D1, **W1D2})
        self.assertEqual(weekly[2], W2D1)

    def test_sessions(self):
        sessions = volume.session_sets(hand_program())
        self.assertEqual(sessions, {(1, 1): W1D1, (1, 2): W1D2, (2, 1): W2D1})

    def test_empty_week_still_appears(self):
        p = program([Week(1, days=[Day(1, rows=[acc("Leg Extension", 3, "6")])])])
        self.assertEqual(volume.weekly_sets(p), {1: {}})

    def test_unknown_muscle_is_reported_not_counted(self):
        real = library.muscles

        def fake(name):
            return ["neck", "traps"] if name == "Neck Harness" else real(name)

        with mock.patch.object(library, "muscles", side_effect=fake):
            r = acc("Neck Harness", 3)
            self.assertEqual(volume.row_sets(r), {"traps": 1.5})
            text = volume.table(program([Week(1, days=[Day(1, rows=[r])])]))
        self.assertIn("unknown muscle neck", text)
        self.assertNotIn("\nneck", text)


class Table(unittest.TestCase):
    def test_table(self):
        text = volume.table(hand_program())
        lines = text.splitlines()
        header = next(ln for ln in lines if ln.startswith("Muscle"))
        self.assertEqual(header.split(), ["Muscle", "W1", "W2d"])
        rows = {ln.split()[0]: ln.split()[1:] for ln in lines
                if ln.split() and ln.split()[0] in volume.MUSCLES}
        self.assertEqual(rows["quadriceps"], ["6", "4"])
        self.assertEqual(rows["hamstrings"], ["3.5", "1"])
        self.assertEqual(rows["chest"], ["5", "0"])
        self.assertEqual(rows["biceps"], ["1.5", "0"])
        self.assertNotIn("lower_back", rows)   # Romanian Deadlift was not hard
        self.assertLess(lines.index(next(ln for ln in lines if ln.startswith("chest"))),
                        lines.index(next(ln for ln in lines if ln.startswith("quadriceps"))))
        self.assertIn("d = deload week", text)
        self.assertIn("W1 D1 Power Clean row 5 (full_body)", text)
        self.assertIn("W1 D2 Tibialis Raise row 5 (not in the library or alias table)", text)

    def test_empty(self):
        self.assertIn("No hard sets counted.", volume.table(program([Week(1)])))

    def test_unreadable_rir_is_listed(self):
        p = program([Week(1, days=[Day(1, rows=[acc("Leg Extension", 3, "RPE 8")])])])
        self.assertIn("RIR unreadable, not counted: W1 D1 Leg Extension row 1", volume.table(p))


class P2(unittest.TestCase):
    def test_p2_reports_the_table(self):
        p = hand_program()
        p2 = by(volume.checks(p, profile("intermediate")), "P-2")
        self.assertEqual([c.status for c in p2], ["pass"])
        self.assertEqual(p2[0].detail, volume.table(p))

    def test_unreadable_rir_warns(self):
        p = program([Week(1, days=[Day(1, rows=[acc("Leg Extension", 3, "")])])])
        self.assertEqual(statuses(volume.checks(p, profile("novice")), "P-2"), ["warn"])


class P7(unittest.TestCase):
    def run_p7(self, *days):
        p = program([Week(1, days=[Day(i + 1, rows=rows) for i, rows in enumerate(days)])])
        return by(volume.checks(p, profile("intermediate")), "P-7")

    def test_over_11_in_one_session(self):
        p7 = self.run_p7([acc("Leg Extension", 12)])
        self.assertEqual([c.status for c in p7], ["fail", "fail"])
        self.assertIn("over 11", p7[0].detail)
        self.assertEqual(p7[0].where, "W1 D1")
        self.assertIn("at least 2 sessions", p7[1].detail)

    def test_fractional_sets_reach_the_session_cap(self):
        # Squat 8 (quadriceps 8) + Leg Press 4 (quadriceps 4) = 12 in one session.
        p7 = self.run_p7([acc("Squat", 8), acc("Leg Press", 4)])
        self.assertTrue(any("quadriceps gets 12" in c.detail for c in p7))

    def test_11_in_one_session_needs_a_second_session(self):
        p7 = self.run_p7([acc("Leg Extension", 11)])
        self.assertEqual([c.status for c in p7], ["fail"])
        self.assertIn("1 session", p7[0].detail)

    def test_split_over_two_sessions_passes(self):
        self.assertEqual([c.status for c in self.run_p7([acc("Leg Extension", 6)], [acc("Leg Extension", 5)])], ["pass"])

    def test_indirect_work_counts_as_a_session(self):
        # Day 2's Push Press gives quadriceps 0.5 a set: the muscle is trained in 2 sessions.
        self.assertEqual([c.status for c in self.run_p7([acc("Leg Extension", 11)], [acc("Push Press", 2)])], ["pass"])

    def test_10_in_one_session_passes(self):
        self.assertEqual([c.status for c in self.run_p7([acc("Leg Extension", 10)])], ["pass"])

    def test_easy_sets_do_not_count(self):
        self.assertEqual([c.status for c in self.run_p7([acc("Leg Extension", 15, "5-6")])], ["n/a"])

    def test_capped_at_ten(self):
        singles = ["Pec Deck", "Lateral Raise", "Dumbbell Curl", "Rope Pushdown", "Leg Extension", "Leg Curl",
                   "Glute Bridge", "Standing Calf Raise", "Crunch", "Dumbbell Shrug", "Wrist Curl",
                   "Straight Arm Pulldown"]
        p7 = self.run_p7([acc(n, 12) for n in singles])
        self.assertEqual(len(p7), 11)
        self.assertIn("14 more", p7[-1].detail)
        self.assertEqual(p7[-1].status, "fail")

    def test_deload_week_is_checked_too(self):
        p = program([Week(1, deload=True, days=[Day(1, rows=[acc("Leg Extension", 12)])])])
        self.assertIn("fail", statuses(volume.checks(p, profile("novice")), "P-7"))


class NoviceBand(unittest.TestCase):
    def novice_program(self):
        return program([
            Week(1, days=[
                Day(1, rows=[acc("Squat", 6), acc("Dumbbell Fly", 3), acc("Lat Pulldown", 4)]),
                Day(2, rows=[acc("Leg Extension", 6), acc("Dumbbell Row", 4)]),
            ]),
            Week(2, deload=True, days=[Day(1, rows=[acc("Squat", 2), acc("Dumbbell Fly", 1)])]),
        ])

    def test_warns_outside_4_to_10(self):
        p5 = by(volume.checks(self.novice_program(), profile("novice")), "P-5")
        self.assertEqual([c.status for c in p5], ["warn"])
        self.assertEqual(p5[0].where, "W1")
        self.assertIn("quadriceps 12 (above 10)", p5[0].detail)
        self.assertIn("chest 3 (below 4)", p5[0].detail)
        # biceps (2) and glutes (3) get only secondary work: shown, not held to the floor
        self.assertNotIn("biceps", p5[0].detail)
        self.assertNotIn("glutes", p5[0].detail)

    def test_in_band_passes(self):
        p = program([Week(1, days=[Day(1, rows=[acc("Squat", 4), acc("Dumbbell Fly", 4)]),
                                   Day(2, rows=[acc("Leg Extension", 4), acc("Lat Pulldown", 5)])])])
        result = volume.checks(p, profile("novice"))
        self.assertEqual(statuses(result, "P-5"), ["pass"])
        self.assertEqual(statuses(result, "P-3"), ["n/a"])

    def test_deload_week_left_out(self):
        p5 = by(volume.checks(self.novice_program(), profile("novice")), "P-5")
        self.assertFalse(any(c.where == "W2" for c in p5))

    def test_not_novice(self):
        self.assertEqual(statuses(volume.checks(self.novice_program(), profile("advanced")), "P-5"), ["n/a"])

    def test_status_unknown(self):
        p5 = by(volume.checks(self.novice_program(), profile(None)), "P-5")
        self.assertEqual([c.status for c in p5], ["warn"])
        self.assertIn("P-1", p5[0].detail)


class HypertrophyBand(unittest.TestCase):
    def hyp_program(self, **kw):
        return program([Week(1, days=[
            Day(1, rows=[acc("Dumbbell Fly", 4), acc("Leg Extension", 4), acc("Straight Arm Pulldown", 3)]),
            Day(2, rows=[acc("Cable Fly", 4), acc("Straight Arm Pulldown", 3)]),
        ])], primary_type="HYP", **kw)

    def test_priority_and_others(self):
        p3 = by(volume.checks(self.hyp_program(), profile("intermediate"), priority_muscles=["chest"]), "P-3")
        self.assertEqual([c.status for c in p3], ["warn"])
        self.assertIn("priority chest 8 (below 10)", p3[0].detail)
        self.assertIn("quadriceps 4 (below 6)", p3[0].detail)
        self.assertNotIn("lats", p3[0].detail)   # 6 meets the floor

    def test_in_band_passes(self):
        p = program([Week(1, days=[
            Day(1, rows=[acc("Dumbbell Fly", 6), acc("Leg Extension", 6)]),
            Day(2, rows=[acc("Cable Fly", 6), acc("Leg Press", 3)]),
        ])], primary_type="HYP")
        self.assertEqual(statuses(volume.checks(p, profile("advanced"), priority_muscles=["Chest"]), "P-3"), ["pass"])

    def test_priority_synonym(self):
        p3 = by(volume.checks(self.hyp_program(), profile("intermediate"), priority_muscles=["Quads"]), "P-3")
        self.assertIn("priority quadriceps 4 (below 10)", p3[0].detail)

    def test_no_priority_named(self):
        p3 = by(volume.checks(self.hyp_program(), profile("intermediate")), "P-3")
        self.assertTrue(any("CT-HYP-4" in c.detail for c in p3))

    def test_goal_from_profile(self):
        p = self.hyp_program()
        p.primary_type = None
        result = volume.checks(p, profile("intermediate", primary_type="CT-HYP"), priority_muscles=["chest"])
        self.assertEqual(statuses(result, "P-3"), ["warn"])

    def test_other_goals_report_only(self):
        p = self.hyp_program()
        p.primary_type = "PLO"
        result = volume.checks(p, profile("intermediate"))
        self.assertEqual(statuses(result, "P-3"), ["n/a"])
        self.assertEqual(statuses(result, "P-5"), ["n/a"])
        self.assertEqual(statuses(result, "P-2"), ["pass"])

    def test_novice_hypertrophy_uses_p5(self):
        self.assertEqual(statuses(volume.checks(self.hyp_program(), profile("novice")), "P-3"), ["n/a"])


class OverTwenty(unittest.TestCase):
    def big_quads(self, departures=None):
        return program([
            Week(1, days=[Day(1, rows=[acc("Leg Extension", 11)]), Day(2, rows=[acc("Leg Extension", 11)])]),
            Week(2, deload=True, days=[Day(1, rows=[acc("Leg Extension", 11)]), Day(2, rows=[acc("Leg Extension", 11)])]),
        ], primary_type="HYP", departures=departures)

    def test_warns(self):
        p4 = by(volume.checks(self.big_quads(), profile("advanced"), priority_muscles=["quadriceps"]), "P-4")
        self.assertEqual([c.status for c in p4], ["warn"])
        self.assertIn("W1 quadriceps 22", p4[0].detail)
        self.assertNotIn("W2", p4[0].detail)   # the deload week is out of the bands

    def test_departure(self):
        dep = [{"rule": "P-4", "reason": "quad specialisation; 22 sets tolerated last block"}]
        p4 = by(volume.checks(self.big_quads(dep), profile("advanced"), priority_muscles=["quadriceps"]), "P-4")
        self.assertEqual([c.status for c in p4], ["departure"])
        self.assertIn("tolerated", p4[0].detail)

    def test_other_rules_departure_does_not_cover_it(self):
        dep = [{"rule": "P-3", "reason": "something else"}]
        self.assertEqual(statuses(volume.checks(self.big_quads(dep), profile("advanced")), "P-4"), ["warn"])

    def test_twenty_is_fine(self):
        p = program([Week(1, days=[Day(1, rows=[acc("Leg Extension", 10)]), Day(2, rows=[acc("Leg Extension", 10)])])])
        self.assertEqual(statuses(volume.checks(p, profile("advanced")), "P-4"), ["pass"])


class Shape(unittest.TestCase):
    def test_every_rule_reports(self):
        result = volume.checks(hand_program(), profile("intermediate"))
        self.assertEqual({c.rule for c in result}, {"P-2", "P-3", "P-4", "P-5", "P-7"})

    def test_empty_program(self):
        result = volume.checks(program([]), profile("novice"))
        self.assertEqual(statuses(result, "P-7"), ["n/a"])
        self.assertEqual(statuses(result, "P-5"), ["n/a"])
        self.assertEqual(statuses(result, "P-4"), ["n/a"])


if __name__ == "__main__":
    unittest.main()
