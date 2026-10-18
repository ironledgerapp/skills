"""loads.py: the golden numbers, rounding edge cases, lb rules and the pre-flight checks.

The checks fixtures reproduce common spreadsheet defects: loads rounded to 5 instead of 2.5, a hard-coded 2 kg set, 66 and 99 kg loads,
duplicate wave loads, work sets under the bar and the 5/5/5 warm-up.
"""
import copy
import unittest

try:
    from tests.program_designer import _path  # noqa: F401  (puts scripts/ on sys.path)
except ImportError:  # discovered with -s tests: the tests dir itself is on sys.path
    import _path  # noqa: F401

from lib import loads, model
from lib.checks import Check

R = model.Row


# --- fixture: a clean kg block (Squat TM 107.5, Bench Press TM 80) -----------------------

SQ_WARM = "Warm-up bar x20, 45x5, 55x5, 65x3"
BN_WARM = "Warm-up bar x20, 32.5x5, 40x5, 50x3"

# week -> [(load, % TM, reps)], computed by hand: CEILING(TM x pct, 2.5)
SQUAT = {
    1: [(70, 65, "5"), (82.5, 75, "5"), (92.5, 85, "5+")],      # 69.875, 80.625, 91.375
    2: [(77.5, 70, "3"), (87.5, 80, "3"), (97.5, 90, "3+")],    # 75.25, 86, 96.75
    3: [(82.5, 75, "5"), (92.5, 85, "3"), (102.5, 95, "1+")],   # 80.625, 91.375, 102.125
}
BENCH = {
    1: [(52.5, 65, "5"), (60, 75, "5"), (70, 85, "5+")],         # 52, 60, 68
    2: [(57.5, 70, "3"), (65, 80, "3"), (72.5, 90, "3+")],       # 56, 64, 72
    3: [(60, 75, "5"), (70, 85, "3"), (77.5, 95, "1+")],         # 60, 68, 76
}


def main_rows(exercise, spec, warm):
    rows = []
    for i, (load, pct, reps) in enumerate(spec):
        amrap = reps.endswith("+")
        rows.append(R(exercise=exercise, role="main_amrap" if amrap else "main", sets=1, reps=reps,
                      rir="1-2" if amrap else "3-5", load=load, basis=f"{pct}% TM",
                      warmup=warm if i == 0 else None))
    return rows


def build_kg():
    weeks = []
    for wk in (1, 2, 3):
        sq_fsl = SQUAT[wk][0]
        bn_fsl = BENCH[wk][0]
        d1 = model.Day(1, "Squat", main_rows("Squat", SQUAT[wk], SQ_WARM) + [
            R("Squat", "supplemental", 5, "5", "3-5", sq_fsl[0], basis=f"{sq_fsl[1]}% TM"),
            R("Goblet Squat", "accessory", 3, "10-12", "2"),
        ])
        d2 = model.Day(2, "Bench", main_rows("Bench Press", BENCH[wk], BN_WARM) + [
            R("Bench Press", "supplemental", 5, "5", "3-5", bn_fsl[0], basis=f"{bn_fsl[1]}% TM"),
            R("Barbell Row", "accessory", 3, "8-10", "2", 60),
        ])
        weeks.append(model.Week(wk, days=[d1, d2]))
    weeks.append(model.Week(4, deload=True, days=[
        model.Day(1, "Squat", [R("Goblet Squat", "accessory", 2, "10-12", "3")]),
        model.Day(2, "Bench", [R("Barbell Row", "accessory", 2, "8-10", "3", 60)]),
    ]))
    return model.Program(client="Sample lifter", block=1, unit="kg",
                         tms={"Squat": 107.5, "Bench Press": 80.0},
                         e1rms={"Squat": 117.5, "Bench Press": 87.5}, weeks=weeks)


def kg_profile(**kw):
    return model.Profile(client="Sample lifter", unit="kg", **kw)


def by(result, rule):
    return [c for c in result if c.rule == rule]


def statuses(result, rule):
    return [c.status for c in by(result, rule)]


def row(program, week, day, index):
    return program.weeks[week - 1].days[day - 1].rows[index - 1]


# --- the maths -------------------------------------------------------------------------------

class UnitsAndSteps(unittest.TestCase):
    def test_bar(self):
        self.assertEqual(loads.bar_weight("kg"), 20)
        self.assertEqual(loads.bar_weight("lb"), 45)
        self.assertEqual(loads.bar_weight("KG"), 20)
        with self.assertRaises(ValueError):
            loads.bar_weight("stone")

    def test_steps(self):
        self.assertEqual(loads.step_for("kg"), 2.5)
        self.assertEqual(loads.step_for("kg", microplates=True), 1.25)
        self.assertEqual(loads.step_for("lb"), 5)
        self.assertEqual(loads.step_for("lb", microplates=True), 2.5)

    def test_plate_loadable_kg(self):
        self.assertTrue(loads.is_plate_loadable(20, "kg"))
        self.assertTrue(loads.is_plate_loadable(22.5, "kg"))
        self.assertTrue(loads.is_plate_loadable(107.5, "kg"))
        self.assertFalse(loads.is_plate_loadable(17.5, "kg"), "under the bar")
        self.assertFalse(loads.is_plate_loadable(2, "kg"), "a hard-coded 2 kg")
        self.assertFalse(loads.is_plate_loadable(66, "kg"), "66 kg")
        self.assertFalse(loads.is_plate_loadable(99, "kg"), "P3's 99 kg")
        self.assertFalse(loads.is_plate_loadable(81.25, "kg"))
        self.assertTrue(loads.is_plate_loadable(81.25, "kg", microplates=True))
        self.assertFalse(loads.is_plate_loadable("Bar", "kg"))
        self.assertFalse(loads.is_plate_loadable(None, "kg"))

    def test_plate_loadable_lb(self):
        self.assertTrue(loads.is_plate_loadable(45, "lb"))
        self.assertTrue(loads.is_plate_loadable(135, "lb"))
        self.assertFalse(loads.is_plate_loadable(40, "lb"), "under the 45 lb bar")
        self.assertFalse(loads.is_plate_loadable(137.5, "lb"))
        self.assertTrue(loads.is_plate_loadable(137.5, "lb", microplates=True))
        self.assertFalse(loads.is_plate_loadable(20, "lb"), "a kg bar in an lb file")


class RoundUp(unittest.TestCase):
    def test_exact_multiple_stays(self):
        self.assertEqual(loads.round_up(107.5, 2.5), 107.5)
        self.assertEqual(loads.round_up(100, 2.5), 100)
        self.assertEqual(loads.round_up(0, 2.5), 0)

    def test_float_noise_never_adds_a_step(self):
        self.assertEqual(repr(100 * 1.1), "110.00000000000001")  # the trap: a naive ceil gives 112.5
        self.assertEqual(loads.round_up(100 * 1.1, 2.5), 110)
        self.assertEqual(loads.round_up(50 * 1.1, 2.5), 55)
        self.assertEqual(loads.round_up(107.50000000000001, 2.5), 107.5)
        self.assertEqual(repr(175 * 0.7), "122.49999999999999")
        self.assertEqual(loads.round_up(175 * 0.7, 2.5), 122.5)

    def test_ceiling_not_nearest_not_floor(self):
        self.assertEqual(loads.round_up(105.75, 2.5), 107.5)
        self.assertEqual(loads.round_up(100.1, 2.5), 102.5)   # nearest would be 100
        self.assertEqual(loads.round_up(102.4, 2.5), 102.5)
        self.assertEqual(loads.round_up(69.875, 2.5), 70)

    def test_step_matters(self):
        # Wendler's CEILING(..., 5) is a pound habit; in kg it overshoots.
        self.assertEqual(loads.round_up(80.625, 2.5), 82.5)
        self.assertEqual(loads.round_up(80.625, 5), 85)
        self.assertEqual(loads.round_up(80.625, 1.25), 81.25)
        self.assertEqual(loads.round_up(146.25, 5), 150)

    def test_no_long_decimals(self):
        for n in range(0, 800):
            for step in (1.25, 2.5, 5):
                x = loads.round_up(n * step, step)
                self.assertEqual(x, round(n * step, 4))
                self.assertLessEqual(len(repr(x).split(".")[-1]), 2, repr(x))

    def test_bad_step(self):
        with self.assertRaises(ValueError):
            loads.round_up(10, 0)
        with self.assertRaises(ValueError):
            loads.round_up(10, -2.5)


class E1rmAndTM(unittest.TestCase):
    def test_c2c_worked_example(self):
        # 100 x 5 -> e1RM 117.5 -> TM 107.5; next cycle 112.5.
        e = loads.e1rm(100, 5, 2.5)
        self.assertEqual(e, 117.5)  # 100 + 100 x 5 x 0.0333 = 116.65, rounded up
        tm = loads.training_max(e, 0.90, 2.5)
        self.assertEqual(tm, 107.5)  # 105.75, rounded up
        met = [(92.5, 6, 5), (97.5, 4, 3), (102.5, 2, 1)]
        self.assertEqual(loads.next_tm(tm, "Squat", met, "kg")[0], 112.5)

    def test_single_is_the_weight(self):
        self.assertEqual(loads.e1rm(140, 1, 2.5), 140)
        self.assertEqual(loads.e1rm(130, 1, 5), 130)  # a formula that adds reps to a single gives 135

    def test_formula_values(self):
        self.assertEqual(loads.e1rm(102.5, 8, 2.5), 130)   # 129.806
        self.assertEqual(loads.e1rm(75, 3, 2.5), 82.5)     # 82.4925
        self.assertEqual(loads.e1rm(100, 5, 5), 120)       # the 5 kg step overshoots
        self.assertEqual(loads.e1rm(102.5, 7, 2.5), 127.5)  # 126.39

    def test_input_limits(self):
        for bad in ((100, 11), (100, 0), (0, 5), (-20, 5), (100, 2.5)):
            with self.assertRaises(ValueError, msg=bad):
                loads.e1rm(bad[0], bad[1], 2.5)

    def test_tm(self):
        self.assertEqual(loads.training_max(117.5, 0.90, 2.5), 107.5)
        self.assertEqual(loads.training_max(117.5, 0.85, 2.5), 100)  # 99.875
        self.assertEqual(loads.training_max(120, 0.9, 5), 110)
        with self.assertRaises(ValueError):
            loads.training_max(117.5, 0.95, 2.5)
        with self.assertRaises(ValueError):
            loads.training_max(117.5, 90, 2.5)


class Parity(unittest.TestCase):
    def test_an1_examples(self):
        self.assertEqual(loads.e1rm_parity(75, 3), 83)       # 82.5 rounds half up; Python round gives 82
        self.assertEqual(loads.e1rm_parity(100, 1), 100)
        self.assertEqual(loads.e1rm_parity(150, 3), 165)
        self.assertEqual(loads.e1rm_parity(102.5, 8), 130)
        self.assertEqual(loads.e1rm_parity(60, 20), 100)     # no rep cap
        self.assertEqual(loads.e1rm_parity(397.5, 4), 451)   # 450.5

    def test_zero_and_single(self):
        self.assertEqual(loads.e1rm_parity(0, 5), 0)
        self.assertEqual(loads.e1rm_parity(100, 0), 0)
        self.assertEqual(loads.e1rm_parity(-5, 3), 0)
        self.assertEqual(loads.e1rm_parity(102.5, 1), 102.5)
        self.assertIsInstance(loads.e1rm_parity(75, 3), int)

    def test_never_mixed_with_programming_e1rm(self):
        # AN-2: the same set gives 83 in the app and 82.5 for programming.
        self.assertNotEqual(loads.e1rm_parity(75, 3), loads.e1rm(75, 3, 2.5))

    def test_61_half_cases(self):
        # AN-1: 61 cases between 40 and 400 kg at 2 to 10 reps where round() would disagree.
        import math
        n = 0
        for i in range(16, 161):
            for r in range(2, 11):
                x = i * 2.5 * (1 + r / 30)
                if round(x) != loads.e1rm_parity(i * 2.5, r):
                    n += 1
                    self.assertEqual(loads.e1rm_parity(i * 2.5, r), math.floor(x + 0.5))
        self.assertEqual(n, 61)


class Wave(unittest.TestCase):
    def test_c2c_waves(self):
        self.assertEqual(loads.wave531(107.5, 1, 2.5), [(0.65, "5", 70), (0.75, "5", 82.5), (0.85, "5+", 92.5)])
        self.assertEqual(loads.wave531(107.5, 2, 2.5), [(0.70, "3", 77.5), (0.80, "3", 87.5), (0.90, "3+", 97.5)])
        self.assertEqual(loads.wave531(107.5, 3, 2.5), [(0.75, "5", 82.5), (0.85, "3", 92.5), (0.95, "1+", 102.5)])

    def test_round_tm_stays_exact(self):
        self.assertEqual([x[2] for x in loads.wave531(100, 1, 2.5)], [65, 75, 85])
        self.assertEqual([x[2] for x in loads.wave531(100, 2, 2.5)], [70, 80, 90])
        self.assertEqual([x[2] for x in loads.wave531(100, 3, 2.5)], [75, 85, 95])

    def test_rounding_to_5_is_a_different_answer(self):
        self.assertEqual([x[2] for x in loads.wave531(107.5, 1, 5)], [70, 85, 95])
        self.assertNotEqual(loads.wave531(107.5, 1, 5), loads.wave531(107.5, 1, 2.5))

    def test_every_wave_rises_and_rounds_up(self):
        for unit, step, lo, hi in (("kg", 2.5, 40, 300), ("lb", 5, 95, 700), ("kg", 1.25, 40, 200)):
            tm = lo
            while tm <= hi:
                for week in (1, 2, 3):
                    wave = loads.wave531(tm, week, step)
                    ws = [x[2] for x in wave]
                    self.assertTrue(all(b > a for a, b in zip(ws, ws[1:])), (unit, tm, week, ws))
                    for pct, _, load in wave:
                        self.assertTrue(loads._is_multiple(load, step), (tm, load))
                        self.assertGreaterEqual(load + 1e-9, tm * pct)
                        self.assertLess(load, tm * pct + step)
                    self.assertTrue(wave[-1][1].endswith("+"))
                    self.assertFalse(any(r.endswith("+") for _, r, _ in wave[:-1]))
                tm += step

    def test_week_4_is_the_deload(self):
        for bad in (0, 4, 5):
            with self.assertRaises(ValueError):
                loads.wave531(107.5, bad, 2.5)


class WarmUp(unittest.TestCase):
    def test_c2c_warmup(self):
        self.assertEqual(loads.warmup531(107.5, 2.5, "kg"),
                         [("Bar", 20, 20), ("40%", 5, 45), ("50%", 5, 55), ("60%", 3, 65)])
        self.assertEqual(loads.warmup_note(107.5, 2.5, "kg"), "Warm-up bar x20, 45x5, 55x5, 65x3")

    def test_half_kilo_formatting(self):
        self.assertEqual(loads.warmup_note(80, 2.5, "kg"), "Warm-up bar x20, 32.5x5, 40x5, 50x3")

    def test_light_lift_never_below_the_bar(self):
        # P9's OHP: 40% and 50% both land at or under the bar. F-5: they become the bar.
        self.assertEqual([x[2] for x in loads.warmup531(40, 2.5, "kg")], [20, 20, 20, 25])
        self.assertEqual(loads.warmup_note(40, 2.5, "kg"), "Warm-up bar x20, 20x5, 20x5, 25x3")
        for tm in range(20, 120):
            for _, _, load in loads.warmup531(tm, 2.5, "kg"):
                self.assertGreaterEqual(load, 20)
                self.assertTrue(loads.is_plate_loadable(load, "kg"))

    def test_lb_warmup(self):
        self.assertEqual([x[2] for x in loads.warmup531(225, 5, "lb")], [45, 90, 115, 135])
        self.assertEqual(loads.warmup_note(225, 5, "lb"), "Warm-up bar x20, 90x5, 115x5, 135x3")
        self.assertEqual([x[2] for x in loads.warmup531(60, 5, "lb")], [45, 45, 45, 45])

    def test_warmup_is_5_5_3_not_5_5_5(self):
        self.assertEqual([x[1] for x in loads.warmup531(107.5, 2.5, "kg")], [20, 5, 5, 3])


class Supplemental(unittest.TestCase):
    def test_fsl(self):
        self.assertEqual(loads.fsl(107.5, 1, 2.5), (0.65, "5", 70, 5))
        self.assertEqual(loads.fsl(107.5, 2, 2.5), (0.70, "5", 77.5, 5))
        self.assertEqual(loads.fsl(107.5, 3, 2.5, sets=3), (0.75, "5", 82.5, 3))
        for bad in (2, 6):
            with self.assertRaises(ValueError):
                loads.fsl(107.5, 1, 2.5, sets=bad)
        with self.assertRaises(ValueError):
            loads.fsl(107.5, 4, 2.5)

    def test_deload_accessory(self):
        self.assertEqual(loads.deload_accessory(3, "2"), (2, "3"))
        self.assertEqual(loads.deload_accessory(4, "2-3"), (2, "3-4"))
        self.assertEqual(loads.deload_accessory(5, "0-1"), (3, "3"))
        self.assertEqual(loads.deload_accessory(2, "3"), (1, "4"))
        self.assertEqual(loads.deload_accessory(1, "2"), (1, "3"))
        self.assertEqual(loads.deload_accessory(3, "2, 2, 1"), (2, "3, 3"))
        for n in range(2, 13):
            kept, _ = loads.deload_accessory(n, "2")
            self.assertTrue(0.3 <= (n - kept) / n <= 0.5, (n, kept))
        with self.assertRaises(ValueError):
            loads.deload_accessory(3, "RPE 8")

    def test_benchmark_ladder(self):
        self.assertEqual(loads.benchmark_ladder(100, 2.5, "kg"),
                         [("Bar", 20, 20), ("40%", 6, 40), ("50%", 4, 50), ("65%", 2, 65), ("70%", 2, 70), ("80%", 1, 80)])
        self.assertEqual([x[2] for x in loads.benchmark_ladder(40, 2.5, "kg")], [20, 20, 20, 27.5, 30, 32.5])


class TopSetBackDown(unittest.TestCase):
    def test_ranges_kg(self):
        self.assertEqual(loads.topset_range(180, "Squat", "kg"), (175, 185))
        self.assertEqual(loads.topset_range(200, "Deadlift", "kg"), (195, 205))
        self.assertEqual(loads.topset_range(100, "Bench Press", "kg"), (97.5, 102.5))
        self.assertEqual(loads.topset_range(181, "Squat", "kg"), (177.5, 187.5))  # mid rounds up first

    def test_ranges_lb(self):
        self.assertEqual(loads.topset_range(400, "Squat", "lb"), (390, 410))
        self.assertEqual(loads.topset_range(225, "Bench Press", "lb"), (220, 230))
        lo, hi = loads.topset_range(402, "Deadlift", "lb")
        self.assertEqual(hi - lo, 20)
        self.assertTrue(loads.is_plate_loadable(lo, "lb") and loads.is_plate_loadable(hi, "lb"))

    def test_backdown(self):
        self.assertEqual(loads.backdown(180, 0.88, 2.5), 160)    # 158.4
        self.assertEqual(loads.backdown(180, 0.85, 2.5), 155)    # 153
        self.assertEqual(loads.backdown(180, 0.87, 2.5), 157.5)  # 156.6
        self.assertEqual(loads.backdown(100, 0.92, 2.5), 92.5)   # PEAK
        self.assertEqual(loads.backdown(400, 0.88, 5), 355)      # lb: 352
        with self.assertRaises(ValueError):
            loads.backdown(180, 88, 2.5)


class RpeRir(unittest.TestCase):
    def test_ct_plm_20(self):
        self.assertEqual(loads.rpe_to_rir(8), "2")
        self.assertEqual(loads.rpe_to_rir(7.5), "2-3")
        self.assertEqual(loads.rpe_to_rir(9), "1")
        self.assertEqual(loads.rpe_to_rir(8.5), "1-2")
        self.assertEqual(loads.rpe_to_rir("8-8.5"), "1-2")       # "RPE 8 to 8.5 is 1-2"
        self.assertEqual(loads.rpe_to_rir("RPE 8 to 8.5"), "1-2")
        self.assertEqual(loads.rpe_to_rir((8, 8.5)), "1-2")
        self.assertEqual(loads.rpe_to_rir("7.5-8"), "2-3")
        self.assertEqual(loads.rpe_to_rir(10), "0")
        self.assertEqual(loads.rpe_to_rir(9.5), "0-1")
        self.assertEqual(loads.rpe_to_rir(6), "4")

    def test_ascii_hyphen_only(self):
        for rpe in (6.5, 7.5, 8.5, 9.5, "8–8.5"):
            text = loads.rpe_to_rir(rpe)
            self.assertNotIn("–", text)
            self.assertNotIn(" ", text)

    def test_bad_rpe(self):
        for bad in (11, 0, "hard", "8-9-10"):
            with self.assertRaises(ValueError, msg=bad):
                loads.rpe_to_rir(bad)

    def test_topset_rpe_ct_plm_5(self):
        self.assertEqual([loads.topset_rpe(w) for w in (1, 2, 3, 4)], ["7.5", "7.5-8", "8", "8-8.5"])
        self.assertEqual([loads.rpe_to_rir(loads.topset_rpe(w)) for w in (1, 2, 3, 4)], ["2-3", "2-3", "2", "1-2"])
        self.assertEqual(loads.topset_rpe(8, start=8), "9")            # capped outside PEAK
        self.assertEqual(loads.topset_rpe(8, start=8, peak=True), "9.5-10")

    def test_accessory_rir_ct_plm_13(self):
        self.assertEqual([loads.accessory_rir_plm(2, w) for w in (1, 2, 3, 4)], ["2", "1-2", "1-2", "1"])
        self.assertEqual(loads.accessory_rir_plm(2, 1, deload=True), "3")
        self.assertEqual(loads.accessory_rir_plm(3, 1, deload=True), "4")
        self.assertEqual(loads.accessory_rir_plm(0, 2), "0")   # never below 0 (F-8)
        self.assertEqual(loads.accessory_rir_plm(0, 4), "0")
        self.assertEqual(loads.accessory_rir_plm(2.5, 1), "2-3")
        with self.assertRaises(ValueError):
            loads.accessory_rir_plm(2, 5)


class LbRules(unittest.TestCase):
    def test_f11_numbers(self):
        self.assertEqual(loads.step_for("lb"), 5)
        self.assertEqual(loads.bar_weight("lb"), 45)
        self.assertEqual(loads.tm_increment("Squat", "lb"), 10)
        self.assertEqual(loads.tm_increment("Deadlift", "lb"), 10)
        self.assertEqual(loads.tm_increment("Bench Press", "lb"), 5)
        self.assertEqual(loads.tm_increment("Overhead Press", "lb"), 5)

    def test_kg_increments(self):
        self.assertEqual(loads.tm_increment("Squat", "kg"), 5)
        self.assertEqual(loads.tm_increment("High Bar Squat", "kg"), 5)
        self.assertEqual(loads.tm_increment("Sumo Deadlift", "kg"), 5)
        self.assertEqual(loads.tm_increment("Bench Press", "kg"), 2.5)
        self.assertEqual(loads.tm_increment("Overhead Press", "kg"), 2.5)

    def test_convert(self):
        self.assertEqual(loads.convert_kg(20, "lb"), 45)      # 44.092
        self.assertEqual(loads.convert_kg(100, "lb"), 225)    # 220.46
        self.assertEqual(loads.convert_kg(100, "lb", microplates=True), 222.5)
        self.assertEqual(loads.convert_kg(101, "kg"), 102.5)

    def test_next_tm_lb(self):
        met = [(185, 6, 5), (195, 4, 3), (205, 2, 1)]
        self.assertEqual(loads.next_tm(225, "Squat", met, "lb")[0], 235)
        self.assertEqual(loads.next_tm(185, "Bench Press", met, "lb")[0], 190)

    def test_lb_wave(self):
        self.assertEqual([x[2] for x in loads.wave531(225, 1, 5)], [150, 170, 195])  # 146.25, 168.75, 191.25


class NextTM(unittest.TestCase):
    MET = [(92.5, 7, 5), (97.5, 5, 3), (102.5, 3, 1)]

    def test_standard_increment(self):
        tm, why = loads.next_tm(107.5, "Squat", self.MET, "kg")
        self.assertEqual(tm, 112.5)
        self.assertIn("L-9", why)
        self.assertEqual(loads.next_tm(80, "Bench Press", self.MET, "kg")[0], 82.5)
        self.assertEqual(loads.next_tm(50, "Overhead Press", self.MET, "kg")[0], 52.5)
        self.assertEqual(loads.next_tm(140, "Deadlift", self.MET, "kg")[0], 145)

    def test_one_miss_holds(self):
        tm, why = loads.next_tm(107.5, "Squat", [(92.5, 7, 5), (97.5, 2, 3), (102.5, 2, 1)], "kg")
        self.assertEqual(tm, 107.5)
        self.assertIn("hold", why)

    def test_two_misses_not_consecutive_hold(self):
        tm, _ = loads.next_tm(107.5, "Squat", [(92.5, 4, 5), (97.5, 4, 3), (102.5, 0, 1)], "kg")
        self.assertEqual(tm, 107.5)

    def test_two_consecutive_misses_reset(self):
        # Latest AMRAP with reps: 97.5 x 2 -> e1RM 103.99 -> 105; TM 94.5 -> 95.
        tm, why = loads.next_tm(107.5, "Squat", [(92.5, 6, 5), (97.5, 2, 3), (102.5, 0, "1+")], "kg")
        self.assertEqual(tm, 95)
        self.assertIn("L-10", why)
        self.assertIn("tell the lifter", why)

    def test_two_consecutive_misses_without_reps(self):
        tm, why = loads.next_tm(107.5, "Squat", [(92.5, 0, 5), (97.5, 0, 3)], "kg")
        self.assertEqual(tm, 107.5)
        self.assertIn("deload", why)

    def test_reset_never_raises_tm(self):
        tm, why = loads.next_tm(100, "Squat", [(85, 4, 5), (110, 4, 5)], "kg")
        self.assertEqual(tm, 100)
        self.assertIn("L-10", why)

    def test_l11_moves_beyond_the_increment(self):
        # Heaviest 102.5 x 7 -> e1RM 127.5; prior 125 agrees within 5%; 0.9 x 127.5 = 114.75 -> 115.
        amraps = [(92.5, 10, 5), (97.5, 8, 3), (102.5, 7, 1)]
        tm, why = loads.next_tm(107.5, "Squat", amraps, "kg", prior_e1rms=(125,))
        self.assertEqual(tm, 115)
        self.assertIn("L-11", why)

    def test_l11_needs_a_prior_that_agrees(self):
        amraps = [(92.5, 10, 5), (97.5, 8, 3), (102.5, 7, 1)]
        self.assertEqual(loads.next_tm(107.5, "Squat", amraps, "kg")[0], 112.5)
        self.assertEqual(loads.next_tm(107.5, "Squat", amraps, "kg", prior_e1rms=(110,))[0], 112.5)
        self.assertEqual(loads.next_tm(107.5, "Squat", amraps, "kg", prior_e1rms=(121.5,))[0], 115)  # 4.9%
        self.assertEqual(loads.next_tm(107.5, "Squat", amraps, "kg", prior_e1rms=(121,))[0], 112.5)  # 5.4%

    def test_l11_blocked_by_a_grind(self):
        amraps = [{"weight": 92.5, "reps": 10, "min_reps": "5+"}, {"weight": 97.5, "reps": 8, "min_reps": "3+"},
                  {"weight": 102.5, "reps": 7, "min_reps": "1+", "rpe": 10}]
        self.assertEqual(loads.next_tm(107.5, "Squat", amraps, "kg", prior_e1rms=(125,))[0], 112.5)
        amraps[-1] = {"weight": 102.5, "reps": 7, "min_reps": 1, "form_ok": False}
        self.assertEqual(loads.next_tm(107.5, "Squat", amraps, "kg", prior_e1rms=(125,))[0], 112.5)

    def test_amrap_over_10_ignored(self):
        amraps = [(92.5, 12, 5), (97.5, 9, 3), (102.5, 12, 1)]   # e1RM from 102.5 x 12 would be 145
        tm, why = loads.next_tm(107.5, "Squat", amraps, "kg", prior_e1rms=(145,))
        self.assertEqual(tm, 112.5)
        self.assertIn("over 10", why)

    def test_l11_below_the_increment_takes_the_increment(self):
        amraps = [(92.5, 6, 5), (97.5, 4, 3), (102.5, 2, 1)]    # e1RM 110 -> 99 -> 100
        self.assertEqual(loads.next_tm(107.5, "Squat", amraps, "kg", prior_e1rms=(110,))[0], 112.5)

    def test_no_amraps_hold(self):
        self.assertEqual(loads.next_tm(107.5, "Squat", [], "kg")[0], 107.5)


# --- the checks --------------------------------------------------------------------------------

class ChecksClean(unittest.TestCase):
    def test_clean_program_passes(self):
        result = loads.checks(build_kg(), kg_profile())
        self.assertTrue(all(isinstance(c, Check) for c in result))
        for rule in ("L-4", "L-5", "L-6", "F-5", "F-11"):
            self.assertEqual(statuses(result, rule), ["pass"], (rule, by(result, rule)))

    def test_fixture_matches_the_functions(self):
        # The hand-written fixture and the maths agree, so the checks test real numbers.
        for wk in (1, 2, 3):
            self.assertEqual([x[2] for x in loads.wave531(107.5, wk, 2.5)], [x[0] for x in SQUAT[wk]])
            self.assertEqual([x[2] for x in loads.wave531(80, wk, 2.5)], [x[0] for x in BENCH[wk]])
        self.assertEqual(loads.warmup_note(80, 2.5, "kg"), BN_WARM)

    def test_nothing_to_check_is_na(self):
        p = model.Program(client="Sample lifter", block=1, weeks=[model.Week(1, days=[
            model.Day(1, rows=[R("Goblet Squat", "accessory", 3, "10-12", "2")])])])
        result = loads.checks(p, kg_profile())
        for rule in ("L-4", "L-5", "L-6", "F-5"):
            self.assertEqual(statuses(result, rule), ["n/a"], rule)
        self.assertEqual(statuses(result, "F-11"), ["pass"])


class ChecksDefects(unittest.TestCase):
    def setUp(self):
        self.p = build_kg()
        self.prof = kg_profile()

    def run_checks(self, profile=None):
        return loads.checks(self.p, profile or self.prof)

    def test_rounded_to_5_fails_l5(self):
        # a wave rounded to 5 kg (70, 85, 95 for TM 107.5).
        row(self.p, 1, 1, 2).load = 85
        row(self.p, 1, 1, 3).load = 95
        result = self.run_checks()
        self.assertEqual(statuses(result, "L-4"), ["pass"], "85 and 95 are multiples of 2.5")
        l5 = by(result, "L-5")
        self.assertEqual([c.status for c in l5], ["fail", "fail"])
        self.assertIn("82.5", l5[0].detail)
        self.assertEqual(l5[0].where, "W1 D1 Squat row 2")

    def test_hard_coded_2kg_set(self):
        # a load cell hard-coded as 2 -> "Low Bar Squat 2 kg x 3" in week 2.
        row(self.p, 2, 1, 1).load = 2
        result = self.run_checks()
        f5 = by(result, "F-5")
        self.assertIn("fail", [c.status for c in f5])
        self.assertTrue(any("dumbbell or technique-bar" in c.detail for c in f5))
        self.assertIn("fail", statuses(result, "L-4"))
        self.assertTrue(any("77.5" in c.detail for c in by(result, "L-5")))

    def test_66_and_99_kg(self):
        # "5 x 66kg" and "3 x 99kg".
        row(self.p, 1, 1, 1).load = 66
        row(self.p, 1, 2, 5).load = 99    # a barbell accessory: F-5 only, not a computed load
        result = self.run_checks()
        l4 = by(result, "L-4")
        self.assertEqual([c.status for c in l4], ["fail"])
        self.assertIn("66", l4[0].detail)
        f5_details = " | ".join(c.detail for c in by(result, "F-5"))
        self.assertIn("66", f5_details)
        self.assertIn("99", f5_details)

    def test_non_plate_warmup(self):
        row(self.p, 1, 1, 1).warmup = "Warm-up bar x20, 45x5, 66x5, 99x3"
        result = self.run_checks()
        self.assertEqual(len([c for c in by(result, "F-5") if c.status == "fail"]), 2)
        self.assertEqual(statuses(result, "L-6"), ["fail"])

    def test_warmup_under_the_bar(self):
        row(self.p, 1, 1, 1).warmup = "Warm-up bar x20, 17.5x5, 55x5, 65x3"
        result = self.run_checks()
        self.assertTrue(any("under the bar" in c.detail for c in by(result, "F-5")))

    def test_wave_not_rising(self):
        row(self.p, 1, 1, 2).load = 70
        result = self.run_checks()
        f5 = by(result, "F-5")
        self.assertEqual([c.status for c in f5], ["fail"])
        self.assertIn("does not rise", f5[0].detail)
        self.assertEqual(f5[0].where, "W1 D1 Squat")

    def test_wave_falling(self):
        row(self.p, 3, 2, 3).load = 65
        result = self.run_checks()
        self.assertTrue(any("does not rise" in c.detail for c in by(result, "F-5")))

    def test_main_row_repeating_one_load_fails(self):
        r = row(self.p, 1, 1, 1)
        r.sets = 2
        result = self.run_checks()
        self.assertTrue(any("does not rise" in c.detail for c in by(result, "F-5")))

    def test_duplicates_allowed_for_fsl_backdown_accessory(self):
        day = self.p.weeks[0].days[0]
        day.rows += [
            R("Squat", "topset", 1, "3", "1-2", 175, basis="Top set 175-185"),
            R("Squat", "backdown", 3, "3", "3-5", 160, basis="Back-off 88% of top set"),
            R("Barbell Row", "accessory", 3, "8", "2", [60, 60, 60]),
        ]
        result = self.run_checks()
        self.assertEqual(statuses(result, "F-5"), ["pass"])
        self.assertEqual(statuses(result, "L-4"), ["pass"])

    def test_under_bar_work_set(self):
        # OHP TM 25: 65/75/85% -> 17.5, 20, 22.5. The 17.5 set is flagged with a DB option.
        self.p.tms["Overhead Press"] = 25
        spec = [(17.5, 65, "5"), (20, 75, "5"), (22.5, 85, "5+")]
        warm = loads.warmup_note(25, 2.5, "kg")
        self.assertEqual(warm, "Warm-up bar x20, 20x5, 20x5, 20x3")
        self.p.weeks[0].days.append(model.Day(3, "OHP", main_rows("Overhead Press", spec, warm)))
        result = self.run_checks()
        f5 = by(result, "F-5")
        self.assertEqual([c.status for c in f5], ["fail"])
        self.assertIn("under the 20 kg bar", f5[0].detail)
        self.assertIn("dumbbell or technique-bar", f5[0].detail)
        self.assertEqual(statuses(result, "L-5"), ["pass"])
        self.assertEqual(statuses(result, "L-6"), ["pass"])

    def test_ez_bar_is_not_held_to_the_olympic_bar(self):
        self.p.weeks[0].days[1].rows.append(R("EZ Bar Curl", "accessory", 3, "10-12", "2", 15))
        self.assertEqual(statuses(self.run_checks(), "F-5"), ["pass"])

    def test_missing_warmup(self):
        row(self.p, 2, 2, 1).warmup = None
        l6 = by(self.run_checks(), "L-6")
        self.assertEqual([c.status for c in l6], ["fail"])
        self.assertEqual(l6[0].where, "W2 D2 Bench Press row 1")

    def test_house_555_warmup_fails(self):
        # a 40/50/60 x 5/5/5 warm-up; M5 uses Wendler's 5/5/3.
        row(self.p, 1, 1, 1).warmup = "Warm-up bar x20, 45x5, 55x5, 65x5"
        self.assertEqual(statuses(self.run_checks(), "L-6"), ["fail"])

    def test_warmup_on_a_later_row_only(self):
        row(self.p, 1, 1, 1).warmup = None
        row(self.p, 1, 1, 2).warmup = SQ_WARM
        self.assertEqual(statuses(self.run_checks(), "L-6"), ["fail"])

    def test_warmup_without_prefix_is_accepted(self):
        row(self.p, 1, 1, 1).warmup = "bar x20, 45x5, 55x5, 65x3"
        self.assertEqual(statuses(self.run_checks(), "L-6"), ["pass"])

    def test_missing_tm(self):
        del self.p.tms["Bench Press"]
        l5 = by(self.run_checks(), "L-5")
        self.assertEqual([c.status for c in l5], ["fail"])
        self.assertIn("W-5", l5[0].detail)

    def test_tm_found_by_family(self):
        self.p.tms = {"Squat": 107.5, "Bench": 80}
        self.assertEqual(statuses(self.run_checks(), "L-5"), ["pass"])

    def test_tm_not_on_step(self):
        self.p.tms["Squat"] = 106
        result = self.run_checks()
        self.assertTrue(any(c.where == "TM Squat" and c.status == "fail" for c in by(result, "L-4")))

    def test_amrap_label(self):
        row(self.p, 1, 1, 3).reps = "5"
        l5 = by(self.run_checks(), "L-5")
        self.assertIn("fail", [c.status for c in l5])
        self.assertTrue(any("'5+'" in c.detail for c in l5))

    def test_plus_on_a_non_amrap_row(self):
        row(self.p, 1, 1, 1).reps = "5+"
        self.assertIn("fail", statuses(self.run_checks(), "L-5"))

    def test_wrong_week_of_the_wave(self):
        # Week 2 given week 1's percentages: every load matches its basis, but it is the wrong wave.
        day = self.p.weeks[1].days[0]
        day.rows[:3] = main_rows("Squat", SQUAT[1], SQ_WARM)
        l5 = by(self.run_checks(), "L-5")
        self.assertEqual([c.status for c in l5], ["fail"])
        self.assertIn("70/80/90", l5[0].detail)

    def test_list_load_with_list_basis(self):
        day = self.p.weeks[0].days[0]
        day.rows[:2] = [R("Squat", "main", 2, "5", "3-5", [70, 82.5], basis="65%, 75% TM", warmup=SQ_WARM)]
        result = self.run_checks()
        self.assertEqual(statuses(result, "L-5"), ["pass"])
        self.assertEqual(statuses(result, "F-5"), ["pass"])
        day.rows[0].load = [70, 85]
        self.assertIn("fail", statuses(self.run_checks(), "L-5"))

    def test_basis_not_a_tm_percentage_warns(self):
        row(self.p, 1, 1, 1).basis = None
        self.assertEqual(statuses(self.run_checks(), "L-5"), ["warn"])

    def test_non_numeric_load(self):
        row(self.p, 1, 1, 1).load = "Bar"
        result = self.run_checks()
        self.assertIn("fail", statuses(result, "L-4"))
        self.assertIn("fail", statuses(result, "F-5"))

    def test_capped_at_ten_rows(self):
        self.p.weeks[0].days[0].rows += [R("Squat", "supplemental", 1, "5", "3-5", 66 + i * 0.1) for i in range(15)]
        l4 = by(self.run_checks(), "L-4")
        self.assertEqual(len(l4), 11)
        self.assertEqual(l4[-1].status, "fail")
        self.assertIn("5 more", l4[-1].detail)
        self.assertIsNone(l4[-1].where)

    def test_microplates(self):
        row(self.p, 1, 1, 2).load = 81.25        # 80.625 to 1.25 instead of 2.5
        result = self.run_checks(kg_profile(microplates=True))
        for rule in ("L-4", "L-5", "F-5"):
            self.assertEqual(statuses(result, rule), ["pass"], rule)
        result = self.run_checks()
        for rule in ("L-4", "L-5", "F-5"):
            self.assertIn("fail", statuses(result, rule), rule)

    def test_microplate_client_on_the_2_5_step_is_fine(self):
        for rule in ("L-4", "L-5", "L-6"):
            self.assertEqual(statuses(self.run_checks(kg_profile(microplates=True)), rule), ["pass"], rule)


class ChecksUnits(unittest.TestCase):
    def build_lb(self):
        wave = {wk: [(ld, round(p * 100), r) for p, r, ld in loads.wave531(225, wk, 5)] for wk in (1, 2, 3)}
        warm = loads.warmup_note(225, 5, "lb")
        weeks = [model.Week(wk, days=[model.Day(1, "Squat", main_rows("Squat", wave[wk], warm))]) for wk in (1, 2, 3)]
        return model.Program(client="Sample lb lifter", block=1, unit="lb", tms={"Squat": 225}, weeks=weeks)

    def test_lb_program_passes(self):
        p = self.build_lb()
        self.assertEqual([row(p, 1, 1, i).load for i in (1, 2, 3)], [150, 170, 195])
        result = loads.checks(p, model.Profile(client="Sample lb lifter", unit="lb"))
        for rule in ("L-4", "L-5", "L-6", "F-5", "F-11"):
            self.assertEqual(statuses(result, rule), ["pass"], (rule, by(result, rule)))
        self.assertIn("45 lb", by(result, "F-11")[0].detail)

    def test_lb_half_step_needs_microplates(self):
        p = self.build_lb()
        p.weeks[0].days[0].rows.append(R("Squat", "supplemental", 5, "5", "3-5", 147.5, basis="65% TM"))
        self.assertIn("fail", statuses(loads.checks(p, model.Profile(client="Sample lb lifter", unit="lb")), "L-4"))
        self.assertEqual(statuses(loads.checks(p, model.Profile(client="Sample lb lifter", unit="lb", microplates=True)), "L-4"),
                         ["pass"])

    def test_kg_bar_in_an_lb_file(self):
        p = self.build_lb()
        p.weeks[0].days[0].rows.append(R("Squat", "supplemental", 5, "5", "3-5", 40))
        f5 = by(loads.checks(p, model.Profile(client="Sample lb lifter", unit="lb")), "F-5")
        self.assertTrue(any("45 lb bar" in c.detail for c in f5))

    def test_unit_mismatch(self):
        p = build_kg()
        f11 = by(loads.checks(p, model.Profile(client="Sample lifter", unit="lb")), "F-11")
        self.assertEqual([c.status for c in f11], ["fail"])
        self.assertIn("profile", f11[0].detail)

    def test_other_unit_named_in_text(self):
        p = self.build_lb()
        row(p, 1, 1, 3).cue = "Top set around 90 kg"
        self.assertEqual(statuses(loads.checks(p, model.Profile(client="Sample lb lifter", unit="lb")), "F-11"), ["fail"])
        p = build_kg()
        row(p, 1, 1, 1).load = "140kg"
        self.assertIn("fail", statuses(loads.checks(p, kg_profile()), "F-11"))

    def test_unknown_unit(self):
        result = loads.checks(build_kg(), model.Profile(client="Sample lifter", unit="stone"))
        self.assertEqual(statuses(result, "F-11"), ["fail"])
        self.assertEqual(statuses(result, "L-4"), ["n/a"])

    def test_checks_do_not_mutate_the_program(self):
        p = build_kg()
        before = copy.deepcopy(model.to_dict(p))
        loads.checks(p, kg_profile())
        self.assertEqual(model.to_dict(p), before)


if __name__ == "__main__":
    unittest.main()
