---
name: ironledger-meet-attempts
description: Plan a powerlifter's opener, second and third attempts for a meet from their recent training, using the IPF and USAPL attempt rules and published coaching guidance, with IronLedger's calculators for estimated maxes, plates, warm-ups and DOTS or IPF GL scores. Use when a lifter asks what to open with, wants their attempts planned for a meet, or asks how to change attempts on meet day.
---

# Plan meet attempts

Attempt selection is a judgement call. Coaches and studies publish ranges, not answers, and they disagree on the details. This skill turns the lifter's own training into a plan with options, names the source of every number, and leaves the decision with the lifter or their coach. The quotes behind every rule here are in `references/sources.md`.

## 1. Ask first

- **Federation and unit.** Attempt rules differ between federations; this skill quotes the IPF and USAPL rulebooks. For any other federation, ask the lifter to check its current rulebook. Ask whether the meet runs in kilograms or pounds.
- **Recent training for each lift:** their heaviest recent sets with weight, reps and RPE if they logged it, and which of those met competition standard (depth, pause, lockout). Also their tested one-rep max, if they have one, and their best competition lift. An IronLedger History CSV export has the weights, reps and RPE (read it the way the `ironledger-training-review` skill describes), but not whether a lift met competition standard. Ask.
- **Experience:** first meet, or how many before.
- **Goal:** a total, a qualifying total, a placing, or a personal record on one lift.
- **For scores:** sex, expected bodyweight, and classic (raw) or equipped.

## 2. The rules every plan must follow

From the IPF Technical Rulebook (effective 1 March 2026):

- The bar must always be a multiple of 2.5 kg, and, except for record attempts, "the progression must be at least 2.5 kg between all attempts". A record attempt must be at least 0.5 kg over the record.
- Openers for all three lifts are declared at weigh-in. Each opener may be changed once, higher or lower. The first group can change until three minutes before the first round of that lift; later groups until three attempts before the end of the previous group's last round.
- The second and third attempts must be submitted within one minute of the previous attempt, counted from when the referees' lights come on. If nothing is submitted, the bar goes up 2.5 kg after a good lift, or stays at the failed weight after a miss.
- Once submitted, second attempts and the third squat and bench press can't be changed. The third deadlift can be changed twice, until the lifter is called to the bar.
- After a miss, the lifter can take the same weight again in the next round.
- The bar and collars weigh 25 kg (a 20 kg bar and two 2.5 kg collars).

The USAPL Rulebook (version 2026.2) has the same rules for submitting, changing and repeating attempts (its deadline for later flights' opener changes is worded slightly differently), and adds:

- An attempt may never be lower than the previous one; after a miss, the same weight may be repeated.
- Meets run in pounds use 5 lb steps, and the automatic increase is 5 lb.
- Local meets may use a 45 lb bar with pound plates and 5 lb collars.
- Youth lifters may use any multiple of 0.5 kg.

## 3. What coaches and studies say

Each source measures from a different base. Use the base the source names, and tell the lifter which one you used.

| Source | Opener | Second | Third | Measured from |
|---|---|---|---|---|
| Matt Gary (MASS interview, 2023) | 90–92%, "about 91% for most people" | 95–97%; he doesn't recommend going over 97% | No set percentage: "that next 2.5 kg increment above their current PR" if the second moves well; if it was hard, a weight "to potentially tie your PB or PR" | One-rep max |
| Matt Gary (2009) | 90–92% | 95–97%, "no higher than 98%" | "the next five-pound (2.5kg) increment" for a PR | "your one-rep max (competition PR)" |
| Chad Wesley Smith (JTS, 2015), for a first meet | 90–92% | 95–97% | 99–102% | "your best CLEAN (deep, paused, full lockout, etc) lift in the gym during that training cycle", stated for the opener |
| Eduardo Chile (RTS, 2016), for a first meet | 87–89% (bench 88–90%) | 94–96% | 99–102% | Not stated |

Two studies describe what lifters actually did. Use them as a comparison, not as a base to plan from:

- Elite classic lifters who made all nine attempts at IPF Classic World Championships opened at about 91% of their third attempt, then went up about 5% and about 3% (Travis, Zourdos and Bazyler, 2021).
- In raw Powerlifting Australia meets, squat openers averaged 92% of the best squat that day (Howells and colleagues, 2022).

Rules the coaches give:

- **Opener:** "easy enough that you can make the lift on your worst day" (Gary, 2009), and "a number that you can hit under any circumstance" (Smith). Gary (2023) puts the opener "somewhere around your best triple", and for a novice who has never tested a true one-rep max, that best triple to competition standard is "a safe place to open".
- **Plan options:** "Have light, medium, and heavy options for your second and third attempts" (Gary, 2009).
- **Warm-ups go badly:** "lower your opener" (Gary, 2009), using the one change the rules allow.
- **A missed opener:** Gary repeats it (2009 and 2023). In 2023 he said he might still move up after a technical miss, such as a rack command; in 2009 he advocated repeating even then. Chile: "If you fail a weight for any reason, you should likely repeat it and then go up from there."
- **Jumps:** "Always make weight increases incrementally smaller" (Gary, 2009).
- **A hard second:** "take what's there – not what you want" (Gary, 2009).

What the meet data show:

- Third attempts succeed less often than seconds, in both sexes (Darragh and colleagues, 2026, 93,333 IPF raw lifters). Fewer than half of lifters made their third bench press in Australian raw meets (van den Hoek and colleagues, 2022).
- At IPF World Championships, making 8 or 9 of 9 attempts raised the odds of winning 5.9 times for men and 1.5 times for women (van den Hoek and colleagues, 2023).
- One research group differs from the coaches: van den Hoek and colleagues (2022) suggest coaches consider openers at weights usually chosen for second attempts (about 95–97%). They say this "differs from current coaching strategies" and should be tried in training or recreational meets first. Mention it only alongside the coaches' ranges, never instead of them.

## 4. Build the plan with the IronLedger calculators

The tools are on the free IronLedger MCP server (`https://www.ironledger.app/mcp`), or the HTTP API at `https://www.ironledger.app/api/tools/<slug>`. See the `ironledger-strength-calculators` skill.

1. **Choose a source and its base for each lift.** For Gary, use a tested one-rep max or best competition lift. For Smith, use the best lift done to competition standard this training cycle. If the lifter has neither, estimate a one-rep max from a recent heavy set with `rpe_estimate_max` (weight, reps and RPE) or `one_rep_max` (weight and reps), and say it is an estimate. An estimate from more than 10 reps is unreliable, and the tool says so.
2. **Apply that source's ranges.** Round each attempt to a legal weight: a multiple of 2.5 kg, or 5 lb in a USAPL meet run in pounds.
3. **Check the plan:** each attempt at least one legal step over the one before, each jump no bigger than the jump before it, and light, medium and heavy options for the second and third.
4. **Plates:** call `plate_loading` with `collars` true. For a kilogram meet, use `unit` kg, `bar` 20 and `collarWeight` 2.5. For a USAPL local meet in pounds, use `unit` lb, `bar` 45 and `collarWeight` 5.
5. **Warm-ups to the opener:** call `warmup_sets` with the opener as `workingWeight`. That is the ramp the IronLedger app suggests in training. If the lifter has a warm-up they already use, keep theirs.
6. **Scores:** call `powerlifting_score` with the total of each plan (light, medium and heavy), bodyweight, sex and equipment, for DOTS and IPF GL. A lifter chasing a placing or a qualifying total can see what each third deadlift does to the result.

## 5. Hand it over

For each lift, give:

- the opener, with its percentage of the base and the base named;
- light, medium and heavy options for the second and the third;
- the source of each range;
- the plates for each attempt.

Then add a meet-day card with the rules from section 2: one change per opener and its deadline, one minute to submit, no changes to seconds or the third squat and bench press, and two changes to the third deadlift.

## Be honest

- Attempt selection is a judgement call. Give options and their sources; the lifter or their coach decides.
- Use only the ranges and rules in this skill and its sources. Don't add percentages of your own, and don't mix one source's percentages with another's base.
- A third attempt is a chance, not a promise.
- Rules change. Tell the lifter to check the current rulebook for their federation and meet.
- This skill doesn't cover making weight or tapering. For a weight cut, the lifter needs a coach or a qualified professional.
- This is training guidance, not medical advice.
