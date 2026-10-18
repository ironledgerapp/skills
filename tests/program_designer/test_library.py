"""Exercise names, synonyms, aliases and substitutions (LB rules,
F-7, A-8, A-9, G-15, G-20, CT-PLO-1, M26)."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.program_designer import _path  # noqa: F401
from lib import library

ASSETS = library.ASSETS
LIBRARY = {}
for _e in json.loads((ASSETS / "exercise-library.json").read_text(encoding="utf-8")):
    LIBRARY.setdefault(_e["name"], _e)
SYN_DOC = json.loads((ASSETS / "exercise-synonyms.json").read_text(encoding="utf-8"))
SYNONYMS = SYN_DOC["synonyms"]
UNMAPPED = SYN_DOC["unmapped"]
ALIAS_LIST = json.loads((ASSETS / "exercise-aliases.json").read_text(encoding="utf-8"))["aliases"]
ALIASES = {a["name"]: a for a in ALIAS_LIST}
SUBS = json.loads((ASSETS / "substitutions.json").read_text(encoding="utf-8"))
PATTERNS = SUBS["patterns"]

MUSCLES = {"abs", "back", "biceps", "calves", "chest", "forearms", "full_body", "glutes", "hamstrings",
           "lats", "lower_back", "obliques", "quadriceps", "shoulders", "traps", "triceps"}
LIB_EQUIPMENT = {t for e in LIBRARY.values() for t in e["equipment"]}
EXTENSIONS = set(SUBS["equipment_extensions"])
FULL_GYM = LIB_EQUIPMENT | EXTENSIONS
BARBELL_ONLY = ["barbell", "rack", "bench"]   # plates come with the barbell
LEVELS = {"regression", "standard", "progression"}


def options():
    for p, spec in PATTERNS.items():
        for o in spec["options"]:
            yield p, o


def primary(name):
    e = LIBRARY.get(name) or ALIASES.get(name)
    return e["muscleGroups"][0]


class Assets(unittest.TestCase):
    """Every name in the three tables resolves to the library or the alias table."""

    def test_synonym_targets_are_library_names(self):
        bad = {s: t for s, t in SYNONYMS.items() if not library.is_library_name(t)}
        self.assertEqual(bad, {})

    def test_synonym_keys_are_not_library_names(self):
        self.assertEqual([s for s in SYNONYMS if s in LIBRARY], [])

    def test_synonyms_target_the_default_spelling(self):
        # LB-6: Back Squat, Conventional Deadlift and Military Press are other keys for the same lift.
        seconds = {o["name"] for _, o in options() if o.get("lineage_alias_of")}
        self.assertEqual({s: t for s, t in SYNONYMS.items() if t in seconds}, {})

    def test_substitution_names_resolve(self):
        for p, o in options():
            with self.subTest(pattern=p, name=o["name"]):
                if o.get("alias"):
                    self.assertIn(o["name"], ALIASES)
                    self.assertFalse(library.is_library_name(o["name"]))
                else:
                    self.assertTrue(library.is_library_name(o["name"]))

    def test_no_name_in_two_patterns(self):
        seen = {}
        for p, o in options():
            self.assertNotIn(o["name"], seen, f"{o['name']} in {seen.get(o['name'])} and {p}")
            seen[o["name"]] = p

    def test_option_equipment_copies_its_source(self):
        for p, o in options():
            src = LIBRARY.get(o["name"]) or ALIASES[o["name"]]
            self.assertEqual(o["equipment"], src["equipment"], o["name"])

    def test_option_fields(self):
        comps = set(SUBS["competition_lifts"])
        for p, o in options():
            with self.subTest(name=o["name"]):
                self.assertIn(o["level"], LEVELS)
                self.assertIn(o["competition_variant_of"], comps | {None})
                self.assertNotEqual(o["competition_variant_of"], o["name"])
                for tag, reason in o["joint_tags"].items():
                    self.assertIn(tag, SUBS["joint_tags"])
                    self.assertIn("CT-PT-3", reason, "a joint tag must cite its rule")
                if o.get("lineage_alias_of"):
                    self.assertIn(o["lineage_alias_of"], LIBRARY)
                    self.assertEqual(library.pattern_of(o["lineage_alias_of"]), p)
                self.assertIn(o.get("reps_unit"), {None, "seconds", "metres"})

    def test_competition_lifts_are_in_the_table(self):
        for lift in SUBS["competition_lifts"]:
            self.assertTrue(library.is_library_name(lift))
            self.assertIsNotNone(library.pattern_of(lift))

    def test_fallbacks_exist_and_say_why(self):
        for p, spec in PATTERNS.items():
            if spec["fallback"]:
                self.assertIn(spec["fallback"], PATTERNS, p)
                self.assertTrue(spec.get("fallback_reason"), p)

    def test_aliases_are_well_formed(self):
        allowed_equipment = LIB_EQUIPMENT | EXTENSIONS | set(SUBS["always_available"])
        for a in ALIAS_LIST:
            with self.subTest(alias=a["name"]):
                self.assertFalse(library.is_library_name(a["name"]))
                self.assertTrue(a["muscleGroups"])
                self.assertLessEqual(set(a["muscleGroups"]), MUSCLES)
                self.assertLessEqual(set(a["equipment"]), allowed_equipment)
                self.assertIsInstance(a["approved"], bool)
                self.assertIsInstance(a["isCompound"], bool)
                self.assertIn(a["pattern"], PATTERNS)
                self.assertTrue(a["note"])
                self.assertEqual(library.pattern_of(a["name"]), a["pattern"])

    def test_every_alias_is_offered_somewhere(self):
        offered = {o["name"] for _, o in options() if o.get("alias")}
        self.assertEqual(set(ALIASES) - offered, set())

    def test_unmapped_candidates_resolve_and_names_stay_unknown(self):
        for name, info in UNMAPPED.items():
            with self.subTest(name=name):
                self.assertTrue(info["reason"])
                for c in info["candidates"]:
                    self.assertTrue(library.is_library_name(c) or c in ALIASES, c)
                self.assertEqual(library.normalize(name), (None, "unknown"))

    def test_one_target_per_normalised_spelling(self):
        # Library names, alias spellings and synonyms must never disagree about a spelling.
        claims = {}
        for n in LIBRARY:
            claims.setdefault(library._key(n), set()).add(n)
        for a in ALIAS_LIST:
            for w in [a["name"], *a.get("also_written", [])]:
                claims.setdefault(library._key(w), set()).add(a["name"])
        for s, t in SYNONYMS.items():
            claims.setdefault(library._key(s), set()).add(t)
        self.assertEqual({k: v for k, v in claims.items() if len(v) > 1}, {})


class MatcherPort(unittest.TestCase):
    """The Python port of matchExercise.ts reproduces LB-2 to LB-4."""

    def test_blocking_matches(self):
        for name, expected, score in [
            ("Leg Curls", "Leg Curl", 1.0),
            ("Incline Dumbbell Press", "Dumbbell Incline Press", 1.0),
            ("Hamstring Curl Machine", "Machine Curl", 0.8),
            ("Pause Bench Press", "Bench Press", 0.8),
            ("Weighted Pull Up", "Pull Up", 0.8),
            ("Weighted Chin-up", "Chin Up", 0.8),
            ("Barbell Bench Press", "Bench Press", 0.8),
            ("Tricep Pushdown", "Cable Tricep Pushdown", 0.8),
        ]:
            with self.subTest(name=name):
                hit = library.ironledger_best_match(name)
                self.assertIsNotNone(hit)
                self.assertEqual(hit[0], expected)
                self.assertAlmostEqual(hit[1], score)

    def test_silent_custom_names(self):
        for name in ["Pull-Ups", "Pull Ups", "Pullups", "Chin-Ups", "RDL", "OHP", "DB Row",
                     "Seated Hamstring Curl", "Adductor Machine", "Cable Y-Raise", "Tibialis Raise",
                     "Pause Deadlift", "Squat (Top Set)"]:
            self.assertIsNone(library.ironledger_best_match(name), name)


class AliasesImportCleanly(unittest.TestCase):
    """LB-9: an alias must score under 0.8 against every library name, or it blocks import.
    Aliases must also stay under 0.8 against each other, because an imported alias joins the
    client's custom list and a later file is matched against it (LB-4)."""

    def test_under_threshold_against_the_library(self):
        for a in ALIASES:
            for n in LIBRARY:
                self.assertLess(library.ironledger_similarity(a, n), 0.8, f"{a} vs {n}")
                self.assertNotEqual(library._key(a), library._key(n))

    def test_under_threshold_against_each_other(self):
        names = sorted(ALIASES)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                self.assertLess(library.ironledger_similarity(a, b), 0.8, f"{a} vs {b}")


# Words that name a muscle. A synonym carrying one must map to an exercise with that primary.
KEYWORD_PRIMARY = {
    "hamstring": {"hamstrings"}, "nordic": {"hamstrings"}, "rdl": {"hamstrings"}, "sldl": {"hamstrings"},
    "calf": {"calves"}, "calves": {"calves"},
    "tricep": {"triceps"}, "triceps": {"triceps"}, "skull": {"triceps"}, "skullcrusher": {"triceps"},
    "pushdown": {"triceps"},
    "bicep": {"biceps"}, "biceps": {"biceps"},
    "quad": {"quadriceps"},
    "shrug": {"traps"},
    "lat": {"lats"}, "pulldown": {"lats"}, "chin": {"lats"}, "chinup": {"lats"}, "pullup": {"lats"},
    "adductor": {"glutes"}, "abductor": {"glutes"},
    "crunch": {"abs"}, "situp": {"abs"},
    "ohp": {"shoulders"}, "delt": {"shoulders"}, "lateral": {"shoulders"},
    "pec": {"chest"}, "fly": {"chest"}, "flye": {"chest"},
}
# Where IronLedger's own suggestion crosses muscle groups and the synonym deliberately doesn't.
PARSER_TRAPS = {
    "Hamstring Curl Machine": "Machine Curl",   # LB-3: a biceps exercise
    "Machine Hamstring Curl": "Machine Curl",
    "Barbell Upright Row": "Barbell Row",       # a back row, not the shoulder movement
}


def keyword_muscles(name):
    found = set()
    tokens = library._key(name).split()
    for t in tokens:
        for form in {t, t[:-1] if t.endswith("s") else t, t[:-2] if t.endswith("es") else t,
                     t[:-3] + "y" if t.endswith("ies") else t}:
            found |= KEYWORD_PRIMARY.get(form, set())
    if {"rear", "reverse"} & set(tokens):
        found.add("shoulders")
    return found


class SynonymMuscles(unittest.TestCase):

    def test_no_synonym_crosses_muscle_groups(self):
        checked = 0
        for s, t in SYNONYMS.items():
            expected = keyword_muscles(s)
            if expected:
                checked += 1
                self.assertIn(primary(t), expected, f"{s!r} -> {t!r}")
        self.assertGreater(checked, 50)

    def test_divergence_from_ironledger_is_deliberate(self):
        for s, t in SYNONYMS.items():
            hit = library.ironledger_best_match(s)
            if hit and hit[0] != t and primary(hit[0]) != primary(t):
                self.assertEqual(PARSER_TRAPS.get(s), hit[0], f"{s!r}: ours {t!r}, IronLedger {hit[0]!r}")
        for s, trap in PARSER_TRAPS.items():
            self.assertNotEqual(primary(SYNONYMS[s]), primary(trap))

    def test_same_primary_when_ironledger_agrees_on_tokens(self):
        # A score of 1.0 means the same words (plural, order or punctuation only): same exercise.
        for s, t in SYNONYMS.items():
            hit = library.ironledger_best_match(s)
            if hit and hit[1] == 1.0:
                self.assertEqual(hit[0], t, s)


class Normalize(unittest.TestCase):

    def test_known_traps(self):
        self.assertEqual(library.normalize("Pull-Ups"), ("Pull Up", "synonym"))
        self.assertEqual(library.normalize("Chin-Ups"), ("Chin Up", "synonym"))
        self.assertEqual(library.normalize("Push-Ups"), ("Push Up", "synonym"))
        self.assertEqual(library.normalize("Incline Dumbbell Press"), ("Dumbbell Incline Press", "synonym"))
        self.assertEqual(library.normalize("Hamstring Curl Machine"), ("Leg Curl", "synonym"))
        self.assertNotEqual(library.normalize("Hamstring Curl Machine")[0], "Machine Curl")
        self.assertEqual(library.normalize("Pause Bench Press"), ("Paused Bench Press", "synonym"))
        self.assertEqual(library.normalize("Barbell Upright Row"), ("Upright Row", "synonym"))

    def test_abbreviations_and_misspellings(self):
        for written, target in [("RDL", "Romanian Deadlift"), ("OHP", "Overhead Press"),
                                ("CGBP", "Close Grip Bench Press"), ("BSS", "Bulgarian Split Squat"),
                                ("SSB", "Safety Bar Squat"), ("DB Row", "Dumbbell Row"),
                                ("DB RDL", "Dumbbell Romanian Deadlift"), ("BB Row", "Barbell Row"),
                                ("inclind Dumbbell Press", "Dumbbell Incline Press"), ("Becnh", "Bench Press"),
                                ("Strict (Seated) Overhead Press", "Seated Overhead Press"),
                                ("Low Bar Barbell Back Squat", "Low Bar Squat"),
                                ("Farmer's Carries", "Farmer's Walk"), ("Heaves", "Pull Up")]:
            self.assertEqual(library.normalize(written), (target, "synonym"), written)

    def test_exact_and_case(self):
        self.assertEqual(library.normalize("Squat"), ("Squat", "exact"))
        self.assertEqual(library.normalize("Dumbbell Pullover (Back Focus)"),
                         ("Dumbbell Pullover (Back Focus)", "exact"))
        self.assertEqual(library.normalize("squat"), ("Squat", "synonym"))
        self.assertEqual(library.normalize("pull-up"), ("Pull Up", "synonym"))
        self.assertEqual(library.normalize("  Pull  Up "), ("Pull Up", "synonym"))
        self.assertEqual(library.normalize("farmers walk"), ("Farmer's Walk", "synonym"))

    def test_set_labels_are_stripped(self):
        self.assertEqual(library.normalize("Deadlift (Top Set)"), ("Deadlift", "synonym"))
        self.assertEqual(library.normalize("Bench Press (Back Down)"), ("Bench Press", "synonym"))
        self.assertEqual(library.normalize("RDL (warm-up)"), ("Romanian Deadlift", "synonym"))

    def test_never_guesses(self):
        for name in ["Pullover", "Shrugs", "Calf Raises", "Weighted Chin-Ups", "Weighted Pull Up",
                     "Romanian Deadlift Variation", "Leg Curls Please", "Goblet Box Squat", "", "   "]:
            self.assertEqual(library.normalize(name), (None, "unknown"), name)
        self.assertEqual(library.normalize(None), (None, "unknown"))
        self.assertIn("Dumbbell Pullover (Back Focus)", library.unmapped("pullover")["candidates"])

    def test_output_is_always_emittable(self):
        for s in list(SYNONYMS) + [w for a in ALIAS_LIST for w in a.get("also_written", [])]:
            target, how = library.normalize(s)
            if target is not None:
                self.assertTrue(library.known(target), s)

    def test_pending_alias_is_unknown(self):
        self.assertEqual(library.normalize("Trap Bar Deadlift"), (None, "unknown"))
        self.assertEqual(library.alias_status("Trap Bar Deadlift"), "pending")
        self.assertEqual(library.alias_status("hex bar deadlift"), "pending")
        self.assertIsNone(library.alias_status("Squat"))

    def test_existing_api_unchanged(self):
        # Synonyms never make a name known: F-7 still fails anything but the exact spelling.
        self.assertFalse(library.known("Incline Dumbbell Press"))
        self.assertFalse(library.known("Trap Bar Deadlift"))
        self.assertTrue(library.known("Dumbbell Incline Press"))
        self.assertEqual(library.primary_muscle("Close Grip Bench Press"), "triceps")


class ApprovedAlias(unittest.TestCase):
    """Once an alias is approved it is emittable, offered and normalised."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        shutil.copytree(ASSETS, self.tmp.name, dirs_exist_ok=True)
        path = Path(self.tmp.name) / "exercise-aliases.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        for a in doc["aliases"]:
            if a["name"] == "Trap Bar Deadlift":
                a["approved"] = True
        path.write_text(json.dumps(doc), encoding="utf-8")
        library.ASSETS = Path(self.tmp.name)
        library.clear_caches()

    def tearDown(self):
        library.ASSETS = ASSETS
        library.clear_caches()
        self.tmp.cleanup()

    def test_approved_alias(self):
        self.assertTrue(library.known("Trap Bar Deadlift"))
        self.assertEqual(library.normalize("Trap Bar Deadlift"), ("Trap Bar Deadlift", "exact"))
        self.assertEqual(library.normalize("Hex Bar Deadlift"), ("Trap Bar Deadlift", "synonym"))
        self.assertEqual(library.alias_status("Trap Bar Deadlift"), "approved")
        self.assertIn("Trap Bar Deadlift", library.substitutes("hinge"))
        self.assertEqual(library.substitutes("hinge", joint_tags=["low-back-friendly"]), ["Trap Bar Deadlift"])
        self.assertEqual(library.primary_muscle("Trap Bar Deadlift"), "glutes")
        # the others are still pending
        self.assertNotIn("Pause Deadlift", library.substitutes("hinge"))


class Substitutes(unittest.TestCase):

    def test_unapproved_aliases_excluded_by_default(self):
        default = library.substitutes("hinge")
        self.assertNotIn("Trap Bar Deadlift", default)
        self.assertNotIn("Pause Deadlift", default)
        self.assertIn("Trap Bar Deadlift", library.substitutes("hinge", include_unapproved=True))
        pending = {n for n, a in ALIASES.items() if not a["approved"]}
        for p in PATTERNS:
            self.assertEqual(set(library.substitutes(p)) & pending, set(), p)

    def test_equipment(self):
        subs = library.substitutes("squat", equipment=BARBELL_ONLY)
        self.assertIn("Squat", subs)
        self.assertNotIn("Goblet Squat", subs)
        self.assertNotIn("Leg Press", subs)
        for p in PATTERNS:
            for n in library.substitutes(p, equipment=BARBELL_ONLY, include_unapproved=True):
                self.assertLessEqual(set(library.option(n)["equipment"]),
                                     set(BARBELL_ONLY) | {"bodyweight", "none"}, n)
        self.assertEqual(library.substitutes("squat", equipment=[]), ["Bodyweight Squat"])
        self.assertNotIn("Trap Bar Deadlift",
                         library.substitutes("hinge", equipment=BARBELL_ONLY, include_unapproved=True))
        self.assertIn("Trap Bar Deadlift",
                      library.substitutes("hinge", equipment=BARBELL_ONLY + ["trap_bar"], include_unapproved=True))

    def test_avoid_and_dislikes(self):
        base = library.substitutes("squat")
        self.assertIn("Goblet Squat", base)
        self.assertNotIn("Goblet Squat", library.substitutes("squat", dislikes=["Goblet Squat"]))
        self.assertNotIn("Goblet Squat", library.substitutes("squat", dislikes=["goblet squats"]))
        self.assertNotIn("Front Squat", library.substitutes("squat", avoid=["Front Squat"]))
        both = library.substitutes("squat", avoid=["Leg Press"], dislikes=["Hack Squat"])
        self.assertFalse({"Leg Press", "Hack Squat"} & set(both))
        # a dislike of one spelling removes the lift under both keys (LB-6)
        self.assertNotIn("Squat", library.substitutes("squat", dislikes=["Back Squat"]))
        # a pattern key in avoid removes the pattern
        self.assertEqual(library.substitutes("vertical pull", avoid=["horizontal pull"]),
                         library.substitutes("vertical pull")[:len(PATTERNS["vertical pull"]["options"])])
        self.assertEqual(library.substitutes("squat", avoid=["squat"]), [])

    def test_excludes_the_exercise_itself(self):
        subs = library.substitutes("Squat")
        self.assertNotIn("Squat", subs)
        self.assertNotIn("Back Squat", subs)
        self.assertIn("Goblet Squat", subs)
        self.assertNotIn("Leg Curl", library.substitutes("Hamstring Curl Machine"))
        self.assertIn("Nordic Curl", library.substitutes("Hamstring Curl Machine"))
        self.assertIn("Squat", library.substitutes("squat"))

    def test_second_spellings_never_offered(self):
        for n in ["Back Squat", "Conventional Deadlift", "Military Press"]:
            for p in PATTERNS:
                self.assertNotIn(n, library.substitutes(p, include_unapproved=True))

    def test_joint_tags(self):
        self.assertEqual(library.substitutes("squat", joint_tags=["knee-friendly"]), ["Leg Press", "Box Squat"])
        self.assertEqual(library.substitutes("single-leg/lunge", joint_tags=["knee-friendly"],
                                             include_unapproved=True), ["Reverse Lunge"])
        self.assertEqual(library.substitutes("hinge", joint_tags=["low-back-friendly"]), [])
        self.assertEqual(library.substitutes("squat", joint_tags=["shoulder-friendly"]), [])
        self.assertIn("High foot", library.option("Leg Press")["joint_tags"]["knee-friendly"])

    def test_order_follows_the_table(self):
        order = [o["name"] for o in PATTERNS["horizontal push"]["options"]]
        subs = library.substitutes("horizontal push", equipment=BARBELL_ONLY)
        self.assertEqual(subs, [n for n in order if n in subs])

    def test_fallback_comes_after_own_options(self):
        full = library.substitutes("vertical pull")
        own = [o["name"] for o in PATTERNS["vertical pull"]["options"]]
        self.assertEqual(full[:len(own)], own)
        self.assertEqual(library.pattern_of(full[len(own)]), "horizontal pull")
        barbell = library.substitutes("vertical pull", equipment=BARBELL_ONLY)
        self.assertTrue(barbell)
        self.assertTrue(all(library.pattern_of(n) == "horizontal pull" for n in barbell))

    def test_unknown_input(self):
        self.assertEqual(library.substitutes("Underwater Basket Weaving"), [])
        self.assertEqual(library.substitutes("Pullover"), [])


class Coverage(unittest.TestCase):
    """Every template slot has options: 3 or more in a full gym, 1 or more with only a barbell,
    rack, bench and plates. A pattern with no library options at all (alias_only) needs an approved alias."""

    def test_template_slots(self):
        slots = [p for p, spec in PATTERNS.items() if spec["template_slot"]]
        self.assertGreaterEqual(len(slots), 15)
        for p in slots:
            with self.subTest(pattern=p):
                if PATTERNS[p].get("alias_only"):
                    self.assertTrue(library.substitutes(p, include_unapproved=True))
                    continue
                self.assertGreaterEqual(len(library.substitutes(p, equipment=FULL_GYM)), 3)
                self.assertGreaterEqual(len(library.substitutes(p, equipment=BARBELL_ONLY)), 1)

    def test_required_patterns_exist(self):
        for p in ["squat", "hinge", "horizontal push", "vertical push", "horizontal pull", "vertical pull",
                  "single-leg/lunge", "knee flexion", "hip extension", "elbow flexion", "elbow extension",
                  "lateral delt", "rear delt/upper back", "anti-extension core", "anti-rotation core", "carry",
                  "calf", "conditioning"]:
            self.assertIn(p, PATTERNS)

    def test_conditioning_is_not_import_rows(self):
        self.assertIs(PATTERNS["conditioning"].get("import_rows"), False)   # IL-28


class PatternKeys(unittest.TestCase):

    def test_spellings(self):
        self.assertEqual(library.pattern_key("hinge"), "hinge")
        self.assertEqual(library.pattern_key("hip-hinge"), "hinge")
        self.assertEqual(library.pattern_key("knee-flexion"), "knee flexion")
        self.assertEqual(library.pattern_key("Single-Leg/Lunge"), "single-leg/lunge")
        self.assertEqual(library.pattern_key("squat-unilateral"), "single-leg/lunge")
        self.assertIsNone(library.pattern_key("Squat Day"))
        self.assertEqual(library.substitutes("hip-hinge"), library.substitutes("hinge"))
        self.assertEqual(library.substitutes("knee-flexion"), library.substitutes("knee flexion"))

    def test_aliases_point_at_patterns(self):
        for a, p in SUBS["pattern_aliases"].items():
            self.assertIn(p, PATTERNS, a)

    def test_template_patterns_resolve(self):
        # Every slot pattern a template names must reach this table (A-9).
        found = 0
        for path in sorted((ASSETS / "templates").glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            stack = [doc]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    if isinstance(node.get("pattern"), str):
                        found += 1
                        self.assertIsNotNone(library.pattern_key(node["pattern"]), f"{path.name}: {node['pattern']}")
                    stack.extend(node.values())
                elif isinstance(node, list):
                    stack.extend(node)
        if not found:
            self.skipTest("no template names a slot pattern yet")


class PatternOf(unittest.TestCase):

    def test_every_option(self):
        for p, o in options():
            self.assertEqual(library.pattern_of(o["name"]), p, o["name"])

    def test_forms(self):
        self.assertEqual(library.pattern_of("RDL"), "hinge")
        self.assertEqual(library.pattern_of("Pull-Ups"), "vertical pull")
        self.assertEqual(library.pattern_of("Hamstring Curl Machine"), "knee flexion")
        self.assertEqual(library.pattern_of("Reverse Lunges"), "single-leg/lunge")
        self.assertEqual(library.pattern_of("Machine Curl"), "elbow flexion")
        self.assertIsNone(library.pattern_of("Pullover"))
        self.assertIsNone(library.pattern_of("hinge"))


class CloseVariants(unittest.TestCase):

    def test_squat(self):
        v = library.close_variants("Squat")
        for n in ["Pause Squat", "Safety Bar Squat", "Box Squat", "Front Squat", "Tempo Squat", "High Bar Squat"]:
            self.assertIn(n, v)
        for n in ["Squat", "Back Squat", "Goblet Squat", "Leg Press", "Pin Squat"]:
            self.assertNotIn(n, v)
        self.assertEqual(library.close_variants("Back Squat"), v)
        self.assertIn("Pin Squat", library.close_variants("Squat", include_unapproved=True))

    def test_bench(self):
        v = library.close_variants("Bench Press")
        for n in ["Paused Bench Press", "Close Grip Bench Press", "Larsen Press", "Spoto Press"]:
            self.assertIn(n, v)
        self.assertNotIn("Dumbbell Bench Press", v)

    def test_deadlift(self):
        v = library.close_variants("Deadlift")
        for n in ["Deficit Deadlift", "Block Pull", "Romanian Deadlift", "Sumo Deadlift"]:
            self.assertIn(n, v)
        self.assertNotIn("Pause Deadlift", v)
        self.assertIn("Pause Deadlift", library.close_variants("Deadlift", include_unapproved=True))
        self.assertEqual(library.close_variants("Conventional Deadlift"), v)

    def test_variant_input(self):
        v = library.close_variants("Pause Squat")
        self.assertEqual(v[-1], "Squat")
        self.assertNotIn("Pause Squat", v)
        self.assertEqual(library.close_variants("CGBP")[-1], "Bench Press")

    def test_not_a_competition_lift(self):
        self.assertEqual(library.close_variants("Overhead Press"), [])
        self.assertEqual(library.close_variants("Leg Press"), [])
        self.assertEqual(library.close_variants("nonsense"), [])


if __name__ == "__main__":
    unittest.main()
