"""Synthetic programs for the IronLedger file tests.

"Sample lifter" is made up and every number here is invented. The small
CEILING helper below is fixture arithmetic only: drafts take their numbers
from lib.loads (G-6), which these tests deliberately don't depend on.

  program_531_4day()      block 1: 531-4day, 3 loading weeks + deload, warm-ups,
                          FSL, blank-load accessories, AMRAP Last Set, superset
  program_topset_prep()   block 2: topset-backdown PREP, 4 loading weeks + deload (CT-PLM)
  program_two_day()       block 3: two days a week, two main lifts a day, no FSL
  program_conditioning()  block 4: 531-club with IL-28 extras, a conditioning-only
                          day, a bye week (IL-29) and timed and distance work
"""
from __future__ import annotations

import math

from lib import model

CLIENT = "Sample lifter"
AMRAP_CUE = "as many strong reps as you can, leaving 1 to 2 in the tank"  # L-13
WAVE = {  # L-5
    1: [(0.65, "5"), (0.75, "5"), (0.85, "5+")],
    2: [(0.70, "3"), (0.80, "3"), (0.90, "3+")],
    3: [(0.75, "5"), (0.85, "3"), (0.95, "1+")],
}


def up(x: float, step: float = 2.5) -> float:
    """CEILING to the step (L-4), float-safe. Fixture arithmetic only."""
    return round(math.ceil(round(x / step, 9)) * step, 6)


def fmt(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(x)


def warmup(tm: float, bar: float = 20.0) -> str:
    """The IL-17 compact warm-up: bar x 20, then 40/50/60% TM x 5/5/3 (L-6); below-bar loads are the bar."""
    a, b, c = (max(bar, up(tm * p)) for p in (0.40, 0.50, 0.60))
    return f"Warm-up bar x20, {fmt(a)}x5, {fmt(b)}x5, {fmt(c)}x3"


def deload_warmup(lift: str, tm: float) -> str:
    """L-7's deload main lift is its warm-up only: an IL-28 'Warm-up:' segment, never rows (IL-17)."""
    return "Warm-up: " + lift + " " + warmup(tm)[len("Warm-up "):]


def main_rows(lift: str, tm: float, week: int, fsl: bool = True) -> list[model.Row]:
    rows = []
    for i, (pct, reps) in enumerate(WAVE[week]):
        amrap = reps.endswith("+")
        heavy = reps in ("3", "3+", "1+")
        rows.append(model.Row(
            exercise=lift, role="main_amrap" if amrap else "main", sets=1, reps=reps,
            rir="1-2" if amrap else "3-5", load=up(tm * pct), basis=f"{round(pct * 100)}% TM",
            rest="Rest 3-5 min" if heavy else "Rest 3 min", warmup=warmup(tm) if i == 0 else None,
            cue=AMRAP_CUE if amrap else None, progression="tm_wave"))
    if fsl:
        pct = WAVE[week][0][0]
        rows.append(model.Row(exercise=lift, role="supplemental", sets=5, reps="5", rir="3-5",
                              load=up(tm * pct), basis=f"{round(pct * 100)}% TM", rest="Rest 2 min",
                              progression="tm_wave"))
    return rows


def acc(name: str, sets: int, reps: str, rir: str, **kw) -> model.Row:
    return model.Row(exercise=name, role="accessory", sets=sets, reps=reps, rir=rir,
                     progression="double", **kw)


def last_set(name: str, reps: str) -> model.Row:
    """A-3, IL-30: the accessory AMRAP Last Set is its own row, Sets 1, RIR 0-1."""
    return model.Row(exercise=name, role="accessory_amrap", sets=1, reps=reps, rir="0-1",
                     progression="double")


def deload(row: model.Row) -> model.Row:
    """L-7: the same accessory with fewer sets at RIR + 1 (3 at least)."""
    bump = {"2": "3", "2-3": "3-4", "2-4": "3-5", "1-2": "3", "1": "3"}
    return model.Row(exercise=row.exercise, role=row.role, sets=max(1, row.sets - 1), reps=row.reps,
                     rir=bump[row.rir], load=row.load, basis=row.basis, superset=row.superset,
                     tempo=row.tempo, reason=row.reason, progression=row.progression)


# --- block 1: 531-4day -----------------------------------------------------------

TMS_531 = {"Squat": 120.0, "Bench Press": 85.0, "Deadlift": 150.0, "Overhead Press": 55.0}
DAYS_531 = [(1, "Squat", "Squat"), (2, "Bench", "Bench Press"), (3, "Deadlift", "Deadlift"),
            (4, "Press", "Overhead Press")]


def _accessories_531(day: int) -> list[model.Row]:
    if day == 1:
        return [acc("Bulgarian Split Squat", 3, "10-12", "2", cue="Add load when you hit 12 on every set at RIR 2"),
                acc("Leg Curl", 3, "10-12", "2-3"),
                acc("Hanging Knee Raise", 3, "12-20", "2-4", reason="In place of sit-ups, easier on your lower back")]
    if day == 2:
        return [acc("Dumbbell Row", 3, "10-12", "2"),
                acc("Lateral Raise", 2, "12-15", "2-3"),
                last_set("Lateral Raise", "15+"),
                acc("Cable Tricep Pushdown", 3, "10-12", "2-3")]
    if day == 3:
        return [acc("Seated Leg Curl", 3, "10-12", "2-3"),
                acc("Goblet Squat", 3, "10-12", "2", tempo="3-1-1"),
                acc("Plank", 3, "30", "2", load=0, basis="Reps in seconds")]
    return [acc("Dumbbell Incline Press", 3, "10-12", "2"),
            acc("Chin Up", 3, "6-10", "2", load=0, superset="A1"),
            acc("Push Up", 3, "10-15", "2", load=0, superset="A2"),
            acc("Cable Tricep Pushdown", 2, "10-12", "2-3"),
            last_set("Cable Tricep Pushdown", "12+")]


def program_531_4day() -> model.Program:
    weeks = []
    for wk in (1, 2, 3):
        days = [model.Day(day=n, label=label, rows=main_rows(lift, TMS_531[lift], wk) + _accessories_531(n))
                for n, label, lift in DAYS_531]
        weeks.append(model.Week(week=wk, days=days))
    days = [model.Day(day=n, label=label, extras=[deload_warmup(lift, TMS_531[lift])],
                      rows=[deload(r) for r in _accessories_531(n) if r.role == "accessory"])
            for n, label, lift in DAYS_531]
    weeks.append(model.Week(week=4, deload=True, days=days))
    return model.Program(client=CLIENT, block=1, unit="kg", template="531-4day", primary_type="GEN",
                         tms=dict(TMS_531), decisions_relied_on=["M2", "M3", "M4", "M5", "M13"], weeks=weeks)


# --- block 2: topset-backdown PREP (CT-PLM) --------------------------------------------

PLM_LIFTS = [  # day, label, lift, week-1 midpoint, range width (CT-PLM-1), weekly step (CT-PLM-3)
    (1, "Squat", "Squat", 160.0, 10.0, 5.0),
    (2, "Bench", "Bench Press", 110.0, 5.0, 2.5),
    (3, "Deadlift", "Deadlift", 190.0, 10.0, 5.0),
]
PLM_REPS = {1: "3", 2: "3", 3: "2", 4: "2"}
PLM_TOP_RIR = {1: "2-3", 2: "2-3", 3: "2", 4: "1-2"}      # RPE 7.5, 7.5-8, 8, 8-8.5 (CT-PLM-5, CT-PLM-20)
PLM_ACC_RIR = {1: "2", 2: "1-2", 3: "1-2", 4: "1", 5: "3"}  # CT-PLM-13 against a week-1 base of 2
PLM_ACC = {1: [("Leg Press", "8-10")], 2: [("Dumbbell Row", "8-12"), ("Lateral Raise", "12-15")],
           3: [("Leg Curl", "10-12")]}


def program_topset_prep() -> model.Program:
    weeks = []
    for wk in (1, 2, 3, 4, 5):
        days = []
        for n, label, lift, mid1, width, step in PLM_LIFTS:
            mid = mid1 + step * min(wk - 1, 3)
            lo, hi = mid - width / 2, mid + width / 2
            rows = []
            if wk < 5:
                # CT-PLM-20: the range goes in as a (low, high) pair or as a "Top set" basis
                top = (model.Row(exercise=lift, role="topset", sets=1, reps=PLM_REPS[wk], rir=PLM_TOP_RIR[wk],
                                 load=lo, basis=f"Top set {fmt(lo)}-{fmt(hi)}", rest="Rest 3-5 min",
                                 progression="rpe_topset") if lift == "Bench Press" else
                       model.Row(exercise=lift, role="topset", sets=1, reps=PLM_REPS[wk], rir=PLM_TOP_RIR[wk],
                                 load=[lo, hi], rest="Rest 3-5 min", progression="rpe_topset"))
                rows.append(top)
                rows.append(model.Row(exercise=lift, role="backdown", sets=3, reps="4", rir="2-3",
                                      load=up(mid * 0.88), basis="88% of top set", rest="Rest 3 min",
                                      progression="rpe_topset"))
            else:
                # CT-PLM-6 deload: 3 x 3 at RPE 6 to 7 (RIR 3-4), no back-downs
                rows.append(model.Row(exercise=lift, role="main", sets=3, reps="3", rir="3-4",
                                      load=up(mid * 0.75), rest="Rest 3 min", progression="rpe_topset"))
            rows += [acc(name, 2, reps, PLM_ACC_RIR[wk]) for name, reps in PLM_ACC[n]]
            days.append(model.Day(day=n, label=label, rows=rows))
        weeks.append(model.Week(week=wk, deload=(wk == 5), days=days))
    return model.Program(client=CLIENT, block=2, unit="kg", template="topset-backdown", primary_type="PLM",
                         e1rms={"Squat": 190.0, "Bench Press": 130.0, "Deadlift": 225.0},
                         decisions_relied_on=["M8", "M10"], weeks=weeks)


# --- block 3: two days a week ------------------------------------------------------------

TMS_2DAY = {"Squat": 120.0, "Bench Press": 85.0, "Deadlift": 150.0, "Overhead Press": 55.0}
DAYS_2DAY = [(1, ("Squat", "Bench Press"), "Dumbbell Row"), (2, ("Deadlift", "Overhead Press"), "Lat Pulldown")]


def program_two_day() -> model.Program:
    weeks = []
    for wk in (1, 2, 3):
        days = [model.Day(day=n, rows=[r for lift in lifts for r in main_rows(lift, TMS_2DAY[lift], wk, fsl=False)]
                          + [acc(extra, 3, "10-12", "2")])
                for n, lifts, extra in DAYS_2DAY]
        weeks.append(model.Week(week=wk, days=days))
    days = [model.Day(day=n, extras=[deload_warmup(lift, TMS_2DAY[lift]) for lift in lifts],
                      rows=[acc(extra, 2, "10-12", "3")])
            for n, lifts, extra in DAYS_2DAY]
    weeks.append(model.Week(week=4, deload=True, days=days))
    return model.Program(client=CLIENT, block=3, unit="kg", template="531-4day", primary_type="GEN",
                         tms=dict(TMS_2DAY), weeks=weeks)


# --- block 4: 531-club with IL-28 extras -------------------------------------------------

TMS_CLUB = {"Squat": 120.0, "Bench Press": 85.0}


def _club_day1(wk: int) -> model.Day:
    rows = main_rows("Squat", TMS_CLUB["Squat"], wk, fsl=False) + [
        acc("Nordic Curl", 2, "3-5", "2", load=0),
        acc("Plank", 3, "30", "2", load=0, basis="Reps in seconds")]
    return model.Day(day=1, label="MD+2", extras=["Warm-up: Limber 11"], rows=rows)


def _club_day2(wk: int) -> model.Day:
    rows = main_rows("Bench Press", TMS_CLUB["Bench Press"], wk, fsl=False) + [
        acc("Farmer's Walk", 3, "40", "2", basis="Reps in metres"),
        acc("Chin Up", 3, "5-8", "2", load=0)]
    return model.Day(day=2, extras=["Then: tempo runs"], rows=rows)


def _club_conditioning() -> model.Day:
    return model.Day(day=3, label="MD-2", extras=["Sprints 6 x 40 m"])  # IL-28: no rows, no Day number


def program_conditioning() -> model.Program:
    weeks = [model.Week(week=wk, optional=(wk == 2), days=[_club_day1(wk), _club_day2(wk), _club_conditioning()])
             for wk in (1, 2, 3)]
    d1, d2 = _club_day1(1), _club_day2(1)
    weeks.append(model.Week(week=4, deload=True, days=[
        model.Day(day=1, label="MD+2", extras=["Warm-up: Limber 11", deload_warmup("Squat", TMS_CLUB["Squat"])],
                  rows=[deload(r) for r in d1.rows if r.role == "accessory"]),
        model.Day(day=2, extras=[deload_warmup("Bench Press", TMS_CLUB["Bench Press"]), "Then: tempo runs"],
                  rows=[deload(r) for r in d2.rows if r.role == "accessory"]),
        _club_conditioning()]))
    return model.Program(client=CLIENT, block=4, unit="kg", template="531-club", primary_type="RGO",
                         tms=dict(TMS_CLUB), weeks=weeks)


def profile(unit: str = "kg") -> model.Profile:
    return model.Profile(client=CLIENT, unit=unit, training_status="intermediate", days=4,
                         screen_cleared=True)
