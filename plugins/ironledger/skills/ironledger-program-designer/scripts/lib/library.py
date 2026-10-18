"""Exercise library lookups (ironledger-import.md LB rules).

The library is IronLedger's own list, pinned in assets/exercise-library.json.
Names the designer may emit are library names exactly, plus the approved
aliases in assets/exercise-aliases.json (LB-9). Nothing else passes.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"
FREE_WEIGHT = {"barbell", "dumbbell", "ez_bar", "kettlebell"}


@lru_cache(maxsize=1)
def _library() -> dict[str, dict]:
    entries = json.loads((ASSETS / "exercise-library.json").read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for e in entries:
        out.setdefault(e["name"], e)  # the library carries one duplicate name; first wins
    return out


@lru_cache(maxsize=1)
def _aliases() -> dict[str, dict]:
    """Approved custom names -> {muscleGroups, equipment, isCompound, category, note}.

    An alias is a name IronLedger will create as a custom exercise (it has no
    muscle groups inside the app), so the designer carries its metadata here.
    """
    path = ASSETS / "exercise-aliases.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {a["name"]: a for a in data.get("aliases", []) if a.get("approved")}


def known(name: str) -> bool:
    return name in _library() or name in _aliases()


def is_library_name(name: str) -> bool:
    return name in _library()


def entry(name: str) -> Optional[dict]:
    return _library().get(name) or _aliases().get(name)


def muscles(name: str) -> list[str]:
    """Muscle groups; index 0 is the primary (LB rules: muscleGroups[0])."""
    e = entry(name)
    return list(e.get("muscleGroups", [])) if e else []


def primary_muscle(name: str) -> Optional[str]:
    m = muscles(name)
    return m[0] if m else None


def is_compound(name: str) -> bool:
    e = entry(name)
    return bool(e and e.get("isCompound"))


def equipment(name: str) -> list[str]:
    e = entry(name)
    return list(e.get("equipment", [])) if e else []


def is_free_weight(name: str) -> bool:
    e = entry(name)
    if not e:
        return False
    return e.get("category") in FREE_WEIGHT or bool(FREE_WEIGHT & set(e.get("equipment", [])))


def is_barbell(name: str) -> bool:
    e = entry(name)
    return bool(e and (e.get("category") == "barbell" or "barbell" in e.get("equipment", [])))


def names() -> list[str]:
    return sorted(set(_library()) | set(_aliases()))


# --- Names people write, and substitutions ------------------------------------
#
# assets/exercise-synonyms.json maps names as people commonly write them to exact
# library names; assets/substitutions.json groups library and alias names into
# movement patterns. Nothing here guesses: normalize() matches exactly, through
# the synonym table, or ignoring case and punctuation the way IronLedger does
# (LB-1). The Dice matcher below is only a port for checks (LB-2, LB-9).

ALWAYS_AVAILABLE = frozenset({"bodyweight", "none"})
_SET_LABEL = re.compile(
    r"^(?P<base>.+?)\s*\((?:top set|warm[- ]?up|back[- ]?offs?|back[- ]?downs?|amrap(?: last set)?|deload)\)\s*$",
    re.IGNORECASE,
)


def _key(name: str) -> str:
    """IronLedger's normalizeExerciseName (LB-1): lowercase, every run of
    non-alphanumerics becomes one space."""
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _read(filename: str, default: dict) -> dict:
    path = ASSETS / filename
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _all_aliases() -> dict[str, dict]:
    """Every alias, approved or not. Only _aliases() (approved) may be emitted."""
    return {a["name"]: a for a in _read("exercise-aliases.json", {}).get("aliases", [])}


@lru_cache(maxsize=1)
def _synonym_doc() -> dict:
    return _read("exercise-synonyms.json", {"synonyms": {}, "unmapped": {}})


@lru_cache(maxsize=1)
def _subs() -> dict:
    return _read("substitutions.json", {"patterns": {}})


@lru_cache(maxsize=1)
def _emit_index() -> dict[str, str]:
    """Normalised key -> an emit-able name (library or approved alias). Library
    spellings win, then approved aliases and their also_written, then synonyms."""
    idx: dict[str, str] = {}
    for n in _library():
        idx.setdefault(_key(n), n)
    for n, a in _aliases().items():
        idx.setdefault(_key(n), n)
        for w in a.get("also_written", []):
            idx.setdefault(_key(w), n)
    for s, t in _synonym_doc().get("synonyms", {}).items():
        if t in _library():
            idx.setdefault(_key(s), t)
    return idx


@lru_cache(maxsize=1)
def _any_index() -> dict[str, str]:
    """_emit_index plus aliases that aren't approved (metadata only)."""
    idx = dict(_emit_index())
    for n, a in _all_aliases().items():
        idx.setdefault(_key(n), n)
        for w in a.get("also_written", []):
            idx.setdefault(_key(w), n)
    return idx


@lru_cache(maxsize=1)
def _options() -> dict[str, tuple[str, dict]]:
    """Option name -> (pattern, entry), in substitutions.json order."""
    out: dict[str, tuple[str, dict]] = {}
    for p, spec in _subs().get("patterns", {}).items():
        for o in spec.get("options", []):
            out.setdefault(o["name"], (p, o))
    return out


def clear_caches() -> None:
    """Re-read every asset on next use (tests, or after an alias is approved)."""
    for f in (_library, _aliases, _all_aliases, _synonym_doc, _subs, _emit_index, _any_index, _options):
        f.cache_clear()


def _emittable(name: str) -> bool:
    return name in _library() or name in _aliases()


def normalize(name: str) -> tuple[Optional[str], str]:
    """Map a name as someone writes it to the name the designer may emit.

    Returns (name, how). how is "exact" when the input already is a library
    name or an approved alias (LB-9), "synonym" when it maps through
    exercise-synonyms.json, an approved alias's also_written, a difference of
    case or punctuation only (IronLedger's own equality, LB-1) or a set label in
    brackets such as "Squat (Top Set)" (the label goes in Notes: IL-18), and
    "unknown" otherwise, with None. Never fuzzy: an unknown name stays unknown.
    An alias that isn't approved is unknown here; see alias_status().
    """
    if not isinstance(name, str) or not name.strip():
        return None, "unknown"
    if name in _library() or name in _aliases():
        return name, "exact"
    s = " ".join(name.split())
    if _emittable(s):
        return s, "synonym"
    syn = _synonym_doc().get("synonyms", {})
    if s in syn and syn[s] in _library():
        return syn[s], "synonym"
    hit = _emit_index().get(_key(s))
    if hit:
        return hit, "synonym"
    m = _SET_LABEL.match(s)
    if m:
        target, _ = normalize(m.group("base"))
        if target:
            return target, "synonym"
    return None, "unknown"


def _resolve_any(name: str) -> Optional[str]:
    """Like normalize(), but also finds aliases awaiting approval."""
    if not isinstance(name, str) or not name.strip():
        return None
    target, _ = normalize(name)
    if target:
        return target
    s = " ".join(name.split())
    if s in _all_aliases():
        return s
    hit = _any_index().get(_key(s))
    if hit:
        return hit
    m = _SET_LABEL.match(s)
    return _resolve_any(m.group("base")) if m else None


def alias_status(name: str) -> Optional[str]:
    """"approved" or "pending" when the name (or a spelling of it) is in the
    alias table, else None."""
    n = _resolve_any(name)
    a = _all_aliases().get(n) if n else None
    if not a:
        return None
    return "approved" if a.get("approved") else "pending"


def unmapped(name: str) -> Optional[dict]:
    """Why a name is deliberately not mapped: {"reason", "candidates"}."""
    table = _synonym_doc().get("unmapped", {})
    if not isinstance(name, str):
        return None
    if name in table:
        return dict(table[name])
    k = _key(name)
    for n, v in table.items():
        if _key(n) == k:
            return dict(v)
    return None


def patterns() -> list[str]:
    return list(_subs().get("patterns", {}))


def option(name: str) -> Optional[dict]:
    """The substitution entry for a name: equipment, level, joint_tags (tag ->
    sourced reason, for the A-8 Notes reason), competition_variant_of, note."""
    n = _resolve_any(name)
    hit = _options().get(n) if n else None
    return dict(hit[1], pattern=hit[0]) if hit else None


def pattern_of(name: str) -> Optional[str]:
    """The movement pattern a library name, alias or synonym belongs to."""
    n = _resolve_any(name)
    if not n:
        return None
    if n in _options():
        return _options()[n][0]
    a = _all_aliases().get(n)
    return a.get("pattern") if a else None


def _same_lift(name: str) -> set[str]:
    """The name plus every library spelling of the same lift (LB-6)."""
    opts = _options()
    parent = opts[name][1].get("lineage_alias_of") if name in opts else None
    parent = parent or name
    return {name, parent} | {m for m, (_, o) in opts.items() if o.get("lineage_alias_of") == parent}


def _pattern_key(text: str, *, loose: bool) -> Optional[str]:
    """Exact key or pattern_aliases entry; with loose, also ignoring case and
    punctuation ("knee-flexion" is "knee flexion")."""
    pats = _subs().get("patterns", {})
    aliases = _subs().get("pattern_aliases", {})
    if text in pats:
        return text
    if aliases.get(text) in pats:
        return aliases[text]
    if loose:
        k = _key(text)
        for p in pats:
            if _key(p) == k:
                return p
        for a, p in aliases.items():
            if _key(a) == k and p in pats:
                return p
    return None


def pattern_key(text: str) -> Optional[str]:
    """The substitutions.json pattern key for a pattern name as a template or
    someone writes it ("hip-hinge", "Knee Flexion"), or None."""
    return _pattern_key(text, loose=True) if isinstance(text, str) else None


def _banned(items: Iterable[str]) -> tuple[set[str], set[str]]:
    """Names and pattern keys to leave out. An exercise name wins over a
    pattern key that differs only in case ("Squat" is the lift, "squat" the
    pattern)."""
    names: set[str] = set()
    pats: set[str] = set()
    for it in items:
        if not isinstance(it, str) or not it.strip():
            continue
        p = _pattern_key(it, loose=False)
        if p:
            pats.add(p)
            continue
        n = _resolve_any(it)
        if n:
            names |= _same_lift(n)
            continue
        p = _pattern_key(it, loose=True)
        if p:
            pats.add(p)
        else:
            names.add(" ".join(it.split()))
    return names, pats


def substitutes(pattern_or_name: str, *, equipment: Optional[Iterable[str]] = None,
                avoid: Iterable[str] = (), dislikes: Iterable[str] = (),
                joint_tags: Iterable[str] = (), include_unapproved: bool = False) -> list[str]:
    """Allowed options for a pattern (e.g. "hinge") or for an exercise's pattern.

    In substitutions.json order, then the pattern's fallback pattern (its
    reason is in the JSON). Leaves out: the exercise itself and its other
    library spelling (LB-6); anything in avoid or dislikes (exercise names in
    any form normalize() or the alias table knows, or pattern keys; A-8,
    G-15); options needing equipment outside `equipment` (None means no
    filter; bodyweight and none are always available); options lacking any of
    `joint_tags`; and aliases that aren't approved, unless include_unapproved.
    A lowercase pattern key is read as the pattern, a library name as the
    exercise: "squat" versus "Squat".
    """
    pats = _subs().get("patterns", {})
    if not isinstance(pattern_or_name, str):
        return []
    pattern = _pattern_key(pattern_or_name, loose=False)
    exclude: set[str] = set()
    if not pattern:
        n = _resolve_any(pattern_or_name)
        if n and pattern_of(n) in pats:
            pattern, exclude = pattern_of(n), _same_lift(n)
    if not pattern:
        pattern = _pattern_key(pattern_or_name, loose=True)
    if not pattern:
        return []
    banned_names, banned_patterns = _banned(list(avoid) + list(dislikes))
    have = None if equipment is None else set(equipment) | ALWAYS_AVAILABLE
    tags = set(joint_tags)
    chain = [pattern]
    fallback = pats[pattern].get("fallback")
    if fallback in pats and fallback != pattern:
        chain.append(fallback)
    out: list[str] = []
    for p in chain:
        if p in banned_patterns:
            continue
        for o in pats[p].get("options", []):
            n = o["name"]
            if o.get("lineage_alias_of") or n in exclude or n in banned_names or n in out:
                continue
            if not include_unapproved and not _emittable(n):
                continue
            if have is not None and not set(o.get("equipment", [])) <= have:
                continue
            if tags and not tags <= set(o.get("joint_tags", {})):
                continue
            out.append(n)
    return out


def close_variants(lift: str, *, include_unapproved: bool = False) -> list[str]:
    """Close variants of a competition lift (CT-PLO-1, M26, CT-PLO-15), in
    substitutions.json order: pause, tempo, SSB, box, close-grip, Larsen,
    deficit, block pull and so on. Given a variant, returns its siblings and
    then the competition lift itself. Any other lift gives []."""
    n = _resolve_any(lift)
    if not n:
        return []
    opts = _options()
    comps = set(_subs().get("competition_lifts", []))
    entry_ = opts[n][1] if n in opts else {}
    base = entry_.get("lineage_alias_of") or n
    comp = base if base in comps else entry_.get("competition_variant_of")
    if comp not in comps:
        return []
    same = _same_lift(comp) | _same_lift(n)
    out = [m for m, (_, o) in opts.items()
           if o.get("competition_variant_of") == comp and m not in same
           and (include_unapproved or _emittable(m))]
    if n not in _same_lift(comp):
        out.append(comp)
    return out


# --- IronLedger's fuzzy matcher, ported for checks only (LB-2, LB-9) --------

def _singular(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if token.endswith("ss"):
        return token
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def ironledger_similarity(a: str, b: str) -> float:
    """matchExercise.ts nameSimilarity: Dice over singularised, de-duplicated
    tokens. 0.8 or more raises an import-blocking match (LB-2)."""
    left = list(dict.fromkeys(_singular(t) for t in _key(a).split(" ") if t))
    right = set(_singular(t) for t in _key(b).split(" ") if t)
    if not left or not right:
        return 0.0
    shared = sum(1 for t in left if t in right)
    return 2 * shared / (len(left) + len(right))


def ironledger_best_match(name: str, known: Optional[Iterable[str]] = None) -> Optional[tuple[str, float]]:
    """matchExercise.ts bestMatch against the library (or `known`): the
    closest name scoring 0.8 or more, ties to the shorter then alphabetical
    name; None when nothing is that close (a silent custom exercise, LB-4)."""
    pool = list(_library()) if known is None else list(known)
    hits = [(k, ironledger_similarity(name, k)) for k in pool]
    hits = [h for h in hits if h[1] >= 0.8]
    if not hits:
        return None
    hits.sort(key=lambda h: (-h[1], len(h[0]), h[0]))
    return hits[0]
