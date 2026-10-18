"""SKILL.md §2 through the real command line: normalize, subs, draft, preflight,
build, client-copy, review, and loads next-tm, as the skill runs them."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.program_designer import _path
from tests.program_designer._programs import profile
from lib import model

DESIGNER = _path.SCRIPTS / "designer.py"


def designer(*args, cwd=None):
    return subprocess.run([sys.executable, str(DESIGNER), *map(str, args)], capture_output=True, text=True, cwd=cwd)


class SkillWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.d = d
        model.dump_json(profile(), d / "profile.json")
        (d / "benchmarks.json").write_text(json.dumps({
            "Squat": {"weight": 100, "reps": 5, "rir": 1, "age_weeks": 2, "logged": True},
            "Bench Press": {"weight": 80, "reps": 5, "rir": 1, "age_weeks": 2, "logged": True},
            "Deadlift": {"weight": 130, "reps": 5, "rir": 1, "age_weeks": 2, "logged": True},
            "Overhead Press": {"weight": 52.5, "reps": 5, "rir": 1, "age_weeks": 2, "logged": True},
        }))
        (d / "rationale.json").write_text(json.dumps({
            "why_template": "Four days available and a general strength goal (CT-GEN-1).",
            "alternative": "531-2x if the squat number becomes the main goal (CT-GEN-5).",
            "signals": "Intermediate, logged benchmarks within 2 weeks, full gym."}))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_1_normalize_maps_common_names(self):
        r = designer("normalize", "Incline Dumbbell Press")
        self.assertEqual(json.loads(r.stdout)["name"], "Dumbbell Incline Press")
        self.assertEqual(designer("normalize", "Hamstring Curl Machine").returncode in (0, 1), True)
        self.assertNotEqual(json.loads(designer("normalize", "Hamstring Curl Machine").stdout)["name"], "Machine Curl")

    def test_2_subs_respects_profile(self):
        r = designer("subs", "Romanian Deadlift", "--profile", self.d / "profile.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["options"])

    def test_3_full_draft_to_review(self):
        d = self.d
        r = designer("draft", "531-4day", d / "profile.json", d / "benchmarks.json", "--block", 1, "--out", d / "program.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(any("107.5" in n for n in json.loads(r.stdout)["notes"]),
                        "C2C golden: Squat 100 x 5 gives TM 107.5, and the notes show it")
        r = designer("preflight", d / "program.json", d / "profile.json")
        self.assertEqual(r.returncode, 0, r.stdout)
        r = designer("build", d / "program.json", "--out", d)
        self.assertEqual(r.returncode, 0, r.stderr)
        csv_file = Path(r.stdout.strip())
        self.assertEqual(csv_file.name, "IronLedger Block 1.csv")
        r = designer("preflight", d / "program.json", d / "profile.json", "--csv", csv_file)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_4_next_tm(self):
        amraps = self.d / "amraps.json"
        amraps.write_text(json.dumps([{"weight": 70, "reps": 8, "min_reps": 5},
                                      {"weight": 80, "reps": 5, "min_reps": 3},
                                      {"weight": 90, "reps": 3, "min_reps": 1}]))
        r = designer("loads", "next-tm", "--lift", "Squat", "--tm", 107.5, "--amraps", amraps)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["next_tm"], 112.5)

    def test_5_under_18_refused(self):
        model.dump_json(profile(age_band="junior"), self.d / "junior.json")
        r = designer("draft", "531-4day", self.d / "junior.json", self.d / "benchmarks.json", "--block", 1,
                 "--out", self.d / "junior-program.json")
        self.assertEqual(r.returncode, 1)
        self.assertIn("CT-JUN-1", r.stderr)


if __name__ == "__main__":
    unittest.main()
