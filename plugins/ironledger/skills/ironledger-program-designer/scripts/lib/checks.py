"""The result type every pre-flight check returns.

A check is tied to one rule ID from references/. Status:
  pass       the rule holds
  fail       the rule is broken; the build is blocked (G-7)
  warn       worth the lifter's attention; does not block
  departure  broken, but the program records a reason for it (G-7)
  n/a        the rule does not apply to this program
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

STATUSES = ("pass", "fail", "warn", "departure", "n/a")


@dataclass
class Check:
    rule: str                    # e.g. "F-5", "IL-9", "P-7"
    status: str                  # one of STATUSES
    detail: str = ""             # one line the lifter can read
    where: Optional[str] = None  # "W2 D3 Squat row 4", "Program sheet C7"

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"bad status {self.status!r} for {self.rule}")


def where(week=None, day=None, exercise=None, index=None) -> str:
    parts = []
    if week is not None:
        parts.append(f"W{week}")
    if day is not None:
        parts.append(f"D{day}")
    if exercise:
        parts.append(exercise)
    if index is not None:
        parts.append(f"row {index}")
    return " ".join(parts)
