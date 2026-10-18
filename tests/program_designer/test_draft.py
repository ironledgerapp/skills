"""The draft generator (lib.draft) and the templates it reads (assets/templates/*.json).

Every template and every layout is generated for a matching synthetic lifter and must:
  * pass pre-flight with no fail, on the program and on the written import file (G-7); a
    departure is allowed only where the template's rules require one, with its reason
  * with IRONLEDGER_LIVE=1, import cleanly through the live IronLedger program file checker:
    no diagnostic but IL-11's "No load given", and no new exercise names (LB-1)

Then the generator's own behaviour: the TM choice and its notes (L-3), the C2C golden numbers,
a missing benchmark (W-5), choices (A-8, G-15), days (CT-SEL-7) and the junior gate (CT-JUN-1).
Every number here is invented.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

from tests.program_designer import _path  # noqa: F401
from tests.program_designer._programs import build_531, profile
from lib import draft, ironledger_io as io, library, loads, model, preflight

CHECKER = "https://www.ironledger.app/api/tools/program-file"
LIVE = os.environ.get("IRONLEDGER_LIVE") == "1"   # opt in: these tests call the live program file checker

TEMPLATES = ["531-4day", "531-2x", "531-club", "pt-general", "hypertrophy-rotation",
             "topset-backdown", "adf-prep"]
FULL_GYM = ["barbell", "rack", "bench", "dumbbell", "cable", "machine", "pull_up_bar", "dip_bars"]


def bench(**over):
    """Synthetic benchmark sets: 5-rep sets, logged 2 weeks ago at RIR 1 (Squat 100 x 5 is the C2C golden)."""
    out = {"Squat": {"weight": 100, "reps": 5, "rir": 1, "age_weeks": 2, "logged": True},
           "Bench Press": {"weight": 80, "reps": 5, "rir": 1, "age_weeks": 2, "logged": True},
           "Deadlift": {"weight": 140, "reps": 5, "rir": 1, "age_weeks": 2, "logged": True},
           "Overhead Press": {"weight": 50, "reps": 5, "rir": 1, "age_weeks": 2, "logged": True}}
    for lift, value in over.items():
        lift = lift.replace("_", " ")
        if value is None:
            out.pop(lift, None)
        else:
            out[lift] = value
    return out


@dataclass
class Case:
    name: str
    template: str
    over: dict = field(default_factory=dict)       # profile overrides
    kwargs: dict = field(default_factory=dict)     # generate() keywords
    departures: tuple = ()                         # the rules the template must depart from
    days: int = 0                                  # expected Day entries a week
    benchmarks: dict = None                        # None: bench()


CASES = [
    Case("531_4day", "531-4day", {"primary_type": "GEN"}, days=4),
    Case("531_4day_3day", "531-4day", {"primary_type": "GEN", "days": 3}, days=3),
    Case("531_4day_2day", "531-4day", {"primary_type": "GEN"}, {"days": 2}, days=2),
    Case("531_4day_hyp", "531-4day", {"primary_type": "HYP"}, days=4),
    Case("531_4day_lb", "531-4day", {"primary_type": "GEN", "unit": "lb"}, days=4,
         benchmarks={lift: {**b, "weight": b["weight"] * 2} for lift, b in bench().items()}),
    Case("531_2x", "531-2x", {"primary_type": "PLO"}, days=4),
    Case("531_club", "531-club", {"primary_type": "RGO", "days": 3}, departures=("IL-30",), days=3),
    Case("531_club_2day", "531-club", {"primary_type": "RGO", "days": 2}, departures=("IL-30",), days=2),
    Case("531_club_4day", "531-club", {"primary_type": "RGO"}, {"days": 4}, departures=("IL-30",), days=4),
    Case("pt_general", "pt-general", {"primary_type": "PT", "days": 3}, days=3),
    Case("pt_general_2day", "pt-general", {"primary_type": "PT", "days": 2}, days=2),
    Case("pt_general_4day", "pt-general", {"primary_type": "PT"}, {"days": 4}, days=4),
    Case("hypertrophy_rotation", "hypertrophy-rotation", {"primary_type": "HYP", "days": 5}, days=3),
    Case("topset_prep2", "topset-backdown", {"primary_type": "PLM"}, days=4),
    Case("topset_peak", "topset-backdown", {"primary_type": "PLM"}, {"phase": "peak"}, days=4),
    Case("adf_prep", "adf-prep", {"primary_type": "ADF", "days": 5, "equipment": FULL_GYM}, days=5),
    Case("adf_prep_6day", "adf-prep", {"primary_type": "ADF", "days": 6, "equipment": FULL_GYM}, {"days": 6}, days=6),
]


def generate(case: Case):
    prof = profile(**case.over)
    program, notes = draft.generate(case.template, prof, bench() if case.benchmarks is None else case.benchmarks,
                                    **case.kwargs)
    return prof, program, notes


def fails(report):
    return [f"{c.rule}: {c.detail} [{c.where}]" for c in report.checks if c.status == "fail"]


# --- the templates themselves ------------------------------------------------------------------

class TemplateFiles(unittest.TestCase):
    def test_every_template_is_present(self):
        self.assertEqual(sorted(draft.template_ids()), sorted(TEMPLATES))

    def test_pl_macrocycle_waits_for_m10(self):
        self.assertNotIn("pl-macrocycle", draft.template_ids())
        with self.assertRaises(draft.DraftError):
            draft.load_template("pl-macrocycle")

    def test_every_template_validates(self):
        for tid in TEMPLATES:
            with self.subTest(tid):
                self.assertEqual(draft.validate_template(draft.load_template(tid)), [])

    def test_every_name_is_exact(self):
        # the known traps: common names that aren't IronLedger's (LB-1, LB-2)
        traps = {"Incline Dumbbell Press", "Pull-Up", "Pull-Ups", "Chin-Up", "Push-Up", "Pushup", "RDL", "OHP"}
        for tid in TEMPLATES:
            text = json.dumps(draft.load_template(tid))
            for trap in traps:
                self.assertNotIn(f'"{trap}"', text, f"{tid} uses {trap}")

    def test_declared_fields(self):
        for tid in TEMPLATES:
            t = draft.load_template(tid)
            with self.subTest(tid):
                for key in ("id", "client_types", "default_days", "decisions_relied_on", "equipment_required",
                            "layouts", "engine"):
                    self.assertIn(key, t)
                for layout in t["layouts"].values():
                    for slot in draft._layout_slots(layout):
                        self.assertTrue(slot.get("pattern"), slot["id"])
                        if t["engine"] == "topset":
                            self.assertIn("base_rir", slot)
                        elif t["engine"] != "rotation":
                            self.assertIn("rir", slot)
                            self.assertIn("reps", slot)

    def test_timed_slots_only_offer_timed_alternatives(self):
        timed = {"Plank", "Side Plank", "Farmer's Walk"}
        for tid in TEMPLATES:
            for key, layout in draft.load_template(tid)["layouts"].items():
                for slot in draft._layout_slots(layout):
                    for name in [slot["exercise"]] + slot.get("alternatives", []):
                        self.assertEqual(name in timed, bool(slot.get("basis")), f"{tid} {key} {slot['id']} {name}")


# --- every template: pre-flight and the parser --------------------------------------------------

class EveryTemplate(unittest.TestCase):
    def check(self, case: Case):
        prof, program, notes = generate(case)
        self.assertEqual(program.template, case.template)
        self.assertTrue(program.primary_type)
        self.assertTrue(program.decisions_relied_on)
        self.assertEqual({w.week for w in program.weeks}, set(range(1, len(program.weeks) + 1)))
        for w in program.weeks:
            self.assertEqual(len(w.days), case.days, f"week {w.week}")
        for w, d, r in program.rows():
            self.assertIn(r.role, model.ROLES)
            self.assertTrue(r.progression, f"W{w.week} D{d.day} {r.exercise}")           # P-13
            self.assertTrue(library.known(r.exercise), r.exercise)                      # F-7
        self.assertFalse([n for n in notes if n.startswith(("VO-1", "IL-6"))], notes)

        # G-7: departures only where the template's rules require one, each with its reason
        self.assertEqual(sorted({d["rule"] for d in program.departures}), sorted(case.departures))
        self.assertTrue(all(d["reason"].strip() for d in program.departures))

        report = preflight.run(program, prof)
        self.assertEqual(fails(report), [], "\n".join(fails(report)))
        with tempfile.TemporaryDirectory() as tmp:
            path = io.write_import(program, tmp)
            report = preflight.run(program, prof, csv_path=path)
        self.assertEqual(fails(report), [], "\n".join(fails(report)))
        self.assertTrue({c.rule for c in report.checks if c.status == "departure"} <= set(case.departures))


@unittest.skipUnless(LIVE, "set IRONLEDGER_LIVE=1 to check every template with the live IronLedger program file checker")
class EveryTemplateLive(unittest.TestCase):
    """write_import, then IronLedger's own import rules, through check_program_file's HTTP endpoint."""

    def check(self, case: Case):
        import urllib.request
        _, program, _ = generate(case)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(io.write_import(program, Path(tmp) / case.name))
            body = json.dumps({"file": path.read_text(encoding="utf-8"), "fileName": path.name}).encode()
        req = urllib.request.Request(CHECKER, data=body, headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            res = json.loads(resp.read())["result"]
        data = io.import_rows(program)[1:]
        blank = {n for n, r in enumerate(data, start=2) if r[io.LOAD] is None}

        # nothing but IL-11's "No load given", on exactly the blank-load rows
        for issue in res["issues"]:
            self.assertEqual(issue["kind"], "warning", issue)
            self.assertTrue(issue["message"].startswith("No load given."), issue)
        self.assertEqual(sorted(i["row"] for i in res["issues"]), sorted(blank))
        self.assertTrue(res["imports"])
        self.assertEqual(res["newExerciseNames"], [])                                 # LB-1
        self.assertEqual(res["programName"], f"IronLedger Block {program.block}")     # IL-2
        self.assertEqual(res["skippedRowCount"], 0)
        self.assertEqual(res["weekCount"], len(program.weeks))


def _attach(cls):
    for case in CASES:
        setattr(cls, f"test_{case.name}", lambda self, c=case: self.check(c))


_attach(EveryTemplate)
_attach(EveryTemplateLive)


# --- loads, TMs and their notes (L-1 to L-3) ---------------------------------------------------

class TrainingMax(unittest.TestCase):
    def draft(self, prof=None, benchmarks=None, template="531-4day", **kw):
        return draft.generate(template, prof or profile(), bench() if benchmarks is None else benchmarks, **kw)

    def note_for(self, notes, lift):
        return next(n for n in notes if n.startswith(f"{lift}: e1RM"))

    def test_c2c_golden_squat_100_x_5(self):
        program, notes = self.draft()
        self.assertEqual(program.e1rms["Squat"], 117.5)
        self.assertEqual(program.tms["Squat"], 107.5)
        squat = [r for r in program.weeks[0].days[0].rows if r.exercise == "Squat"]
        self.assertEqual([r.load for r in squat], [70.0, 82.5, 92.5, 70.0])      # 65/75/85% wave, FSL at 65%
        self.assertEqual(squat[0].warmup, "Warm-up bar x20, 45x5, 55x5, 65x3")
        note = self.note_for(notes, "Squat")
        for text in ("e1RM 117.5 kg", "100 x 5", "TM 90% = 107.5 kg", "L-3"):
            self.assertIn(text, note)

    def test_matches_the_reference_531_block(self):
        # tests/_programs.build_531 is the hand-built clean block; its Squat e1RM (117.5) is our golden input
        ref = build_531()
        program, _ = self.draft()
        self.assertEqual(len(program.weeks), len(ref.weeks))
        self.assertEqual([w.deload for w in program.weeks], [w.deload for w in ref.weeks])
        key = lambda r: (r.exercise, r.role, r.sets, r.reps, r.rir, r.load, r.basis, r.warmup, r.progression)  # noqa: E731
        for wk in range(3):
            ours = [key(r) for r in program.weeks[wk].days[0].rows if r.exercise == "Squat"]
            theirs = [key(r) for r in ref.weeks[wk].days[0].rows if r.exercise == "Squat"]
            self.assertEqual(ours, theirs, f"week {wk + 1}")
        for ours, theirs in zip(program.weeks, ref.weeks):
            for d_ours, d_ref in zip(ours.days, theirs.days):
                roles = lambda d: [r.role for r in d.rows if r.role not in ("accessory", "accessory_amrap")]  # noqa: E731
                self.assertEqual(roles(d_ours), roles(d_ref))
        deload = program.weeks[3].days[0]
        self.assertIn("Warm-up: Squat bar x20, 45x5, 55x5, 65x3", deload.extras)       # IL-17, L-7
        self.assertTrue(all(r.role == "accessory" for r in deload.rows))

    def test_90_percent_by_default(self):
        program, _ = self.draft()
        self.assertEqual(program.tms, {"Squat": 107.5, "Bench Press": 87.5, "Deadlift": 150.0, "Overhead Press": 55.0})

    def test_85_percent_for_a_novice(self):
        program, notes = self.draft(profile(training_status="novice"))
        self.assertEqual(program.tms["Squat"], loads.training_max(117.5, 0.85, 2.5))
        self.assertIn("TM 85%", self.note_for(notes, "Squat"))
        self.assertIn("novice", self.note_for(notes, "Squat"))

    def test_85_percent_for_a_returning_client(self):
        program, notes = self.draft(profile(flags=["returning"]))
        self.assertEqual(program.tms["Bench Press"], loads.training_max(95.0, 0.85, 2.5))
        self.assertIn("returning", self.note_for(notes, "Bench Press"))

    def test_85_percent_for_an_uncertain_benchmark(self):
        for why, value, text in (("old", {"age_weeks": 10}, "10 weeks old"),
                                 ("self-reported", {"logged": False}, "self-reported"),
                                 ("rated RIR 3", {"rir": 3}, "RIR 3")):
            with self.subTest(why):
                b = bench(Squat={**bench()["Squat"], **value})
                program, notes = self.draft(benchmarks=b)
                self.assertEqual(program.tms["Squat"], 100.0)           # 85% of 117.5 = 99.875, rounded up
                self.assertEqual(program.tms["Bench Press"], 87.5)      # the other lifts keep 90%
                note = self.note_for(notes, "Squat")
                self.assertIn("TM 85%", note)
                self.assertIn(text, note)

    def test_a_single_is_the_weight(self):
        program, notes = self.draft(benchmarks=bench(Squat={"weight": 120, "reps": 1, "logged": True}))
        self.assertEqual(program.e1rms["Squat"], 120.0)                  # L-2: no Epley inflation
        self.assertIn("single", self.note_for(notes, "Squat"))

    def test_more_than_10_reps_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "L-2"):
            self.draft(benchmarks=bench(Squat={"weight": 60, "reps": 12, "logged": True}))

    def test_a_work_set_under_the_bar_is_flagged(self):  # F-5
        program, notes = self.draft(profile(unit="lb"))       # kg-sized numbers read as lb: a 50 lb press
        self.assertTrue(any(n.startswith("F-5: Overhead Press") for n in notes))

    def test_lb_client(self):
        program, _ = self.draft(profile(unit="lb"),
                                benchmarks={k: {**v, "weight": v["weight"] * 2} for k, v in bench().items()})
        self.assertEqual(program.unit, "lb")
        for _, _, r in program.rows():
            if r.role in ("main", "main_amrap", "supplemental"):
                self.assertTrue(loads.is_plate_loadable(r.load, "lb"), r)

    def test_program_round_trips_as_json(self):
        program, _ = self.draft()
        self.assertEqual(model.program_from_dict(model.to_dict(program)), program)


# --- W-5: a main lift with no benchmark ----------------------------------------------------------

class MissingBenchmark(unittest.TestCase):
    def setUp(self):
        self.prof = profile()
        self.program, self.notes = draft.generate("531-4day", self.prof, bench(Squat={"estimate": 120}))

    def test_week_1_is_a_benchmark_session(self):
        rows = [r for r in self.program.weeks[0].days[0].rows if r.exercise == "Squat"]
        self.assertEqual([r.role for r in rows], ["benchmark", "benchmark"])
        ramp, top = rows
        ladder = loads.benchmark_ladder(120, 2.5, "kg")
        self.assertEqual(ramp.load, [load for _, _, load in ladder])     # W-1: bar, 40/50/65/70/80%
        self.assertEqual(ramp.reps, ", ".join(str(r) for _, r, _ in ladder))
        self.assertEqual(ramp.sets, len(ladder))
        self.assertEqual((top.sets, top.reps, top.rir, top.load), (1, "3-5", "1-2", None))

    def test_later_weeks_leave_the_lift_out(self):
        self.assertNotIn("Squat", self.program.tms)
        self.assertNotIn("Squat", self.program.e1rms)
        for w in self.program.weeks[1:]:
            self.assertFalse([r for r in w.days[0].rows if r.exercise == "Squat"], f"week {w.week}")
        self.assertFalse([x for x in self.program.weeks[3].days[0].extras if "Squat bar" in x])
        self.assertTrue(self.program.weeks[1].days[0].rows)              # the day keeps its accessories (IL-6)

    def test_notes_say_to_reissue(self):
        text = " ".join(self.notes)
        self.assertIn("W-5", text)
        self.assertIn("IL-20", text)
        self.assertIn("Re-issue", text)

    def test_blank_benchmark_load_is_a_recorded_departure(self):
        self.assertEqual([d["rule"] for d in self.program.departures], ["IL-11"])
        self.assertEqual(fails(preflight.run(self.program, self.prof)), [])

    def test_no_estimate_is_asked_for_once(self):
        with self.assertRaises(draft.DraftError) as cm:
            draft.generate("531-4day", profile(), bench(Squat=None, Deadlift=None))
        msg = str(cm.exception)
        self.assertIn("W-5", msg)
        self.assertIn("Squat, Deadlift", msg)
        self.assertIn("estimate", msg)

    def test_club_needs_a_confirmed_3rm(self):
        b = bench(Squat={"weight": 100, "reps": 3, "logged": False})
        program, notes = draft.generate("531-club", profile(primary_type="RGO", days=3), b)
        self.assertNotIn("Squat", program.tms)
        top = [r for r in program.weeks[0].days[0].rows if r.exercise == "Squat"][-1]
        self.assertEqual((top.role, top.reps), ("benchmark", "3"))
        self.assertTrue(any("CT-RGO-14" in n for n in notes))


# --- choices (A-8, G-15) --------------------------------------------------------------------------

class Choices(unittest.TestCase):
    def test_a_choice_replaces_the_default(self):
        program, _ = draft.generate("531-4day", profile(), bench(),
                                    choices={"squat.unilateral": {"exercise": "Dumbbell Split Squat",
                                                                  "reason": "Easier on the knee you flagged"}})
        rows = [r for _, _, r in program.rows() if r.exercise == "Dumbbell Split Squat"]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r.reason == "Easier on the knee you flagged" for r in rows))
        self.assertFalse([r for _, _, r in program.rows() if r.exercise == "Bulgarian Split Squat"])
        notes = [row[io.NOTES] for row in io.import_rows(program)[1:] if row[io.EXERCISE] == "Dumbbell Split Squat"]
        self.assertTrue(all(n and n.endswith("Easier on the knee you flagged") for n in notes))

    def test_a_disliked_choice_is_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "dislike"):
            draft.generate("531-4day", profile(dislikes=["Leg Press"]), bench(), choices={"squat.unilateral": "Leg Press"})

    def test_an_avoided_choice_is_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "avoid"):
            draft.generate("531-4day", profile(avoid=["Goblet Squat"]), bench(),
                           choices={"deadlift.squat": {"exercise": "Goblet Squat", "reason": "x"}})

    def test_a_name_outside_the_library_is_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "library"):
            draft.generate("531-4day", profile(), bench(), choices={"press.incline": "Incline Dumbbell Press"})

    def test_an_unknown_slot_is_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "slot"):
            draft.generate("531-4day", profile(), bench(), choices={"squat.nothing": "Leg Press"})

    def test_a_choice_the_equipment_rules_out_is_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "CT-RGO-15"):
            draft.generate("531-club", profile(primary_type="RGO", days=3), bench(), choices={"sb.delts": "Cable Lateral Raise"})

    def test_the_club_ceiling_caps_the_lifters_own_kit(self):  # CT-RGO-15 never widens G-15
        kit = ["barbell", "rack", "bench", "dumbbell"]
        program, _ = draft.generate("531-club", profile(primary_type="RGO", days=3, equipment=kit), bench())
        for _, _, r in program.rows():
            self.assertLessEqual(set(library.equipment(r.exercise)), set(kit) | {"bodyweight", "none"}, r.exercise)
        with self.assertRaisesRegex(draft.DraftError, r"needs dumbbell, which the profile doesn't list \(G-15\)"):
            draft.generate("531-club", profile(primary_type="RGO", days=3, equipment=["barbell", "rack", "bench"]), bench())

    def test_a_disliked_default_is_swapped_with_a_reason(self):
        prof = profile(dislikes=["Bulgarian Split Squat"])
        program, notes = draft.generate("531-4day", prof, bench())
        rows = [r for _, _, r in program.rows() if r.exercise == "Dumbbell Split Squat"]
        self.assertTrue(rows)
        self.assertTrue(all("Bulgarian Split Squat" in r.reason for r in rows))    # A-8, VO-4
        self.assertTrue(any(n.startswith("squat.unilateral") for n in notes))
        self.assertEqual(fails(preflight.run(program, prof)), [])

    def test_a_reason_on_a_deload_day_still_fits_vo1(self):
        # the deload's first row carries the day's extras and the main-lift warm-up (IL-17); the A-8
        # reason is never dropped, so the optional day label gives way instead
        prof = profile(dislikes=["Bulgarian Split Squat"])
        program, notes = draft.generate("531-4day", prof, bench())
        for row in io.import_rows(program)[1:]:
            self.assertLessEqual(draft._words(row[io.NOTES] or ""), 20, row)
        self.assertIsNone(program.weeks[3].days[0].label)
        self.assertEqual(program.weeks[0].days[0].label, "Squat")
        self.assertTrue(any(n.startswith("VO-1: W4 D1") for n in notes))
        swapped = [r for r in program.weeks[3].days[0].rows if r.exercise == "Dumbbell Split Squat"]
        self.assertTrue(swapped and "Bulgarian Split Squat" in swapped[0].reason)      # never dropped (IL-14)
        self.assertEqual(fails(preflight.run(program, prof)), [])

    def test_a_reason_on_a_two_lift_deload_day_moves_down(self):
        prof = profile(primary_type="GEN", days=2)
        program, notes = draft.generate("531-4day", prof, bench(),
                                        choices={"sb.hinge": {"exercise": "Dumbbell Romanian Deadlift",
                                                              "reason": "Easier on the back you flagged"}})
        deload = program.weeks[3].days[0]
        self.assertEqual(deload.rows[0].exercise, "Dumbbell Row")
        self.assertEqual(deload.rows[1].exercise, "Dumbbell Romanian Deadlift")
        self.assertEqual(fails(preflight.run(program, prof)), [])

    def test_missing_equipment_falls_back_and_is_noted(self):
        prof = profile(primary_type="PT", days=3, equipment=["dumbbell", "bench"])
        program, notes = draft.generate("pt-general", prof, None)
        used = {r.exercise for _, _, r in program.rows()}
        self.assertNotIn("Lat Pulldown", used)
        self.assertTrue(all(set(library.equipment(n)) <= {"dumbbell", "bench", "bodyweight", "none"} for n in used))
        self.assertTrue(any(n.startswith("u.pull") for n in notes))
        self.assertEqual(fails(preflight.run(program, prof)), [])

    def test_free_weight_compound_never_planned_at_rir_0(self):
        program, notes = draft.generate("531-4day", profile(primary_type="HYP"), bench(),
                                        choices={"squat.unilateral": "Bulgarian Split Squat"})
        rows = [r for _, _, r in program.rows() if r.exercise == "Bulgarian Split Squat"]
        self.assertTrue(rows)
        self.assertTrue(all(preflight.rir_low(r.rir) >= 1 for r in rows))    # HYP's RIR 0 slot, A-7 bumped
        self.assertTrue(any(n.startswith("A-7") for n in notes))


# --- days, types and gates (CT-SEL-7, CT-JUN-1) -----------------------------------------------------

class Gates(unittest.TestCase):
    def test_more_days_than_the_client_has_are_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "CT-SEL-7"):
            draft.generate("531-4day", profile(days=4), bench(), days=5)

    def test_a_layout_the_rules_dont_give_is_flagged(self):
        with self.assertRaisesRegex(draft.DraftError, "no 3-day layout"):
            draft.generate("531-2x", profile(primary_type="PLO", days=3), bench())

    def test_fewer_days_take_the_reduced_layout(self):
        program, notes = draft.generate("531-4day", profile(days=2), bench())
        self.assertEqual({len(w.days) for w in program.weeks}, {2})
        self.assertEqual([r.exercise for r in program.weeks[0].days[0].rows if r.role == "main"][:1], ["Squat"])
        self.assertFalse([r for _, _, r in program.rows() if r.role == "supplemental"])    # L-14
        self.assertTrue(any("CT-GEN-2" in n for n in notes))

    def test_under_18_is_refused(self):
        with self.assertRaises(draft.DraftError) as cm:
            draft.generate("531-4day", profile(age_band="junior"), bench())
        self.assertIn("CT-JUN-1", str(cm.exception))
        self.assertIn("under 18", str(cm.exception))

    def test_screen_not_cleared_is_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "G-4"):
            draft.generate("531-4day", profile(screen_cleared=False), bench())

    def test_wrong_primary_type_is_refused(self):
        with self.assertRaisesRegex(draft.DraftError, "CT-SEL-1"):
            draft.generate("531-4day", profile(primary_type="PLM"), bench())

    def test_rotation_needs_5_available_days(self):
        with self.assertRaisesRegex(draft.DraftError, "CT-HYP-6"):
            draft.generate("hypertrophy-rotation", profile(primary_type="HYP", days=4), None)

    def test_missing_barbell_kit_goes_to_pt_general(self):
        with self.assertRaisesRegex(draft.DraftError, "CT-SEL-8"):
            draft.generate("531-4day", profile(equipment=["dumbbell", "bench"]), bench())
        program, notes = draft.generate("pt-general", profile(primary_type="RGO", days=3,
                                                              equipment=["dumbbell", "bench", "cable"]), None)
        self.assertEqual(program.primary_type, "RGO")
        self.assertTrue(any("CT-SEL-8" in n for n in notes))

    def test_novice_on_531_needs_measured_benchmarks(self):
        with self.assertRaisesRegex(draft.DraftError, "CT-NOV-2"):
            draft.generate("531-4day", profile(training_status="novice"), bench(Squat={"estimate": 100}))

    def test_phase_only_on_topset(self):
        with self.assertRaises(draft.DraftError):
            draft.generate("531-4day", profile(), bench(), phase="peak")


# --- the rules each engine carries ----------------------------------------------------------------

class EngineRules(unittest.TestCase):
    def test_novice_first_block_stops_at_rir_3(self):  # CT-NOV-1, G-20
        program, _ = draft.generate("531-4day", profile(training_status="novice"), bench())
        for w in program.weeks[:2]:
            for d in w.days:
                for r in d.rows:
                    self.assertNotIn("amrap", r.role, f"W{w.week} {r.exercise}")
                    self.assertGreaterEqual(preflight.rir_low(r.rir), 3, f"W{w.week} {r.exercise} {r.rir}")
        self.assertTrue([r for _, _, r in program.rows() if r.role == "main_amrap"])   # week 3 has its AMRAPs

    def test_amrap_rows_follow_il30(self):
        program, _ = draft.generate("531-4day", profile(), bench())
        for _, _, r in program.rows():
            if r.role == "main_amrap":
                self.assertEqual((r.sets, r.rir), (1, "1-2"))
                self.assertTrue(r.reps.endswith("+"))
            if r.role == "accessory_amrap":
                self.assertEqual((r.sets, r.rir), (1, "0-1"))
                self.assertFalse(library.is_compound(r.exercise) and library.is_free_weight(r.exercise))

    def test_club_amrap_stops_at_rir_2(self):  # CT-RGO-13
        program, _ = draft.generate("531-club", profile(primary_type="RGO", days=3), bench())
        amraps = [r for _, _, r in program.rows() if r.role == "main_amrap"]
        self.assertTrue(amraps)
        self.assertTrue(all(r.rir == "2-3" and "2 in the tank" in r.cue for r in amraps))
        self.assertIn("CT-RGO-13", program.departures[0]["reason"])
        accessory = [r for _, _, r in program.rows() if r.role == "accessory"]
        self.assertTrue(all(preflight.rir_low(r.rir) >= 3 for r in accessory))          # CT-RGO-12
        extras = [x for w in program.weeks for d in w.days for x in d.extras]
        self.assertIn("Warm-up: Limber 11", extras)                                      # CT-RGO-7

    def test_topset_encoding(self):  # CT-PLM-1, CT-PLM-4, CT-PLM-20
        program, _ = draft.generate("topset-backdown", profile(primary_type="PLM"), bench())
        rows = program.weeks[0].days[0].rows
        top, back = rows[0], rows[1]
        self.assertEqual((top.role, back.role), ("topset", "backdown"))
        lo, hi = (float(x) for x in top.basis.removeprefix("Top set ").split("-"))
        self.assertEqual(hi - lo, 10.0)                                                 # squat range 10 kg wide
        self.assertEqual(top.load, lo)                                                  # Load is the low end
        self.assertEqual(top.rir, loads.rpe_to_rir(loads.topset_rpe(1)))                 # RPE 7.5 as RIR 2-3
        self.assertEqual(back.load, loads.backdown((lo + hi) / 2, 0.88, 2.5))
        bench_top = program.weeks[0].days[1].rows[0]
        lo_b, hi_b = (float(x) for x in bench_top.basis.removeprefix("Top set ").split("-"))
        self.assertEqual(hi_b - lo_b, 5.0)                                              # bench range 5 kg wide
        self.assertFalse(program.tms)
        mids = [sum(float(x) for x in w.days[0].rows[0].basis.removeprefix("Top set ").split("-")) / 2
                for w in program.weeks[:4]]
        self.assertTrue(all(b > a for a, b in zip(mids, mids[1:])))                     # CT-PLM-3: the midpoint rises
        deload = program.weeks[4].days[0].rows[0]
        self.assertEqual((deload.sets, deload.reps, deload.rir), (3, "3", "3-4"))       # CT-PLM-6

    def test_peak_leaves_opener_and_second_to_the_lifter(self):  # CT-PLM-14
        program, notes = draft.generate("topset-backdown", profile(primary_type="PLM"), bench(), phase="peak")
        last = program.weeks[-1]
        self.assertFalse([r for d in last.days for r in d.rows if r.role in ("topset", "single")])
        self.assertTrue(any("OPENER" in n and "SECOND" in n and "IL-20" in n for n in notes))
        self.assertFalse([r for d in program.weeks[2].days for r in d.rows if r.role == "accessory"])   # CT-PLM-11

    def test_adf_runs_are_extras_not_rows(self):  # IL-28, CT-ADF-5
        prof = profile(primary_type="ADF", days=5, equipment=FULL_GYM)
        program, _ = draft.generate("adf-prep", prof, bench())
        run_days = [d for d in program.weeks[0].days if not d.rows]
        self.assertEqual(len(run_days), 2)
        self.assertTrue(all(d.extras for d in run_days))
        practice = [d for d in program.weeks[0].days if any(r.exercise == "Push Up" for r in d.rows)]
        self.assertGreaterEqual(len(practice), 3)                                       # CT-ADF-6

    def test_rotation_phases(self):  # CT-HYP-1, CT-HYP-3
        program, _ = draft.generate("hypertrophy-rotation", profile(primary_type="HYP", days=5), None)
        first = [r for r in program.weeks[0].days[0].rows if r.role == "accessory"][0]
        self.assertEqual((first.reps, first.rir), ("13-15", "3"))
        self.assertEqual({r.reps for r in program.weeks[2].days[0].rows if r.role == "accessory"}, {"10-12"})
        late = {r.exercise: r.rir for r in program.weeks[4].days[1].rows if r.role == "accessory"}
        self.assertEqual(late["Bench Press"], "1")                                      # free-weight compound
        self.assertEqual(late["Dumbbell Fly"], "0")                                     # isolation may reach 0

    def test_pt_general_is_written_week_by_week(self):  # CT-PT-1, CT-PT-8
        program, _ = draft.generate("pt-general", profile(primary_type="PT", days=3), None)
        for d in program.weeks[0].days:
            self.assertIn(len(d.rows), (5, 6))
            self.assertTrue(all(r.sets == 3 for r in d.rows))
            self.assertTrue(d.extras[0].startswith("Warm-up:"))                         # CT-PT-2
            self.assertIn(d.rows[-1].exercise, ("Farmer's Walk", "Dead Bug", "Plank"))  # carry or core finisher
        self.assertTrue(program.weeks[-1].deload)


if __name__ == "__main__":
    unittest.main()
