#!/usr/bin/env python3
"""IronLedger program designer command line. Every number a draft shows comes from here (G-6).

  designer.py loads e1rm --weight 100 --reps 5 [--unit kg] [--microplates]
  designer.py loads wave --tm 107.5 --week 1 [--unit kg]
  designer.py loads warmup --tm 107.5 [--unit kg]
  designer.py loads next-tm --lift Squat --tm 107.5 --amraps AMRAPS.json [--prior 118,120]
  designer.py normalize "Incline Dumbbell Press"
  designer.py subs PATTERN_OR_NAME [--profile PROFILE.json] [--tags knee-friendly]
  designer.py draft TEMPLATE PROFILE.json BENCHMARKS.json [--choices C.json] [--days N] [--phase prep2|peak] --block N --out PROGRAM.json
  designer.py draft TEMPLATE PROFILE.json BENCHMARKS.json [--choices C.json] [--days N] --two-blocks --block N --out DIR
  designer.py preflight PROGRAM.json PROFILE.json [--csv FILE] [--json]
  designer.py build PROGRAM.json --out DIR
  designer.py volume PROGRAM.json

Exit codes: 0 ok, 1 pre-flight failed or draft refused, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import draft, ironledger_io, library, loads, model, preflight, volume  # noqa: E402


def _step(args) -> float:
    return loads.step_for(args.unit, getattr(args, "microplates", False))


def cmd_loads(args) -> int:
    step = _step(args)
    if args.what == "e1rm":
        e = loads.e1rm(args.weight, args.reps, step)
        out = {"inputs": {"weight": args.weight, "reps": args.reps, "unit": args.unit, "step": step},
               "e1rm": e,
               "tm_90": loads.training_max(e, 0.90, step),
               "tm_85": loads.training_max(e, 0.85, step),
               "app_e1rm": loads.e1rm_parity(args.weight, args.reps)}
    elif args.what == "wave":
        out = {"inputs": {"tm": args.tm, "week": args.week, "unit": args.unit, "step": step},
               "sets": [{"pct": p, "reps": r, "load": l} for p, r, l in loads.wave531(args.tm, args.week, step)]}
    elif args.what == "warmup":
        out = {"inputs": {"tm": args.tm, "unit": args.unit, "step": step},
               "sets": [{"set": s, "reps": r, "load": l} for s, r, l in loads.warmup531(args.tm, step, args.unit)],
               "note": loads.warmup_note(args.tm, step, args.unit)}
    elif args.what == "next-tm":
        amraps = json.loads(Path(args.amraps).read_text(encoding="utf-8"))
        prior = [float(x) for x in (args.prior or "").split(",") if x.strip()]
        new_tm, reason = loads.next_tm(args.tm, args.lift, amraps, args.unit, prior_e1rms=prior)
        out = {"inputs": {"lift": args.lift, "tm": args.tm, "unit": args.unit, "amraps": amraps, "prior_e1rms": prior},
               "next_tm": new_tm, "reason": reason}
    else:
        print(f"unknown loads subcommand {args.what}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


def _load(path, kind):
    obj = model.load_json(path)
    if not isinstance(obj, kind):
        raise SystemExit(f"{path} is not a {kind.__name__} document")
    return obj


def cmd_normalize(args) -> int:
    name, how = library.normalize(args.name)
    print(json.dumps({"input": args.name, "name": name, "how": how,
                      "pattern": library.pattern_of(name) if name else None}, indent=2))
    return 0 if name else 1


def cmd_subs(args) -> int:
    prof = _load(args.profile, model.Profile) if args.profile else None
    opts = library.substitutes(
        args.pattern,
        equipment=(prof.equipment or None) if prof else None,
        avoid=prof.avoid if prof else (),
        dislikes=prof.dislikes if prof else (),
        joint_tags=[t for t in (args.tags or "").split(",") if t.strip()],
        include_unapproved=False)
    print(json.dumps({"pattern": library.pattern_of(args.pattern) or args.pattern, "options": opts}, indent=2))
    return 0 if opts else 1


def cmd_draft(args) -> int:
    prof = _load(args.profile, model.Profile)
    benchmarks = json.loads(Path(args.benchmarks).read_text(encoding="utf-8"))
    choices = json.loads(Path(args.choices).read_text(encoding="utf-8")) if args.choices else None
    if args.two_blocks:
        return _draft_two_blocks(args, prof, benchmarks, choices)
    try:
        program, notes = draft.generate(args.template, prof, benchmarks, block=args.block,
                                        choices=choices, days=args.days, phase=args.phase)
    except draft.DraftError as e:
        print(f"draft refused: {e}", file=sys.stderr)
        return 1
    model.dump_json(program, args.out)
    print(json.dumps({"program": args.out, "notes": notes}, indent=2))
    return 0


def _draft_two_blocks(args, prof, benchmarks, choices) -> int:
    """OO-1: both blocks at once, into DIR/Block N/ and DIR/Block N+1/."""
    if args.phase:
        print("draft refused: OO-2: a two-block program has no topset-backdown phases", file=sys.stderr)
        return 1
    try:
        a, b, notes = draft.generate_one_off(args.template, prof, benchmarks, block=args.block,
                                             choices=choices, days=args.days)
    except draft.DraftError as e:
        print(f"draft refused: {e}", file=sys.stderr)
        return 1
    paths = []
    for program in (a, b):
        folder = Path(args.out) / f"Block {program.block}"
        folder.mkdir(parents=True, exist_ok=True)
        paths.append(str(folder / "program.json"))
        model.dump_json(program, paths[-1])
    print(json.dumps({"programs": paths, "notes": notes}, indent=2))
    return 0


def cmd_build(args) -> int:
    program = _load(args.program, model.Program)
    path = ironledger_io.write_import(program, args.out)
    print(path)
    return 0


def cmd_preflight(args) -> int:
    program = _load(args.program, model.Program)
    profile = _load(args.profile, model.Profile)
    report = preflight.run(program, profile, csv_path=args.csv)
    print(preflight.main_json(report) if args.json else report.render())
    return 1 if report.failed else 0


def cmd_volume(args) -> int:
    program = _load(args.program, model.Program)
    print(volume.table(program))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="designer.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("loads", help="load maths with inputs shown")
    pl.add_argument("what", choices=["e1rm", "wave", "warmup", "next-tm"])
    pl.add_argument("--lift")
    pl.add_argument("--amraps", help="JSON list of AMRAP sets: [{weight, reps, min_reps, rpe?, form_ok?}]")
    pl.add_argument("--prior", help="comma-separated earlier programming e1RMs (L-11)")
    pl.add_argument("--weight", type=float)
    pl.add_argument("--reps", type=int)
    pl.add_argument("--tm", type=float)
    pl.add_argument("--week", type=int)
    pl.add_argument("--unit", default="kg", choices=["kg", "lb"])
    pl.add_argument("--microplates", action="store_true")
    pl.set_defaults(fn=cmd_loads)

    pn = sub.add_parser("normalize", help="map an exercise name to the IronLedger library name")
    pn.add_argument("name")
    pn.set_defaults(fn=cmd_normalize)

    ps = sub.add_parser("subs", help="allowed substitutes for a pattern or exercise")
    ps.add_argument("pattern")
    ps.add_argument("--profile")
    ps.add_argument("--tags", help="comma-separated joint tags, e.g. knee-friendly")
    ps.set_defaults(fn=cmd_subs)

    pd = sub.add_parser("draft", help="generate a whole block from a template")
    pd.add_argument("template")
    pd.add_argument("profile")
    pd.add_argument("benchmarks")
    pd.add_argument("--choices")
    pd.add_argument("--days", type=int)
    pd.add_argument("--phase", choices=["prep2", "peak"])
    pd.add_argument("--block", type=int, required=True)
    pd.add_argument("--two-blocks", dest="two_blocks", action="store_true",
                    help="an 8-week program: blocks N and N+1 together, written into --out DIR (OO-1)")
    pd.add_argument("--out", required=True, help="PROGRAM.json, or with --two-blocks a folder")
    pd.set_defaults(fn=cmd_draft)

    pb = sub.add_parser("build", help="write the IronLedger import file")
    pb.add_argument("program")
    pb.add_argument("--out", default=".")
    pb.set_defaults(fn=cmd_build)

    pp = sub.add_parser("preflight", help="run every rule check")
    pp.add_argument("program")
    pp.add_argument("profile")
    pp.add_argument("--csv", help="also check the written import file")
    pp.add_argument("--json", action="store_true")
    pp.set_defaults(fn=cmd_preflight)

    pv = sub.add_parser("volume", help="weekly fractional hard sets per muscle")
    pv.add_argument("program")
    pv.set_defaults(fn=cmd_volume)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except (ValueError, KeyError) as e:
        print(f"designer.py: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
