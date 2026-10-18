"""The program designer's program and profile models.

A program is a logical prescription: weeks, days and rows, with each row
saying what the lifter does and why (role, load basis). How that maps onto
IronLedger's import columns is ironledger_io's job (ironledger-import.md).
Everything here is plain data so it round-trips through JSON between the
skill's steps.

Shapes (schema tags are checked on load):

  designer-profile/1  what pre-flight needs to know about the lifter
  designer-program/1  the draft itself
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Union

PROGRAM_SCHEMA = "designer-program/1"
PROFILE_SCHEMA = "designer-profile/1"

# Row roles. The writer and the checks branch on these, never on names.
ROLES = (
    "main",            # a 5/3/1 work set that is not the AMRAP (L-5)
    "main_amrap",      # the last 5/3/1 work set, "5+" / "3+" / "1+" (L-5, L-13)
    "topset",          # topset-backdown template: the top set (CT-PLM)
    "backdown",        # back-down after a top set (CT-PLM-4)
    "supplemental",    # FSL / BBB after the main sets (L-14)
    "accessory",       # accessory, double progression (A-1, A-6)
    "accessory_amrap", # an accessory "AMRAP Last Set" row (A-3, IL-30)
    "single",          # a scripted single, e.g. PEAK or the CT-PLM-2 5/3/1 peak
    "benchmark",       # a W-1 / W-5 benchmark set
)

Load = Union[float, int, None, list]  # None only under IL-11; list = per-set loads


@dataclass
class Row:
    exercise: str                 # exact library or alias name (LB rules)
    role: str                     # one of ROLES
    sets: int
    reps: str                     # "5", "8-12", "5+", "5, 3, 1" (IL-9)
    rir: str                      # "2", "1-2", "3-5", "2, 2, 1" (IL-12)
    load: Load = None             # in the profile unit; None only for a lifter-chosen accessory load
    basis: Optional[str] = None   # IL-14 load basis: "65% TM", "88% of top set", "Top set 175-185"
    rest: Optional[str] = None    # an IL-14 token: "Rest 2 min", "Rest 3 min", "Rest 3-5 min", "Rest 90 s"
    superset: Optional[str] = None  # "A1", "A2", ...
    tempo: Optional[str] = None     # "3-1-1"
    warmup: Optional[str] = None    # IL-17 compact warm-up, first work row of a main lift only
    cue: Optional[str] = None       # at most one cue (VO rules)
    reason: Optional[str] = None    # compulsory when the choice was made for an injury or dislike (A-8)
    progression: Optional[str] = None  # P-13: "linear", "double", "tm_wave", "rpe_topset"


@dataclass
class Day:
    day: int                      # 1..n within the week (IL "Day N")
    label: Optional[str] = None   # "Squat", "Upper A"; goes to Notes as "Day: <label>"
    rows: list[Row] = field(default_factory=list)
    extras: list[str] = field(default_factory=list)  # IL-28: warm-up blocks, runs, conditioning (listed in the hand-over)


@dataclass
class Week:
    week: int
    deload: bool = False
    optional: bool = False        # IL-29: a rugby bye week keeps its rows marked optional
    days: list[Day] = field(default_factory=list)


@dataclass
class Program:
    client: str                   # a short label for the lifter or program; lineage is the block number
    block: int                    # IronLedger Block <N> (IL-2)
    unit: str = "kg"              # "kg" | "lb" (F-10, F-11)
    template: Optional[str] = None
    primary_type: Optional[str] = None      # CT-SEL-1: PLO, PLM, RGO, ...
    modifiers: list[str] = field(default_factory=list)
    priority_muscles: list[str] = field(default_factory=list)    # CT-HYP-4 / P-3: muscles held to the 10 to 20 band
    tms: dict[str, float] = field(default_factory=dict)          # lift -> training max
    e1rms: dict[str, float] = field(default_factory=dict)        # lift -> e1RM used
    decisions_relied_on: list[str] = field(default_factory=list)  # unconfirmed M-decisions (F-9)
    departures: list[dict] = field(default_factory=list)          # [{"rule": "P-3", "reason": "..."}] (G-7)
    weeks: list[Week] = field(default_factory=list)
    # A one-off program (OO-1): {"part": 1 or 2, "of": 2, "blocks": [N, N+1]}; part 2 adds
    # "self_check": {lift: {"tm_block1", "increment", "amraps": [{"week", "min_reps", "load"}]}} (OO-4).
    one_off: Optional[dict] = None
    client_name: Optional[str] = None       # optional lifter name; never in the import
    schema: str = PROGRAM_SCHEMA

    # --- iteration helpers -------------------------------------------------
    def rows(self):
        """Yield (week, day, row) for every row."""
        for w in self.weeks:
            for d in w.days:
                for r in d.rows:
                    yield w, d, r


@dataclass
class Profile:
    client: str
    name: Optional[str] = None               # the lifter's name, optional
    unit: str = "kg"
    microplates: bool = False                # L-4: allows a 1.25 kg (2.5 lb) step
    training_status: Optional[str] = None    # novice | intermediate | advanced (P-1)
    days: Optional[int] = None               # available training days (CT-SEL-7)
    session_min: Optional[int] = None
    equipment: list[str] = field(default_factory=list)   # library equipment vocabulary
    dislikes: list[str] = field(default_factory=list)    # exercise names (A-8)
    avoid: list[str] = field(default_factory=list)       # exercises ruled out by injury or clinician (G-15)
    primary_type: Optional[str] = None
    modifiers: list[str] = field(default_factory=list)
    age_band: Optional[str] = None           # adult | junior (a junior is refused, CT-JUN-1)
    screen_cleared: bool = False             # G-4: no to all six APSS Stage 1 questions, or a health professional's go-ahead
    flags: list[str] = field(default_factory=list)       # conditions the rules act on, e.g. pregnancy, osteoporosis
    goal: Optional[str] = None               # the lifter's goal in their words
    target_date: Optional[str] = None        # next competition or target date, YYYY-MM-DD
    schema: str = PROFILE_SCHEMA


# --- JSON round-trip ---------------------------------------------------------

def _row(d: dict) -> Row:
    return Row(**d)


def program_from_dict(d: dict[str, Any]) -> Program:
    if d.get("schema") != PROGRAM_SCHEMA:
        raise ValueError(f"not a {PROGRAM_SCHEMA} document (schema={d.get('schema')!r})")
    weeks = [
        Week(
            week=w["week"],
            deload=w.get("deload", False),
            optional=w.get("optional", False),
            days=[Day(day=dy["day"], label=dy.get("label"), extras=dy.get("extras", []),
                      rows=[_row(r) for r in dy.get("rows", [])]) for dy in w.get("days", [])],
        )
        for w in d.get("weeks", [])
    ]
    fields = {k: v for k, v in d.items() if k != "weeks"}
    return Program(weeks=weeks, **fields)


def profile_from_dict(d: dict[str, Any]) -> Profile:
    if d.get("schema") != PROFILE_SCHEMA:
        raise ValueError(f"not a {PROFILE_SCHEMA} document (schema={d.get('schema')!r})")
    known = set(Profile.__dataclass_fields__)
    unknown = sorted(set(d) - known)
    if unknown:
        raise ValueError(f"profile has unknown fields: {', '.join(unknown)} (known: {', '.join(sorted(known))})")
    return Profile(**d)


def to_dict(obj) -> dict:
    return asdict(obj)


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("schema") == PROGRAM_SCHEMA:
        return program_from_dict(d)
    if d.get("schema") == PROFILE_SCHEMA:
        return profile_from_dict(d)
    raise ValueError(f"{path}: unknown schema {d.get('schema')!r}")


def dump_json(obj, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_dict(obj), f, indent=2, ensure_ascii=False)
        f.write("\n")
