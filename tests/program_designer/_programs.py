"""Synthetic programs and profiles for tests. Every number is invented.

build_531() makes a clean 4-week 531-4day block the way the skill should:
every number from lib.loads, exact library names, IL-30 RIR ranges on
percentage rows, IL-17 warm-up notes, FSL supplemental work, double-
progression accessories with lifter-chosen (blank) loads, an accessory AMRAP
row, and an L-7 deload week. Tests mutate copies of it to make defects.
"""
from __future__ import annotations

import copy

from tests.program_designer import _path  # noqa: F401
from lib import loads, model

LIFTS = ["Squat", "Bench Press", "Deadlift", "Overhead Press"]
E1RMS = {"Squat": 117.5, "Bench Press": 90.0, "Deadlift": 150.0, "Overhead Press": 60.0}

ACCESSORIES = {
    "Squat": [("Bulgarian Split Squat", 3, "10-12", "2"), ("Leg Curl", 3, "10-12", "2"),
              ("Hanging Leg Raise", 3, "12-15", "2")],
    "Bench Press": [("Dumbbell Bench Press", 3, "10-12", "2"), ("Dumbbell Row", 3, "10-12", "2"),
                    ("Lateral Raise", 3, "12-15", "2")],
    "Deadlift": [("Romanian Deadlift", 3, "8-10", "2"), ("Leg Press", 3, "10-12", "2"),
                 ("Ab Wheel Rollout", 3, "10-12", "2")],
    # A-2: OHP day = incline DB press + row + core, which also gives chest its
    # second weekly session (P-7: over 10 sets a week needs 2 sessions).
    "Overhead Press": [("Dumbbell Incline Press", 3, "10-12", "2"), ("Seated Cable Row", 3, "10-12", "2"),
                       ("Cable Crunch", 3, "12-15", "2")],
}
AMRAP_ACCESSORY = {"Bench Press": "Cable Tricep Pushdown", "Overhead Press": "Rope Pushdown"}


def _tms(step=2.5):
    return {lift: loads.training_max(e, 0.90, step) for lift, e in E1RMS.items()}


def build_531(client="Sample lifter", block=1, unit="kg") -> model.Program:
    step = loads.step_for(unit)
    tms = _tms(step)
    weeks = []
    for wk in (1, 2, 3, 4):
        deload = wk == 4
        days = []
        for i, lift in enumerate(LIFTS, start=1):
            rows: list[model.Row] = []
            tm = tms[lift]
            extras = []
            if not deload:
                wave = loads.wave531(tm, wk, step)
                for n, (pct, reps, load) in enumerate(wave):
                    amrap = n == len(wave) - 1
                    rows.append(model.Row(
                        exercise=lift, role="main_amrap" if amrap else "main", sets=1, reps=reps,
                        rir="1-2" if amrap else "3-5", load=load, basis=f"{round(pct * 100)}% TM",
                        rest="Rest 3 min", warmup=loads.warmup_note(tm, step, unit) if n == 0 else None,
                        cue=("as many strong reps as you can, leaving 1 to 2 in the tank" if amrap else None),
                        progression="tm_wave"))
                pct, reps, load, sets = loads.fsl(tm, wk, step, sets=5)
                rows.append(model.Row(exercise=lift, role="supplemental", sets=sets, reps=reps, rir="3-5",
                                      load=load, basis=f"FSL {round(pct * 100)}% TM", rest="Rest 2 min",
                                      progression="tm_wave"))
            else:
                extras.append("Warm-up: " + loads.warmup_note(tm, step, unit))
            for name, sets, reps, rir in ACCESSORIES[lift]:
                if deload:
                    sets, rir = loads.deload_accessory(sets, rir)
                rows.append(model.Row(exercise=name, role="accessory", sets=sets, reps=reps, rir=rir,
                                      load=None, progression="double"))
            if lift in AMRAP_ACCESSORY and not deload:
                rows.append(model.Row(exercise=AMRAP_ACCESSORY[lift], role="accessory_amrap", sets=1,
                                      reps="12+", rir="0-1", load=None, cue="AMRAP Last Set",
                                      progression="double"))
            days.append(model.Day(day=i, label=lift, rows=rows, extras=extras))
        weeks.append(model.Week(week=wk, deload=deload, days=days))
    return model.Program(client=client, block=block, unit=unit, template="531-4day",
                         primary_type="GEN", tms=tms, e1rms=dict(E1RMS),
                         decisions_relied_on=["M3", "M4", "M5", "M6", "M7", "M8", "M9", "M11"],
                         weeks=weeks)


def profile(client="Sample lifter", **over) -> model.Profile:
    p = model.Profile(client=client, unit="kg", training_status="intermediate",
                      days=4, session_min=75,
                      equipment=["barbell", "rack", "bench", "dumbbell", "cable", "machine"],
                      primary_type="GEN", age_band="adult", screen_cleared=True)
    for k, v in over.items():
        setattr(p, k, v)
    return p


def clone(p: model.Program) -> model.Program:
    return copy.deepcopy(p)
