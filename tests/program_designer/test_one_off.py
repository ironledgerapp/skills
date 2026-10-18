"""A one-off program (rulebook OO-1 to OO-6): two 4-week blocks drafted together from one intake, with
no check-ins. Block N+1's TMs are block N's plus the L-9 increment, and the lifter does L-9's check
themselves from what the hand-over tells them. Every number here is invented.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.program_designer import _path
from tests.program_designer._programs import profile
from tests.program_designer.test_draft import FULL_GYM, bench
from lib import draft, ironledger_io as io, loads, model, preflight

DESIGNER = _path.SCRIPTS / "designer.py"

# The OO-2 templates, each with a lifter it suits (the same pairs test_draft uses).
ACCEPTED = {
    "531-4day": {"primary_type": "GEN"},
    "531-2x": {"primary_type": "PLO"},
    "531-club": {"primary_type": "RGO", "days": 3},
    "adf-prep": {"primary_type": "ADF", "days": 5, "equipment": FULL_GYM},
    "pt-general": {"primary_type": "PT", "days": 3},
}


def one_off(template="531-4day", benchmarks=None, block=1, **over):
    prof = profile(**{**ACCEPTED.get(template, {}), **over})
    a, b, notes = draft.generate_one_off(template, prof, bench() if benchmarks is None else benchmarks, block=block)
    return prof, a, b, notes


def fails(report):
    return [f"{c.rule}: {c.detail} [{c.where}]" for c in report.checks if c.status == "fail"]


class BothBlocks(unittest.TestCase):
    def test_every_accepted_template_drafts_two_clean_blocks(self):
        for template in ACCEPTED:
            with self.subTest(template=template):
                prof, a, b, _ = one_off(template)
                self.assertEqual((a.block, b.block), (1, 2))                                    # OO-1, IL-2
                self.assertEqual([len(a.weeks), len(b.weeks)], [4, 4])
                for program in (a, b):
                    with tempfile.TemporaryDirectory() as tmp:
                        path = io.write_import(program, tmp)
                        report = preflight.run(program, prof, csv_path=path)
                    self.assertEqual(fails(report), [], "\n".join(fails(report)))

    def test_every_accepted_template_has_4_week_blocks(self):
        for template in draft.ONE_OFF_TEMPLATES:
            self.assertEqual(len(draft.load_template(template)["weeks"]), 4, template)

    def test_block_2_tms_are_block_1_plus_the_l9_increment(self):
        _, a, b, notes = one_off()
        self.assertEqual(a.tms, {"Squat": 107.5, "Bench Press": 87.5, "Deadlift": 150.0, "Overhead Press": 55.0})
        self.assertEqual(b.tms, {"Squat": 112.5, "Bench Press": 90.0, "Deadlift": 155.0, "Overhead Press": 57.5})
        for lift, tm in a.tms.items():
            self.assertEqual(b.tms[lift], tm + loads.tm_increment(lift, "kg"), lift)
        self.assertEqual(b.e1rms, a.e1rms)
        self.assertIn("M28", a.decisions_relied_on)
        self.assertIn("M28", b.decisions_relied_on)
        self.assertTrue(any(n.startswith("OO-4 {M28}") and "Squat 107.5 + 5 = 112.5 kg" in n for n in notes), notes)

    def test_block_2_loads_come_from_its_own_tm(self):
        _, a, b, _ = one_off()
        w1 = next(w for w in b.weeks if w.week == 1)
        squat = [r for d in w1.days for r in d.rows if r.exercise == "Squat" and r.role in ("main", "main_amrap")]
        self.assertEqual([r.load for r in squat], [x[2] for x in loads.wave531(112.5, 1, 2.5)])

    def test_lb_increments(self):
        heavy = {lift: {**b, "weight": b["weight"] * 2} for lift, b in bench().items()}
        _, a, b, _ = one_off(benchmarks=heavy, unit="lb")
        for lift, tm in a.tms.items():
            self.assertEqual(b.tms[lift] - tm, loads.tm_increment(lift, "lb"), lift)
        self.assertEqual(b.tms["Squat"] - a.tms["Squat"], 10)
        self.assertEqual(b.tms["Bench Press"] - a.tms["Bench Press"], 5)

    def test_later_blocks_keep_the_lineage(self):
        _, a, b, _ = one_off(block=3)
        self.assertEqual((a.block, b.block), (3, 4))
        self.assertEqual(a.one_off["blocks"], [3, 4])
        self.assertEqual(b.one_off["blocks"], [3, 4])

    def test_self_check_records_every_block_1_amrap(self):
        _, a, b, _ = one_off()
        self.assertEqual(a.one_off, {"part": 1, "of": 2, "blocks": [1, 2]})
        sc = b.one_off["self_check"]
        self.assertEqual(set(sc), set(a.tms))
        amraps = {(w.week, r.exercise): r for w, _, r in a.rows() if r.role == "main_amrap"}
        for lift, c in sc.items():
            self.assertEqual([x["week"] for x in c["amraps"]], [1, 2, 3], lift)
            self.assertEqual([x["min_reps"] for x in c["amraps"]], [5, 3, 1], lift)
            for x in c["amraps"]:
                self.assertEqual(x["load"], amraps[(x["week"], lift)].load, lift)
            self.assertEqual((c["tm_block1"], c["tm"]), (a.tms[lift], b.tms[lift]))

    def test_novice_floor_is_block_1_only(self):
        _, a, b, _ = one_off(training_status="novice", primary_type="GEN")
        a_weeks = sorted({w.week for w, _, r in a.rows() if r.role == "main_amrap"})
        b_weeks = sorted({w.week for w, _, r in b.rows() if r.role == "main_amrap"})
        self.assertEqual(a_weeks, [3])                    # CT-NOV-1: weeks 1-2 AMRAPs are fixed sets
        self.assertEqual(b_weeks, [1, 2, 3])              # OO-6: block 2 has no floor
        self.assertEqual({x["week"] for c in b.one_off["self_check"].values() for x in c["amraps"]}, {3})

    def test_double_progression_block_2_carries_on(self):
        _, a, b, notes = one_off("pt-general")
        self.assertEqual((a.tms, b.tms), ({}, {}))
        self.assertEqual(b.one_off["self_check"], {})
        self.assertNotIn("M28", b.decisions_relied_on)
        self.assertTrue(notes[-1].startswith("OO-6"), notes[-1])

    def test_the_program_json_round_trips(self):
        _, _, b, _ = one_off()
        back = model.program_from_dict(json.loads(json.dumps(model.to_dict(b))))
        self.assertEqual(back.one_off, b.one_off)


class Refusals(unittest.TestCase):
    def refused(self, fn, rule):
        with self.assertRaises(draft.DraftError) as cm:
            fn()
        self.assertTrue(str(cm.exception).startswith(rule), str(cm.exception))
        return str(cm.exception)

    def test_templates_that_need_check_ins_or_other_lengths(self):
        for template, why in (("topset-backdown", "one block at a time"), ("hypertrophy-rotation", "6 weeks")):
            msg = self.refused(lambda t=template: one_off(t, primary_type="GEN"), "OO-2")
            self.assertIn(why, msg)
            self.assertIn("Draft one block at a time instead", msg)

    def test_a_lift_without_a_benchmark_set(self):
        est = bench(Deadlift={"estimate": 160})
        msg = self.refused(lambda: one_off(benchmarks=est), "OO-3")
        self.assertIn("Deadlift", msg)
        self.assertIn("pt-general", msg)

    def test_an_untested_club_3rm(self):
        untested = bench(Squat={"weight": 100, "reps": 3, "rir": 1, "age_weeks": 2, "logged": False})
        self.refused(lambda: one_off("531-club", benchmarks=untested), "OO-3")

class CommandLine(unittest.TestCase):
    def designer(self, *args):
        return subprocess.run([sys.executable, str(DESIGNER), *map(str, args)], capture_output=True, text=True)

    def test_draft_two_blocks_writes_both_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            model.dump_json(profile(primary_type="GEN"), d / "profile.json")
            (d / "benchmarks.json").write_text(json.dumps(bench()))
            r = self.designer("draft", "531-4day", d / "profile.json", d / "benchmarks.json", "--two-blocks",
                          "--block", 1, "--out", d / "out")
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["programs"], [str(d / "out" / "Block 1" / "program.json"),
                                               str(d / "out" / "Block 2" / "program.json")])
            b = model.load_json(out["programs"][1])
            self.assertEqual((b.block, b.one_off["part"]), (2, 2))
            r = self.designer("draft", "topset-backdown", d / "profile.json", d / "benchmarks.json", "--two-blocks",
                          "--phase", "peak", "--block", 1, "--out", d / "out")
            self.assertEqual(r.returncode, 1)
            self.assertIn("OO-2", r.stderr)


if __name__ == "__main__":
    unittest.main()
