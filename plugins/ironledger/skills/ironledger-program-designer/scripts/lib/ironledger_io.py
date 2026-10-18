"""IronLedger files: the import file the lifter loads into the IronLedger app.

Implements references/ironledger-import.md (IL and LB rules) plus rulebook
F-3, F-8 and F-10. The contract file wins over anything here; each decision
below cites the rule that makes it.

  import_rows(program)          header + cells, in IL order
  notes_for(...)                one Notes cell, IL-14 tokens in IL-14 order
  write_import(program, dir)    "IronLedger Block <N>.csv", UTF-8 CSV (IL-1, IL-26)
  read_import(path)             rows as written, numbers back as numbers
  checks(program, profile, csv_path=None)

How a logical model.Row maps onto the import (the writer's conventions):

  * One model row is one import row. 5/3/1 work sets are rows with Sets 1, the
    AMRAP is its own row (IL-9), FSL is one row of N sets.
  * `load` None leaves Load blank, which only a lifter-chosen accessory may do
    (IL-11). A list is a per-set load list (IL-10). A string "OPENER" or
    "SECOND" holds the row back from the import until the lifter fills it
    (CT-PLM-20).
  * A top set's range comes from `load` as a (low, high) pair, or from `basis`
    "Top set <low>-<high>"; Load is the low bound (CT-PLM-20).
  * `basis` is the IL-14 load-basis segment ("85% TM", "88% of top set"). A
    `Reps in seconds` or `Reps in metres` token in it moves to its own segment.
  * `Day.extras` are IL-28 work that is never a row. "Warm-up: <block>" stays a
    warm-up segment; anything else becomes "Then: <session>". A day holding
    only extras takes no Day number.
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from lib import library, model
from lib.checks import Check, where

# --- the import file's fixed shape -------------------------------------------

HEADER = ("Week", "Day", "Exercise", "Sets", "Reps", "Load", "RIR", "Notes")  # IL-3
FILE_TEMPLATE = "IronLedger Block {block}.csv"                             # IL-2
COLS = "ABCDEFGH"
WEEK, DAY, EXERCISE, SETS, REPS, LOAD, RIR, NOTES = range(8)
TEXT_COLS = (REPS, RIR, NOTES)       # always text: 8-12 or 1-2 must never become a date (F-3, IL-9, IL-12)
NUMBER_COLS = (WEEK, SETS, LOAD)     # read back as numbers when they parse as one
SEP = " · "                          # IL-14: the parser's own separator (programImport.ts:602-604)

CLIENT_CHOSEN = ("accessory", "accessory_amrap")   # IL-11: the only rows whose Load may be blank
PERCENT_ROLES = ("main", "supplemental", "backdown")  # IL-30: non-AMRAP percentage rows
PERCENT_RIR = "3-5"                  # IL-30 default cap, a range the logger won't auto-write
AMRAP_RIR = "1-2"                    # IL-30: the 5/3/1 AMRAP row
LAST_SET_RIR = "0-1"                 # IL-30, A-3: an accessory AMRAP Last Set row
UNIT_TOKENS = ("Reps in seconds", "Reps in metres")  # IL-28, IL-14 segment 8
HELD_BACK = ("OPENER", "SECOND")     # CT-PLM-20: stay out of the import until the lifter fills them
NOTE_WORD_CAP = 20                   # VO-1, applied by IL-14
REST_ALIASES = ("rest", "rest time", "rest (s)", "rest sec", "rest seconds")  # IL-4, IL-13
MAX_REPORTED = 10                    # fails listed per rule before "and N more"

_REPS_RE = re.compile(r"^([1-9]\d*)(?:-([1-9]\d*)|(\+))?$")               # IL-9: 5, 8-12, 5+
_INT_LIST_RE = re.compile(r"^\d+(?:\s*,\s*\d+)+$")                          # IL-9, IL-12: 5, 3, 1
_RIR_RE = re.compile(r"^(\d+)(?:-(\d+))?$")                                 # IL-12: 2, 1-2
_NUM_LIST_RE = re.compile(r"^\d+(?:\.\d+)?(?:\s*,\s*\d+(?:\.\d+)?)+$")      # IL-10: 95, 97.5, 100
_TOPSET_RE = re.compile(r"^Top set (\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$")       # CT-PLM-20
_DAY_RE = re.compile(r"^Day ([1-9]\d*)$")                                   # IL-6


# --- small value helpers -------------------------------------------------------

def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _num(v):
    """A whole float becomes an int so the cell reads 65, never 65.0."""
    if isinstance(v, float) and math.isfinite(v) and v.is_integer():
        return int(v)
    return v


def _num_text(v) -> str:
    """The number as JavaScript's String() prints it: 65, 97.5, 101.25."""
    return str(_num(float(v)))


def _text(v):
    """Reps and RIR are text (IL-9, IL-12). A whole number from the builder is written as its text."""
    if isinstance(v, int) and not isinstance(v, bool):
        return str(v)
    return v


def _words(text: str) -> int:
    return sum(1 for t in text.split() if t != "·")


def _sort_key(v):
    return (0, float(v), "") if _is_num(v) else (1, 0.0, str(v))


def _is_whole(v) -> bool:
    return _is_num(v) and float(v).is_integer()


def _ref(col: int, row: int) -> str:
    return f"cell {chr(ord('A') + col)}{row}"


# --- the import plan -----------------------------------------------------------

@dataclass
class _Entry:
    """One import row: where it came from and its place in the day."""
    week: model.Week
    day: model.Day
    row: model.Row
    day_n: int            # the import's Day number (IL-6, IL-28)
    first_of_day: bool
    first_of_lift: bool

    def where(self) -> str:
        return where(self.week.week, self.day.day, self.row.exercise)


def _held_back(row: model.Row) -> bool:
    return isinstance(row.load, str) and row.load.strip().upper() in HELD_BACK


def _plan(program: model.Program) -> list[_Entry]:
    """Every row that becomes an import row, sorted by Week, then Day, then row order (IL-6)."""
    out: list[_Entry] = []
    for w in sorted(program.weeks, key=lambda w: _sort_key(w.week)):
        day_n = 0
        for d in sorted(w.days, key=lambda d: _sort_key(d.day)):
            rows = [r for r in d.rows if not _held_back(r)]  # CT-PLM-20: OPENER and SECOND wait for the lifter
            if not rows:
                continue  # IL-28: a day of only warm-up blocks or conditioning takes no Day number
            day_n += 1    # IL-6: Day n restarts at 1 each week and runs without gaps
            seen: set[str] = set()
            for i, r in enumerate(rows):
                out.append(_Entry(w, d, r, day_n, i == 0, r.exercise not in seen))
                seen.add(r.exercise)
    return out


def _topset_range(row: model.Row):
    """(low, high) of a top set, from a (low, high) load pair or a "Top set 175-185" basis (CT-PLM-20)."""
    if isinstance(row.load, (list, tuple)) and len(row.load) == 2 and all(_is_num(v) for v in row.load):
        return float(row.load[0]), float(row.load[1])
    if row.basis:
        for token in row.basis.split(SEP):
            m = _TOPSET_RE.match(token.strip())
            if m:
                return float(m.group(1)), float(m.group(2))
    return None


def _load_cell(row: model.Row):
    """Load: a number, a per-set text list, or blank (IL-10, IL-11, CT-PLM-20)."""
    if row.role == "topset":
        rng = _topset_range(row)
        if rng:
            return _num(rng[0])  # CT-PLM-20: a top set's import Load is the lower bound of its range
    load = row.load
    if load is None:
        return None              # IL-11: blank, the lifter chooses (checks() allows it on accessories only)
    if isinstance(load, (list, tuple)):
        if len(load) == 1:
            return _num(load[0])
        if all(_is_num(v) for v in load):
            return ", ".join(_num_text(v) for v in load)  # IL-10: one entry per set, as text
        return ", ".join(str(v) for v in load)            # malformed; written as is so IL-10 fails
    return _num(load)            # IL-10: a numeric cell; a string such as "75%" is written as is and fails IL-10


# --- Notes (IL-14) ---------------------------------------------------------------

def _extras(extras) -> tuple[list[str], list[str]]:
    """IL-28 extras as IL-14 segment-2 tokens: warm-up blocks first, then the rest of the session."""
    warm, then = [], []
    for x in extras or []:
        x = (x or "").strip()
        if not x:
            continue
        if x.startswith("Warm-up:"):
            warm.append(x)                                     # `Warm-up: Limber 11`
        else:
            body = x[len("Then:"):].strip() if x.startswith("Then:") else x
            then.append(f"Then: {body}")                       # `Then: 6 x 400 m`
    return warm, then


def _label(row: model.Row) -> Optional[str]:
    """IL-14 segment 3, the row label."""
    if row.role == "main_amrap":
        return "AMRAP"
    if row.role == "accessory_amrap":
        return "AMRAP Last Set"                                # IL-30, A-3
    if row.role == "topset":
        rng = _topset_range(row)
        return f"Top set {_num_text(rng[0])}-{_num_text(rng[1])}" if rng else "Top set"  # CT-PLM-20
    if row.role == "backdown":
        return "Back Down"
    return None


def _basis(row: model.Row) -> tuple[list[str], list[str]]:
    """IL-14 segments 7 (load basis) and 8 (the unit of timed or distance work, IL-28)."""
    basis, units = [], []
    for token in (row.basis or "").split(SEP):
        token = token.strip()
        if not token:
            continue
        if token in UNIT_TOKENS:
            units.append(token)
        elif row.role == "topset" and _TOPSET_RE.match(token):
            continue                                           # already the segment-3 label
        else:
            basis.append(token)
    return basis, units


def notes_for(program: model.Program, week: model.Week, day: model.Day, row: model.Row,
              first_of_day: bool, first_of_lift: bool) -> str:
    """One Notes cell: IL-14's segments in IL-14's order, joined by " · ", empty ones left out.

    The text is written verbatim. A line break or a double quote in it is not
    cleaned up here; checks() fails it under IL-14 so the draft gets fixed.
    """
    logistics: list[str] = []
    # (1) week marker on every row of the week: IL-15 deload, IL-29 optional (bye) week
    if week.deload:
        logistics.append("Deload week")
    if week.optional:
        logistics.append("Optional this week")
    # (2) first row of the day: the day's name (IL-6 drops the label), then IL-28's warm-up and after-session work
    if first_of_day:
        if day.label:
            logistics.append(f"Day: {day.label}")
        warm, then = _extras(day.extras)
        logistics += warm + then
    # (3) row label: AMRAP, AMRAP Last Set (IL-30), Top set <range> (CT-PLM-20), Back Down
    label = _label(row)
    if label:
        logistics.append(label)
    # (4) superset pair
    if row.superset:
        s = row.superset.strip()
        logistics.append(s if s.startswith("Superset") else f"Superset {s}")
    # (5) tempo or Full ROM
    if row.tempo:
        t = row.tempo.strip()
        logistics.append(f"Tempo {t}" if t[:1].isdigit() else t)
    # (6) rest (IL-13: never a column)
    if row.rest:
        logistics.append(row.rest.strip())
    # (7) load basis, (8) unit of timed or distance work
    basis, units = _basis(row)
    logistics += basis + units
    # (9) IL-17: the main-lift warm-up, one compact segment on the lift's first work row, never rows
    if first_of_lift and row.warmup:
        w = row.warmup.strip()
        logistics.append(w if w.startswith("Warm-up") else f"Warm-up {w}")
    # (10) one cue or reason (VO-1). A-8 and VO-4 make a reason compulsory, so it takes the slot and
    # is never dropped; a cue is dropped first when the cell passes VO-1's 20 words (IL-14).
    segs = list(logistics)
    if row.reason:
        segs.append(row.reason.strip())
    elif row.cue:
        with_cue = segs + [row.cue.strip()]
        if _words(SEP.join(with_cue)) <= NOTE_WORD_CAP:
            segs = with_cue
    return SEP.join(segs)


# --- import rows, writer and reader -------------------------------------------------

def import_rows(program: model.Program) -> list[list]:
    """The import sheet as a list of rows: the exact IL-3 header, then one row per import row.

    Cells: Week an int (IL-5), Day "Day N" (IL-6), Exercise the exact name
    (IL-7), Sets an int (IL-8), Reps text (IL-9), Load a number, a text list or
    None (IL-10, IL-11), RIR text (IL-12), Notes text or None (IL-14). A value
    the program gets wrong is written as it is, so checks() can fail it.
    """
    out: list[list] = [list(HEADER)]
    for e in _plan(program):
        r = e.row
        notes = notes_for(program, e.week, e.day, r, e.first_of_day, e.first_of_lift)
        out.append([
            _num(e.week.week),        # IL-5: a whole number, never "Week 1"
            f"Day {e.day_n}",         # IL-6: exactly "Day <n>"; the day's name goes to Notes
            r.exercise,               # IL-7, LB-1: the exact library or approved alias name
            _num(r.sets),             # IL-8: a whole number, AMRAP lives in Reps
            _text(r.reps),            # IL-9
            _load_cell(r),            # IL-10, IL-11, CT-PLM-20
            _text(r.rir),             # IL-12, IL-30
            notes or None,            # IL-14
        ])
    return out


def _csv_cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        return _num_text(v)
    return str(v)


def write_import(program: model.Program, out_dir) -> str:
    """Write `IronLedger Block <N>.csv` (IL-2): UTF-8, one header row, then the rows. Returns its path.

    CSV, so the IronLedger program file checker can read exactly the file the
    lifter imports (IL-26). No cell holds a double quote or a line break
    (IL-14), so quoting only ever wraps a cell that contains a comma.
    """
    rows = import_rows(program)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / FILE_TEMPLATE.format(block=program.block)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        for values in rows:
            w.writerow([_csv_cell(v) for v in values])
    return str(path)


def _read_number(text: str):
    try:
        f = float(text)
    except ValueError:
        return text
    if math.isfinite(f) and re.fullmatch(r"-?\d+(?:\.\d+)?", text.strip()):
        return _num(f)
    return text


def read_import(path) -> list[list]:
    """The file's rows: text stays text, Week, Sets and a single Load come back as numbers,
    empty cells are None, trailing empty cells are dropped and blank rows are kept as []."""
    rows: list[list] = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for cells in csv.reader(fh):
            vals = []
            for c_i, c in enumerate(cells):
                if c == "":
                    vals.append(None)
                elif c_i in NUMBER_COLS:
                    vals.append(_read_number(c))
                else:
                    vals.append(c)
            while vals and vals[-1] is None:
                vals.pop()
            rows.append(vals)
    while rows and not rows[-1]:
        rows.pop()
    return rows


@dataclass
class _Facts:
    max_column: int
    rows: list[list]
    raw: str                           # the file's text, for IL-26's doubled-quote check
    errors: list[str]                  # "F2 #REF!": spreadsheet error values pasted into the file (F-8)


def _read_facts(path) -> _Facts:
    raw = Path(path).read_text(encoding="utf-8-sig")
    rows = read_import(path)
    errors = [f"{_ref(c, r)} {v}" for r, cells in enumerate(rows, start=1) for c, v in enumerate(cells)
              if isinstance(v, str) and v.strip().startswith("#") and v.strip().rstrip("!?").lstrip("#").isupper()]
    return _Facts(max((len(r) for r in rows), default=0), rows, raw, errors)


# --- checks ----------------------------------------------------------------------------

class _Found:
    """Problems per rule, reported once per rule: its fails (up to a cap), else one pass."""

    def __init__(self):
        self.ok: dict[str, str] = {}     # rule -> pass detail, in report order
        self.problems: dict[str, list[tuple[str, Optional[str]]]] = {}

    def rule(self, rule: str, ok: str, replace: bool = False) -> None:
        if replace or not self.ok.get(rule):
            self.ok[rule] = ok

    def fail(self, rule: str, detail: str, at: Optional[str] = None) -> None:
        self.ok.setdefault(rule, "")
        self.problems.setdefault(rule, []).append((detail, at))

    def checks(self) -> list[Check]:
        out: list[Check] = []
        for rule, ok in self.ok.items():
            found = self.problems.get(rule, [])
            if not found:
                out.append(Check(rule, "pass", ok))
                continue
            out += [Check(rule, "fail", d, w) for d, w in found[:MAX_REPORTED]]
            if len(found) > MAX_REPORTED:
                out.append(Check(rule, "fail", f"and {len(found) - MAX_REPORTED} more like these"))
        return out


def _reps_problem(reps, sets) -> Optional[str]:
    """IL-9. None when the Reps value is a text cell in one of the four forms."""
    if reps is None or reps == "":
        return "Reps is blank"
    if not isinstance(reps, str):
        return f"Reps is a number or date cell ({reps!r}); write it as text"
    m = _REPS_RE.match(reps)
    if m:
        if m.group(2) and int(m.group(2)) <= int(m.group(1)):
            return f"Reps range {reps!r} doesn't rise"
        if m.group(3) and sets != 1:
            return f"AMRAP Reps {reps!r} on a row of {sets} sets; an AMRAP set is its own row with Sets 1"
        return None
    if _INT_LIST_RE.match(reps):
        n = len(reps.split(","))
        if _is_whole(sets) and n != int(sets):
            return f"Reps list {reps!r} has {n} entries for {sets} sets"
        if "0" in [x.strip() for x in reps.split(",")]:
            return f"Reps list {reps!r} has a 0"
        return None
    return f"Reps {reps!r} is not 5, 8-12, 5+ or a per-set list"


def _f3_problem(reps) -> Optional[str]:
    """F-3: a rep range is an ASCII hyphen in a text cell."""
    if reps is None or reps == "":
        return None
    if not isinstance(reps, str):
        return f"Reps is a number or date cell ({reps!r}), so a range can become a date"
    if "–" in reps or "—" in reps or "−" in reps:
        return f"Reps {reps!r} uses a dash that isn't an ASCII hyphen; IronLedger logs its first number"
    if re.search(r"\bto\b", reps, re.I):
        return f"Reps {reps!r} writes a range with 'to'; IronLedger logs its first number"
    return None


def _load_problem(load, sets) -> Optional[str]:
    """IL-10 for a non-blank Load."""
    if isinstance(load, bool):
        return f"Load is {load!r}"
    if _is_num(load):
        return None if load >= 0 else f"Load {load!r} is negative"
    if isinstance(load, str):
        s = load.strip()
        if _NUM_LIST_RE.match(s):
            n = len(s.split(","))
            if _is_whole(sets) and n != int(sets):
                return f"Load list {load!r} has {n} entries for {sets} sets"
            return None
        if re.fullmatch(r"\d+(?:\.\d+)?", s):
            return f"Load {load!r} is text; write it as a number cell"
        if "%" in s:
            why = "a percentage logs as the load on tick; write the load and put the % in Notes"
        elif re.search(r"rpe", s, re.I):
            why = "an RPE logs as the load on tick"
        elif re.search(r"\d\s*(?:kg|kgs|lb|lbs)\b", s, re.I):
            why = "a unit suffix leaves it text"
        elif re.fullmatch(r"\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?", s):
            why = "a load range logs nothing"
        else:
            why = "words log nothing"
        return f"Load {load!r}: {why}"
    return f"Load {load!r} is not a number"


def _rir_problem(rir, sets) -> Optional[str]:
    """IL-12. None when RIR is a text cell: 2, 1-2 or a per-set list."""
    if rir is None or rir == "":
        return "RIR is blank"
    if not isinstance(rir, str):
        return f"RIR is a number or date cell ({rir!r}); write it as text"
    s = rir.strip()
    if re.match(r"^[-−]\s*\d", s):
        return f"RIR {rir!r} is negative"
    m = _RIR_RE.match(s)
    if m:
        if m.group(2) is not None and int(m.group(2)) <= int(m.group(1)):
            return f"RIR range {rir!r} doesn't rise"
        return None
    if _INT_LIST_RE.match(s):
        n = len(s.split(","))
        if _is_whole(sets) and n != int(sets):
            return f"RIR list {rir!r} has {n} entries for {sets} sets"
        return None
    return f"RIR {rir!r} is not 2, 1-2 or a per-set list"


def _cell_checks(rows: list[list], plan: list[_Entry], f: "_Found", errors=()) -> None:
    """IL-3 to IL-15, IL-29, IL-30, VO-1, F-3, F-8 and LB-1 on a sheet's cells (the file's, or import_rows')."""
    cell = lambda cells, i: cells[i] if i < len(cells) else None  # noqa: E731
    header = rows[0] if rows else []
    data = [(n, cells) for n, cells in enumerate(rows[1:], start=2)
            if any(v is not None and v != "" for v in cells)]
    n_rows = len(data)
    f.rule("IL-3", "header is exactly Week | Day | Exercise | Sets | Reps | Load | RIR | Notes")
    f.rule("IL-5", "every Week is a whole number from 1 to the block's week count")
    f.rule("IL-6", "every Day is 'Day n', rows sorted, the same days every week")
    f.rule("LB-1", "every Exercise is a library name or approved alias, spelt exactly")
    f.rule("IL-8", "every Sets is a whole number of 1 or more")
    f.rule("IL-9", f"every Reps is text in an IL-9 form ({n_rows} rows)")
    f.rule("F-3", "rep ranges use an ASCII hyphen in a text cell")
    f.rule("IL-10", "every Load is a number or a per-set list")
    f.rule("IL-11", "")  # its pass detail counts the blank loads, set below
    f.rule("IL-12", "every RIR is text: a whole number, a range or a per-set list")
    f.rule("IL-13", "no Rest column")
    f.rule("IL-14", "Notes are one line with no double quotes")
    f.rule("VO-1", f"every Notes cell is {NOTE_WORD_CAP} words or fewer")
    f.rule("IL-15", "deload rows lead with 'Deload week', and no other rows do")
    f.rule("IL-29", "optional-week rows lead with 'Optional this week'")
    f.rule("IL-30", "percentage rows carry an RIR range; AMRAP rows are 1 x n+ at their fixed RIR")
    f.rule("F-8", "no blank required cell, no negative RIR, no error value")

    # IL-3: row 1 is exactly the eight headers
    if [cell(header, i) for i in range(max(len(header), len(HEADER)))] != list(HEADER):
        f.fail("IL-3", f"row 1 reads {header!r}; it must be {' | '.join(HEADER)}", "row 1")
    # IL-13: no Rest column
    for i, h in enumerate(header):
        if isinstance(h, str) and h.strip().lower() in REST_ALIASES:
            f.fail("IL-13", f"a {h!r} column; rest goes in Notes", f"row 1 column {i + 1}")
    # F-8: no #REF! or other error value
    for err in errors:
        f.fail("F-8", f"error value in {err}")

    days_by_week: dict[int, list[int]] = {}
    weeks_seen: list[int] = []
    last_week = None
    blank_ok = 0

    for k, (rn, cells) in enumerate(data):
        e = plan[k] if k < len(plan) else None
        role = e.row.role if e else None
        at = lambda col: _ref(col, rn) + (f" ({e.where()})" if e else "")  # noqa: E731
        wk, dy, ex, sets, reps, load, rir, notes = (cell(cells, i) for i in range(8))

        # F-8: no blank required cell (a blank Load is IL-11's; Notes may be empty)
        for col in (WEEK, DAY, EXERCISE, SETS, REPS, RIR):
            if cell(cells, col) is None or cell(cells, col) == "":
                f.fail("F-8", f"{HEADER[col]} is blank", at(col))

        # IL-5: Week is a whole number from 1 (the upper bound is checked after the loop)
        if not (_is_whole(wk) and wk >= 1):
            f.fail("IL-5", f"Week {wk!r} is not a whole-number week", at(WEEK))
        else:
            wk = int(wk)
            if last_week is not None and wk < last_week:
                f.fail("IL-6", f"week {wk} comes after week {last_week}; sort by Week, then Day", at(WEEK))
            if wk not in weeks_seen:
                weeks_seen.append(wk)
            last_week = wk

        # IL-6: Day reads exactly "Day <n>"
        m = _DAY_RE.match(dy) if isinstance(dy, str) else None
        if not m:
            f.fail("IL-6", f"Day {dy!r} is not exactly 'Day <n>'", at(DAY))
        elif isinstance(wk, int):
            seq = days_by_week.setdefault(wk, [])
            n = int(m.group(1))
            if seq and n < seq[-1]:
                f.fail("IL-6", f"Day {n} comes after Day {seq[-1]} in week {wk}", at(DAY))
            seq.append(n)

        # LB-1 (IL-7): the exact library name, or an approved alias (LB-9)
        if not (isinstance(ex, str) and library.known(ex)):
            f.fail("LB-1", f"{ex!r} is not a library name or approved alias, spelt exactly", at(EXERCISE))

        # IL-8: Sets is a whole number, 1 or more
        if not (_is_whole(sets) and sets >= 1):
            f.fail("IL-8", f"Sets {sets!r} is not a whole number of 1 or more", at(SETS))

        # IL-9 and F-3: Reps
        p = _reps_problem(reps, sets)
        if p:
            f.fail("IL-9", p, at(REPS))
        p = _f3_problem(reps)
        if p:
            f.fail("F-3", p, at(REPS))

        # IL-10 and IL-11: Load
        if load is None or load == "":
            if role in CLIENT_CHOSEN:
                blank_ok += 1
            else:
                f.fail("IL-11", f"Load is blank on a {role or 'unknown'} row; only a lifter-chosen accessory "
                                "may leave it blank", at(LOAD))
        else:
            p = _load_problem(load, sets)
            if p:
                f.fail("IL-10", p, at(LOAD))

        # IL-12 and F-8: RIR
        p = _rir_problem(rir, sets)
        if p:
            f.fail("IL-12", p, at(RIR))
        if (isinstance(rir, str) and re.match(r"^\s*[-−]\s*\d", rir)) or (_is_num(rir) and rir < 0):
            f.fail("F-8", f"RIR {rir!r} is negative; RIR floors at 0", at(RIR))

        # IL-14: one line, no double quotes; VO-1 (applied by IL-14): 20 words or fewer
        notes_s = notes if isinstance(notes, str) else ""
        if notes is not None and notes != "":
            if not isinstance(notes, str):
                f.fail("IL-14", f"Notes {notes!r} is not text", at(NOTES))
            else:
                if "\n" in notes or "\r" in notes:
                    f.fail("IL-14", "Notes has a line break; a CSV re-save splits it into a new row", at(NOTES))
                if '"' in notes:
                    f.fail("IL-14", "Notes has a double quote; a CSV re-save strips it", at(NOTES))
                if _words(notes) > NOTE_WORD_CAP:
                    f.fail("VO-1", f"Notes is {_words(notes)} words; the cap is {NOTE_WORD_CAP}", at(NOTES))

        # IL-15 and IL-29: the week marker leads every row of that week
        if e is not None:
            marks = (["Deload week"] if e.week.deload else []) + (["Optional this week"] if e.week.optional else [])
            if marks and not notes_s.startswith(SEP.join(marks)):
                f.fail("IL-15" if e.week.deload else "IL-29",
                       f"Notes doesn't start with {SEP.join(marks)!r}", at(NOTES))
            if not e.week.deload and notes_s.startswith("Deload week"):
                f.fail("IL-15", "a 'Deload week' marker in a week that isn't a deload", at(NOTES))

        # IL-30: percentage rows carry an RIR range; AMRAP rows are single sets at their fixed RIR
        if role in PERCENT_ROLES and isinstance(rir, str) and not re.fullmatch(r"\d+-\d+", rir.strip()):
            f.fail("IL-30", f"RIR {rir!r} on a {role} row: a single number is auto-written on tick, "
                            f"so write a range (default {PERCENT_RIR})", at(RIR))
        if role in ("main_amrap", "accessory_amrap"):
            want = AMRAP_RIR if role == "main_amrap" else LAST_SET_RIR
            if sets != 1 or not (isinstance(reps, str) and re.fullmatch(r"[1-9]\d*\+", reps)) or rir != want:
                f.fail("IL-30", f"{role} row is {sets!r} x {reps!r} at RIR {rir!r}; it must be 1 x n+ at RIR {want}",
                       at(RIR))

    # IL-5: whole numbers from 1 to the block's week count
    for wk in weeks_seen:
        if wk > len(weeks_seen):
            f.fail("IL-5", f"week {wk} is past the block's {len(weeks_seen)} weeks")
    # IL-6: days 1..n in every week, and the same n every week
    counts: dict[int, int] = {}
    for wk, seq in days_by_week.items():
        distinct = sorted(set(seq))
        if distinct != list(range(1, len(distinct) + 1)):
            f.fail("IL-6", f"week {wk} has days {distinct}; they must run 1 to n with no gaps")
        counts[wk] = len(distinct)
    if len(set(counts.values())) > 1:
        f.fail("IL-6", "days per week differ: " + ", ".join(f"week {w} has {n}" for w, n in sorted(counts.items())))
    if len(set(counts.values())) == 1:
        f.rule("IL-6", f"every Day is 'Day n', rows sorted, {next(iter(counts.values()))} days in every week",
               replace=True)
    f.rule("IL-5", f"every Week is a whole number from 1 to {len(weeks_seen)}", replace=True)
    f.rule("IL-11", f"{blank_ok} blank Loads, all on lifter-chosen accessory rows (each raises IronLedger's "
                    "tolerated 'No load given')", replace=True)


def _program_checks(program: model.Program, profile, plan: list[_Entry], f: "_Found") -> list[Check]:
    """Rules only the draft can show: IL-2's block number, F-10, IL-17 and CT-PLM-20. Returns extra warnings."""
    expected = FILE_TEMPLATE.format(block=program.block)
    f.rule("IL-2", f"block {program.block}: the file is {expected!r}")
    f.rule("F-10", f"loads in {program.unit}, the profile unit")
    f.rule("IL-17", "main-lift warm-ups sit in the Notes of each lift's first work row, never as rows")

    if not (isinstance(program.block, int) and not isinstance(program.block, bool) and program.block >= 1):
        f.fail("IL-2", f"block {program.block!r} is not a whole number from 1")

    unit = getattr(profile, "unit", None)
    if program.unit not in ("kg", "lb"):
        f.fail("F-10", f"program unit {program.unit!r} is not kg or lb")
    elif unit is not None and unit != program.unit:
        f.fail("F-10", f"program is in {program.unit} but the profile says {unit}; one unit per file")

    if any(r.role == "topset" for _, _, r in program.rows()):
        f.rule("CT-PLM-20", "top sets import the low end of their range as Load, with the range in Notes")
    for e in plan:
        r = e.row
        if r.warmup and not e.first_of_lift:
            f.fail("IL-17", "warm-up on a row that isn't the lift's first work row, so it would be dropped", e.where())
        if r.role == "topset":
            rng = _topset_range(r)
            if rng is None:
                f.fail("CT-PLM-20", "top set has no range: give load (low, high) or basis 'Top set <low>-<high>'",
                       e.where())
            elif _is_num(r.load) and abs(float(r.load) - rng[0]) > 1e-9:
                f.fail("CT-PLM-20", f"top-set load {r.load} isn't the low end of its range "
                                    f"{_num_text(rng[0])}-{_num_text(rng[1])}", e.where())

    held = [(w, d, r) for w, d, r in program.rows() if _held_back(r)]
    if not held:
        return []
    w, d, r = held[0]
    return [Check("CT-PLM-20", "warn", f"{len(held)} OPENER/SECOND rows held out of the import until the lifter "
                                       "fills them (ironledger-meet-attempts); then re-issue under IL-20",
                  where(w.week, d.day, r.exercise))]


def _norm(v):
    if v is None or v == "":
        return None
    if _is_num(v):
        return float(v)
    return v


def _file_checks(program: model.Program, path: Path, facts: _Facts, f: "_Found") -> None:
    """IL-1, IL-2's file name, IL-24 and IL-26 on the written file."""
    expected = FILE_TEMPLATE.format(block=program.block)
    want = import_rows(program)[1:]
    f.rule("IL-26", f"{path.name} is a UTF-8 CSV with no double quotes inside a cell")
    f.rule("IL-1", "one header row and columns A to H only")
    f.rule("IL-24", f"every file row matches its draft row ({len(want)} rows)")

    if path.name != expected:
        f.fail("IL-2", f"file is named {path.name!r}; it must be {expected!r}", str(path))
    if facts.max_column > len(HEADER):
        f.fail("IL-1", f"the file uses {facts.max_column} columns; nothing goes past column H")
    if '""' in facts.raw:
        f.fail("IL-26", "a cell holds a double quote, which IronLedger drops")

    # IL-24 (the Python side): the file still says exactly what the draft says, e.g. after a hand edit
    got = [(n, cells) for n, cells in enumerate(facts.rows[1:], start=2)
           if any(v is not None and v != "" for v in cells)]
    if len(got) != len(want):
        f.fail("IL-24", f"the file has {len(got)} data rows; the draft has {len(want)}")
    for (rn, g), w in zip(got, want):
        for col in range(len(HEADER)):
            a = _norm(g[col] if col < len(g) else None)
            b = _norm(w[col])
            same = abs(a - b) <= 1e-9 if isinstance(a, float) and isinstance(b, float) else a == b
            if not same:
                f.fail("IL-24", f"{HEADER[col]} is {a!r} in the file and {b!r} in the draft", _ref(col, rn))


def checks(program: model.Program, profile, csv_path=None) -> list[Check]:
    """The IL rules, F-3, F-8, F-10, VO-1 and LB-1 on the draft, and on the written file when csv_path is given.

    Without a file, the cells checked are import_rows(program): what would be
    written. With one, they are the file's own cells (read_import), mapped onto
    the draft's rows by position, plus the file-only rules: IL-1, IL-2's name,
    IL-24's row-for-row match and IL-26. Each rule is reported once: its fails,
    or one pass. F-5 plate-loadability is loads' check, not repeated here.
    """
    f = _Found()
    plan = _plan(program)
    extra = _program_checks(program, profile, plan, f)
    rows, errors = None, ()
    if csv_path is not None:
        path = Path(csv_path)
        f.rule("IL-26", f"{path.name} is a UTF-8 CSV")
        if path.suffix.lower() != ".csv":
            f.fail("IL-26", f"{path.name} is not a .csv file", str(path))
        else:
            try:
                facts = _read_facts(path)
            except Exception as exc:  # missing, unreadable or not UTF-8
                f.fail("IL-26", f"cannot read {path.name} as a UTF-8 CSV: {exc}", str(path))
            else:
                _file_checks(program, path, facts, f)
                rows, errors = facts.rows, facts.errors
    if rows is None:
        rows = import_rows(program)
    _cell_checks(rows, plan, f, errors)
    return f.checks() + extra
