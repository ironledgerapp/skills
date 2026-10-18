"""ironledger_io: the import file's cells, Notes, CSV writer, reader and gate checks.

Every program here is synthetic (tests/program_designer/fixtures/programs.py).
Rule IDs are from the program designer's references/ironledger-import.md
unless marked otherwise.

Ownership: ironledger_io owns the file's format. Whether a load is
plate-loadable (F-5: a 2 kg barbell set, 66 or 99 kg) is lib.loads' check,
The tests for those fixtures assert only what this module owns: the load is
written as a number, IL-10 passes, and this module doesn't report F-5 twice.
"""
import csv
import tempfile
import unittest
from pathlib import Path

try:
    from . import _path  # noqa: F401  (python -m unittest tests.test_ironledger_io)
    from .fixtures import programs as fx
except ImportError:
    import _path  # noqa: F401  (python -m unittest discover -s tests)
    from fixtures import programs as fx

from lib import ironledger_io as io
from lib import model



def statuses(checks, rule):
    return {c.status for c in checks if c.rule == rule}


def fails(checks):
    return [c for c in checks if c.status == "fail"]


def rows_where(program, pred):
    return [r for _, _, r in program.rows() if pred(r)]


def first_row(program, pred):
    return rows_where(program, pred)[0]


def pad(row, n=8):
    return list(row) + [None] * (n - len(row))


class TmpDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.profile = fx.profile()

    def tearDown(self):
        self._tmp.cleanup()

    def edit(self, path, **cells):
        """Change cells in a written file, the way a hand edit would. Refs are sheet-style, e.g. F2."""
        with open(path, encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        for ref, value in cells.items():
            col, row = io.COLS.index(ref[0]) if ref[0] in io.COLS else ord(ref[0]) - ord("A"), int(ref[1:]) - 1
            while len(rows) <= row:
                rows.append([])
            while len(rows[row]) <= col:
                rows[row].append("")
            rows[row][col] = "" if value is None else str(value)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh, lineterminator="\n").writerows(rows)

    def raw(self, path):
        with open(path, encoding="utf-8", newline="") as fh:
            return list(csv.reader(fh))

    def ref_of(self, program, col, pred):
        """The sheet cell (e.g. E7) of the first import row whose model row matches pred."""
        for i, e in enumerate(io._plan(program)):
            if pred(e.row):
                return f"{io.COLS[col]}{i + 2}"
        raise AssertionError("no such row")


# --- import_rows and notes_for ----------------------------------------------------------

class TestImportRows(unittest.TestCase):
    def setUp(self):
        self.program = fx.program_531_4day()
        self.rows = io.import_rows(self.program)
        self.data = self.rows[1:]

    def test_header_is_exact(self):  # IL-3
        self.assertEqual(self.rows[0], ["Week", "Day", "Exercise", "Sets", "Reps", "Load", "RIR", "Notes"])

    def test_cell_types(self):  # IL-5, IL-6, IL-8, IL-9, IL-10, IL-12
        for r in self.data:
            week, day, ex, sets, reps, load, rir, notes = r
            self.assertIs(type(week), int)
            self.assertRegex(day, r"^Day [1-4]$")
            self.assertIsInstance(ex, str)
            self.assertIs(type(sets), int)
            self.assertIsInstance(reps, str)
            self.assertTrue(load is None or type(load) in (int, float), load)
            self.assertIsInstance(rir, str)
            self.assertTrue(notes is None or isinstance(notes, str))

    def test_whole_loads_are_ints(self):
        loads = [r[5] for r in self.data if r[5] is not None]
        self.assertIn(80, loads)
        self.assertTrue(all(type(v) is int for v in loads if float(v).is_integer()))

    def test_row_counts(self):
        # 3 loading weeks x (4 main-lift days) + a deload with accessories only (L-7, IL-17)
        self.assertEqual(len(self.data), 106)
        self.assertEqual(sorted({r[0] for r in self.data}), [1, 2, 3, 4])

    def test_rows_sorted_week_day(self):  # IL-6
        keys = [(r[0], int(r[1].split()[1])) for r in self.data]
        self.assertEqual(keys, sorted(keys))

    def test_first_work_row_carries_day_and_warm_up(self):  # IL-14 (2) (6) (7) (9), IL-17
        self.assertEqual(self.data[0][:8], [1, "Day 1", "Squat", 1, "5", 80, "3-5",
                                            "Day: Squat · Rest 3 min · 65% TM · Warm-up bar x20, 50x5, 60x5, 72.5x3"])
        # the warm-up is never a row, and only the lift's first work row carries it
        self.assertFalse(any("Warm-up" in r[2] for r in self.data))
        squat_w1 = [r for r in self.data if r[0] == 1 and r[2] == "Squat"]
        self.assertEqual(sum("Warm-up bar" in (r[7] or "") for r in squat_w1), 1)

    def test_amrap_row(self):  # IL-9, IL-30, L-13
        amrap = self.data[2]
        self.assertEqual(amrap[3:7], [1, "5+", 102.5, "1-2"])
        self.assertEqual(amrap[7], "AMRAP · Rest 3 min · 85% TM · "
                                   "as many strong reps as you can, leaving 1 to 2 in the tank")

    def test_percentage_rows_carry_rir_range(self):  # IL-30
        for e, r in zip(io._plan(self.program), self.data):
            if e.row.role in ("main", "supplemental"):
                self.assertEqual(r[6], "3-5")

    def test_fsl_row(self):  # L-14 as one row of 5 sets
        fsl = self.data[3]
        self.assertEqual(fsl[2:8], ["Squat", 5, "5", 80, "3-5", "Rest 2 min · 65% TM"])

    def test_accessory_loads_blank(self):  # IL-11
        for e, r in zip(io._plan(self.program), self.data):
            if e.row.role in ("main", "main_amrap", "supplemental"):
                self.assertIsNotNone(r[5])
        self.assertIsNone(self.data[4][5])  # Bulgarian Split Squat

    def test_bodyweight_load_is_zero(self):  # IL-10
        chin = [r for r in self.data if r[2] == "Chin Up"][0]
        self.assertEqual(chin[5], 0)

    def test_accessory_amrap_last_set(self):  # IL-30, A-3
        last = [r for r in self.data if r[0] == 1 and r[2] == "Lateral Raise"]
        self.assertEqual(len(last), 2)
        self.assertEqual(last[1][3:8], [1, "15+", None, "0-1", "AMRAP Last Set"])

    def test_superset_tempo_and_unit_tokens(self):  # IL-14 (4) (5) (8), IL-16, IL-28
        by_name = {r[2]: r for r in self.data if r[0] == 1}
        self.assertEqual(by_name["Chin Up"][7], "Superset A1")
        self.assertEqual(by_name["Push Up"][7], "Superset A2")
        self.assertEqual(by_name["Goblet Squat"][7], "Tempo 3-1-1")
        self.assertEqual(by_name["Plank"][7], "Reps in seconds")
        self.assertEqual(by_name["Plank"][4], "30")

    def test_reason_takes_the_cue_slot(self):  # IL-14 (10), VO-1, A-8
        knee = [r for r in self.data if r[0] == 1 and r[2] == "Hanging Knee Raise"][0]
        self.assertEqual(knee[7], "In place of sit-ups, easier on your lower back")

    def test_deload_week(self):  # IL-15, L-7, IL-17, IL-28
        deload = [r for r in self.data if r[0] == 4]
        self.assertTrue(deload)
        self.assertTrue(all(r[7].startswith("Deload week") for r in deload))
        self.assertFalse(any(r[2] in fx.TMS_531 for r in deload))  # warm-up only: no main-lift rows
        self.assertEqual(deload[0][7], "Deload week · Day: Squat · Warm-up: Squat bar x20, 50x5, 60x5, 72.5x3")
        self.assertEqual(sorted({r[1] for r in deload}), ["Day 1", "Day 2", "Day 3", "Day 4"])

    def test_notes_order_and_separator(self):  # IL-14
        w = model.Week(week=4, deload=True, optional=True)
        d = model.Day(day=1, label="MD+2", extras=["Then: tempo runs", "Warm-up: Limber 11"])
        r = model.Row(exercise="Squat", role="backdown", sets=3, reps="5", rir="3-5", load=100,
                      basis="85% of top set", rest="Rest 2 min", superset="A1", tempo="3-1-1",
                      warmup="bar x20, 40x5", cue="Brace")
        self.assertEqual(
            io.notes_for(self.program, w, d, r, True, True),
            "Deload week · Optional this week · Day: MD+2 · Warm-up: Limber 11 · Then: tempo runs · "
            "Back Down · Superset A1 · Tempo 3-1-1 · Rest 2 min · 85% of top set · Warm-up bar x20, 40x5")

    def test_cue_dropped_first_over_20_words(self):  # IL-14 applying VO-1
        w, d = model.Week(week=1), model.Day(day=1, label="Squat")
        r = model.Row(exercise="Squat", role="main", sets=1, reps="5", rir="3-5", load=80, basis="65% TM",
                      rest="Rest 3 min", warmup="Warm-up bar x20, 50x5, 60x5, 72.5x3",
                      cue="Keep the bar over your midfoot; it keeps the lift in your legs")
        self.assertEqual(io.notes_for(self.program, w, d, r, True, True),
                         "Day: Squat · Rest 3 min · 65% TM · Warm-up bar x20, 50x5, 60x5, 72.5x3")
        # a short cue fits and stays
        r.cue = "Brace hard"
        self.assertTrue(io.notes_for(self.program, w, d, r, True, True).endswith(" · Brace hard"))
        # a reason (A-8) is never dropped
        r.cue, r.reason = None, "Box squat instead, easier on the knee you flagged in training"
        self.assertTrue(io.notes_for(self.program, w, d, r, True, True).endswith("flagged in training"))

    def test_topset_encoding(self):  # CT-PLM-20, IL-18
        data = io.import_rows(fx.program_topset_prep())[1:]
        self.assertEqual(data[0][2:8], ["Squat", 1, "3", 155, "2-3", "Day: Squat · Top set 155-165 · Rest 3-5 min"])
        self.assertEqual(data[1][2:8], ["Squat", 3, "4", 142.5, "2-3", "Back Down · Rest 3 min · 88% of top set"])
        bench = [r for r in data if r[2] == "Bench Press"][0]
        self.assertEqual((bench[5], bench[7]), (107.5, "Day: Bench · Top set 107.5-112.5 · Rest 3-5 min"))

    def test_extras_only_day_takes_no_day_number(self):  # IL-28, IL-6
        data = io.import_rows(fx.program_conditioning())[1:]
        self.assertEqual({r[1] for r in data}, {"Day 1", "Day 2"})
        first_d2 = [r for r in data if r[0] == 1 and r[1] == "Day 2"][0]
        self.assertTrue(first_d2[7].startswith("Then: tempo runs · "))
        self.assertFalse(any("Sprints" in (r[7] or "") for r in data))  # hand-over only

    def test_optional_week(self):  # IL-29
        data = io.import_rows(fx.program_conditioning())[1:]
        wk2 = [r for r in data if r[0] == 2]
        self.assertTrue(wk2 and all(r[7].startswith("Optional this week") for r in wk2))
        self.assertEqual(wk2[0][7].split(" · ")[:3], ["Optional this week", "Day: MD+2", "Warm-up: Limber 11"])

    def test_distance_work(self):  # IL-28
        data = io.import_rows(fx.program_conditioning())[1:]
        walk = [r for r in data if r[2] == "Farmer's Walk"][0]
        self.assertEqual((walk[4], walk[5], walk[6], walk[7]), ("40", None, "2", "Reps in metres"))

    def test_per_set_lists(self):  # IL-10, IL-9, IL-12
        p = fx.program_531_4day()
        r = p.weeks[0].days[1].rows[0]
        r.sets, r.reps, r.rir, r.load = 3, "5, 3, 1", "3, 3, 2", [57.5, 65.0, 72.5]
        data = io.import_rows(p)[1:]
        row = [x for x in data if x[1] == "Day 2"][0]
        self.assertEqual(row[3:7], [3, "5, 3, 1", "57.5, 65, 72.5", "3, 3, 2"])
        self.assertNotIn("IL-10", {c.rule for c in fails(io.checks(p, fx.profile()))})

    def test_opener_rows_held_back(self):  # CT-PLM-20
        p = fx.program_topset_prep()
        p.weeks[3].days[0].rows.insert(0, model.Row(exercise="Squat", role="single", sets=1, reps="1",
                                                    rir="1", load="OPENER"))
        self.assertEqual(len(io.import_rows(p)), len(io.import_rows(fx.program_topset_prep())))
        checks = io.checks(p, fx.profile())
        self.assertIn("warn", statuses(checks, "CT-PLM-20"))
        self.assertEqual(fails(checks), [])


# --- the writer and reader -----------------------------------------------------------------

class TestRoundTrip(TmpDir):
    def setUp(self):
        super().setUp()
        self.program = fx.program_531_4day()
        self.path = io.write_import(self.program, self.tmp)

    def test_file_name_and_columns(self):  # IL-2, IL-1, IL-26
        self.assertEqual(Path(self.path).name, "IronLedger Block 1.csv")
        rows = self.raw(self.path)
        self.assertEqual(rows[0], list(io.HEADER))
        self.assertEqual({len(r) for r in rows}, {8})
        self.assertNotIn('""', Path(self.path).read_text(encoding="utf-8"))

    def test_cell_types(self):  # F-3, IL-9, IL-12, IL-14
        rows = self.raw(self.path)[1:]
        self.assertEqual(len(rows), 106)
        blank_loads = 0
        for row in rows:
            week, day, ex, sets, reps, load, rir, notes = row
            self.assertRegex(week, r"^[1-9]\d*$")
            self.assertRegex(sets, r"^[1-9]\d*$")
            self.assertRegex(day, r"^Day [1-9]\d*$")
            self.assertTrue(ex and reps and rir)
            if load == "":
                blank_loads += 1
            else:
                self.assertRegex(load, r"^\d+(\.\d+)?(, \d+(\.\d+)?)*$")
            self.assertNotIn("\n", notes)
        self.assertGreater(blank_loads, 0)

    def test_range_stays_text(self):  # F-3: "8-12" and "1-2" never become dates
        read = io.read_import(self.path)
        reps = {r[4] for r in read[1:]}
        rirs = {r[6] for r in read[1:]}
        self.assertIn("10-12", reps)
        self.assertIn("2-3", rirs)
        self.assertTrue(all(isinstance(v, str) for v in reps | rirs))

    def test_read_back_equals_rows(self):  # IL-24 (Python side)
        self.assertEqual([pad(r) for r in io.read_import(self.path)], io.import_rows(self.program))

    def test_checks_pass_before_and_after_writing(self):
        before = io.checks(self.program, self.profile)
        after = io.checks(self.program, self.profile, csv_path=self.path)
        self.assertEqual(fails(before), [])
        self.assertEqual(fails(after), [])
        self.assertEqual(statuses(after, "IL-11"), {"pass"})
        # file-only rules appear only when there is a file
        for rule in ("IL-1", "IL-24", "IL-26"):
            self.assertEqual(statuses(before, rule), set(), rule)
            self.assertEqual(statuses(after, rule), {"pass"}, rule)
        for rule in ("IL-3", "IL-5", "IL-6", "IL-8", "IL-9", "IL-10", "IL-12", "IL-13", "IL-14",
                     "IL-30", "F-3", "F-8", "F-10", "LB-1"):
            self.assertEqual(statuses(after, rule), {"pass"}, rule)

    def test_every_fixture_passes(self):
        for build in (fx.program_topset_prep, fx.program_two_day, fx.program_conditioning):
            p = build()
            path = io.write_import(p, self.tmp / build.__name__)
            self.assertEqual(fails(io.checks(p, self.profile, csv_path=path)), [], build.__name__)

    def test_read_import_keeps_blank_rows(self):
        # blank rows are kept as [], trailing empties dropped, Week, Sets and Load read as numbers
        rows = self.raw(self.path)
        rows.insert(2, [])
        with open(self.path, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh, lineterminator="\n").writerows(rows)
        read = io.read_import(self.path)
        self.assertEqual(read[2], [])
        self.assertIsInstance(read[1][0], int)
        self.assertIsInstance(read[1][4], str)


# --- defect fixtures that must fail their rule -------------------------------------------------

class TestDefects(TmpDir):
    def setUp(self):
        super().setUp()
        self.program = fx.program_531_4day()

    def program_fails(self, rule, program=None):
        checks = io.checks(program or self.program, self.profile)
        self.assertIn("fail", statuses(checks, rule), f"{rule} did not fail")
        return checks

    def file_fails(self, rule, program=None, **cells):
        program = program or self.program
        path = io.write_import(program, self.tmp)
        if cells:
            self.edit(path, **cells)
        checks = io.checks(program, self.profile, csv_path=path)
        self.assertIn("fail", statuses(checks, rule), f"{rule} did not fail")
        return checks

    # loads: the format is ours, plate-loadability is lib.loads' (F-5)
    def test_2kg_barbell_set_is_a_numeric_cell(self):
        first_row(self.program, lambda r: r.role == "main").load = 2
        checks = io.checks(self.program, self.profile)
        self.assertEqual(io.import_rows(self.program)[1][5], 2)
        self.assertEqual(statuses(checks, "IL-10"), {"pass"})
        self.assertEqual(statuses(checks, "F-5"), set())  # loads.checks owns F-5

    def test_66_and_99_are_numeric_cells(self):
        mains = rows_where(self.program, lambda r: r.role == "main")
        mains[0].load, mains[1].load = 66, 99
        path = io.write_import(self.program, self.tmp)
        rows = io.read_import(path)
        self.assertEqual((rows[1][5], rows[2][5]), (66, 99))
        checks = io.checks(self.program, self.profile, csv_path=path)
        self.assertEqual(statuses(checks, "IL-10"), {"pass"})
        self.assertEqual(statuses(checks, "F-5"), set())  # loads.checks owns F-5

    def test_reps_10_to_12(self):  # IL-9, F-3
        first_row(self.program, lambda r: r.reps == "10-12").reps = "10 to 12"
        checks = self.program_fails("IL-9")
        self.assertIn("fail", statuses(checks, "F-3"))

    def test_reps_en_dash(self):  # IL-9, F-3
        first_row(self.program, lambda r: r.reps == "10-12").reps = "10–12"
        checks = self.program_fails("IL-9")
        self.assertIn("fail", statuses(checks, "F-3"))

    def test_load_percent(self):  # IL-10
        first_row(self.program, lambda r: r.role == "main").load = "75%"
        self.program_fails("IL-10")
        self.file_fails("IL-10")

    def test_load_range(self):  # IL-10
        first_row(self.program, lambda r: r.role == "main").load = "170-180"
        self.program_fails("IL-10")

    def test_rir_blank(self):  # IL-12, F-8
        first_row(self.program, lambda r: r.role == "accessory").rir = ""
        checks = self.program_fails("IL-12")
        self.assertIn("fail", statuses(checks, "F-8"))

    def test_rir_negative(self):  # IL-12, F-8
        first_row(self.program, lambda r: r.role == "accessory").rir = "-1"
        checks = self.program_fails("IL-12")
        self.assertIn("fail", statuses(checks, "F-8"))

    def test_reps_stored_as_a_date(self):  # IL-9, F-3
        ref = self.ref_of(self.program, io.REPS, lambda r: r.reps == "10-12")
        checks = self.file_fails("IL-9", **{ref: "12-Aug"})   # what a spreadsheet re-save writes
        self.assertIn("12-Aug", " ".join(c.detail for c in checks if c.rule == "IL-9"))

    def test_rir_stored_as_a_date(self):  # IL-12
        ref = self.ref_of(self.program, io.RIR, lambda r: r.rir == "2-3")
        self.file_fails("IL-12", **{ref: "1-Feb"})

    def test_week_text(self):  # IL-5
        self.program.weeks[0].week = "Week 1"
        self.program_fails("IL-5")
        self.file_fails("IL-5", program=fx.program_531_4day(), A2="Week 1")

    def test_week_decimal(self):  # IL-5
        self.file_fails("IL-5", A2=2.5)

    def test_day_with_name(self):  # IL-6
        self.file_fails("IL-6", B2="Day 1 - Squat")

    def test_uneven_days(self):  # IL-6
        del self.program.weeks[1].days[3]
        self.program_fails("IL-6")

    def test_plural_exercise(self):  # LB-1
        first_row(self.program, lambda r: r.exercise == "Chin Up").exercise = "Pull-Ups"
        self.program_fails("LB-1")

    def test_parenthetical_exercise(self):  # LB-1, LB-5
        first_row(self.program, lambda r: r.role == "main").exercise = "Squat (Top Set)"
        self.program_fails("LB-1")

    def test_notes_line_break(self):  # IL-14
        first_row(self.program, lambda r: r.role == "accessory").cue = "Brace hard\nthen drive up"
        self.program_fails("IL-14")
        self.file_fails("IL-14", program=fx.program_531_4day(), H3="Rest 3 min\n75% TM")

    def test_notes_double_quote(self):  # IL-14
        first_row(self.program, lambda r: r.role == "accessory").cue = 'Say "brace" and go'
        self.program_fails("IL-14")

    def test_header_changed(self):  # IL-3
        self.file_fails("IL-3", F1="Weight")

    def test_rest_column(self):  # IL-13, IL-1
        checks = self.file_fails("IL-13", I1="Rest", I2="90")
        self.assertIn("fail", statuses(checks, "IL-1"))

    def test_renamed_file(self):  # IL-2
        path = Path(io.write_import(self.program, self.tmp))
        renamed = path.with_name("IronLedger Block 1 (1).csv")
        path.rename(renamed)
        self.assertIn("fail", statuses(io.checks(self.program, self.profile, csv_path=renamed), "IL-2"))

    def test_xlsx_refused(self):  # IL-26
        other = self.tmp / "IronLedger Block 1.xlsx"
        other.write_text("Week,Day\n")
        self.assertIn("fail", statuses(io.checks(self.program, self.profile, csv_path=other), "IL-26"))

    def test_edited_file_drifts_from_draft(self):  # IL-24
        checks = self.file_fails("IL-24", F2=82.5)
        self.assertEqual(statuses(checks, "IL-10"), {"pass"})

    def test_error_cell(self):  # F-8
        path = io.write_import(self.program, self.tmp)
        self.edit(path, F2="#REF!")
        checks = io.checks(self.program, self.profile, csv_path=path)
        self.assertIn("fail", statuses(checks, "F-8"))


# --- the export (EX rules) -----------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
