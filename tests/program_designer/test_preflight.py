"""End to end: a clean synthetic block passes pre-flight on the program and on
the written import file; each known defect fails the rule it breaks."""
import tempfile
import unittest

from tests.program_designer import _path  # noqa: F401
from tests.program_designer._programs import build_531, clone, profile
from lib import ironledger_io, preflight


def statuses(report, rule):
    return {c.status for c in report.checks if c.rule == rule}


class CleanBlock(unittest.TestCase):
    def setUp(self):
        self.program = build_531()
        self.profile = profile()

    def test_clean_program_passes(self):
        report = preflight.run(self.program, self.profile)
        fails = [f"{c.rule}: {c.detail} [{c.where}]" for c in report.checks if c.status == "fail"]
        self.assertEqual(fails, [], "\n".join(fails))

    def test_clean_written_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = ironledger_io.write_import(self.program, tmp)
            self.assertTrue(str(path).endswith("IronLedger Block 1.csv"))
            report = preflight.run(self.program, self.profile, csv_path=str(path))
        fails = [f"{c.rule}: {c.detail} [{c.where}]" for c in report.checks if c.status == "fail"]
        self.assertEqual(fails, [], "\n".join(fails))

    def test_report_names_unconfirmed_decisions(self):
        report = preflight.run(self.program, self.profile)
        f9 = [c for c in report.checks if c.rule == "F-9"]
        self.assertTrue(f9 and "M7" in f9[0].detail)


class Defects(unittest.TestCase):
    def run_pf(self, program=None, prof=None):
        return preflight.run(program or build_531(), prof or profile())

    def test_screen_not_cleared_fails_g4(self):
        self.assertIn("fail", statuses(self.run_pf(prof=profile(screen_cleared=False)), "G-4"))

    def test_under_18_always_fails(self):
        self.assertIn("fail", statuses(self.run_pf(prof=profile(age_band="junior")), "CT-JUN-1"))
        r = self.run_pf(prof=profile(age_band="junior", flags=["guardian-consent", "supervised"]))
        self.assertIn("fail", statuses(r, "CT-JUN-1"))

    def test_gates_cannot_be_departed_from(self):
        p = build_531()
        p.departures = [{"rule": "G-4", "reason": "trust me"}, {"rule": "CT-JUN-1", "reason": "keen parent"}]
        r = self.run_pf(p, profile(screen_cleared=False, age_band="junior"))
        self.assertIn("fail", statuses(r, "G-4"))
        self.assertIn("fail", statuses(r, "CT-JUN-1"))
        self.assertNotIn("departure", statuses(r, "G-4") | statuses(r, "CT-JUN-1"))
        self.assertIn("fail", statuses(r, "G-7"))

    def test_disliked_exercise_fails_a8(self):
        self.assertIn("fail", statuses(self.run_pf(prof=profile(dislikes=["Leg Press"])), "A-8"))

    def test_rir0_on_free_weight_compound_fails_a7(self):
        p = build_531()
        for _, _, row in p.rows():
            if row.exercise == "Romanian Deadlift":
                row.rir = "0"
        self.assertIn("fail", statuses(self.run_pf(p), "A-7"))

    def test_unknown_exercise_fails_f7(self):
        p = build_531()
        p.weeks[0].days[3].rows[-2].exercise = "Incline Dumbbell Press"  # a common name; not in the library
        self.assertIn("fail", statuses(self.run_pf(p), "F-7"))

    def test_too_many_days_fails_ct_sel_7(self):
        self.assertIn("fail", statuses(self.run_pf(prof=profile(days=3)), "CT-SEL-7"))

    def test_missing_rir_fails_p9(self):
        p = build_531()
        p.weeks[1].days[2].rows[-1].rir = ""
        self.assertIn("fail", statuses(self.run_pf(p), "P-9"))

    def test_off_step_load_fails_loads_checks(self):
        # 66 kg and 2 kg loads.
        p = build_531()
        p.weeks[0].days[0].rows[1].load = 66
        r = self.run_pf(p)
        self.assertTrue({"fail"} & (statuses(r, "F-5") | statuses(r, "L-4") | statuses(r, "L-5")))
        p2 = build_531()
        p2.weeks[0].days[0].rows[0].load = 2
        self.assertIn("fail", statuses(self.run_pf(p2), "F-5"))

    def test_departure_with_reason_does_not_block(self):
        p = build_531()
        p.weeks[0].days[3].rows[-2].exercise = "Incline Dumbbell Press"
        p.departures = [{"rule": "F-7", "reason": "alias pending approval"}]
        r = self.run_pf(p)
        self.assertIn("departure", statuses(r, "F-7"))
        self.assertNotIn("fail", statuses(r, "F-7"))

    def test_departure_without_reason_fails_g7(self):
        p = build_531()
        p.departures = [{"rule": "P-3", "reason": "  "}]
        self.assertIn("fail", statuses(self.run_pf(p), "G-7"))

    def test_profile_program_mismatch_fails_g16(self):
        self.assertIn("fail", statuses(self.run_pf(prof=profile(client="Someone else")), "G-16"))

    def test_clone_is_independent(self):
        a = build_531()
        b = clone(a)
        b.weeks[0].days[0].rows[0].load = 1
        self.assertNotEqual(a.weeks[0].days[0].rows[0].load, 1)


if __name__ == "__main__":
    unittest.main()
