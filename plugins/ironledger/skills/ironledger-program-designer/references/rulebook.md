# Rulebook

These are the program designer's house rules and the general programming rules every draft must satisfy. The house rules are practice-based defaults, and the evidence rules come from verified research. Client-type rules live in `client-types.md`, the Notes voice in `voice.md`, and the IronLedger file contract in `ironledger-import.md`. Where a rule depends on a method decision, it follows that decision's recommended option and carries the decision's ID.

Rule IDs are stable, so some numbers are missing. In each rule, `ev:` lists PubMed IDs, every one of which is in `evidence.md`.

## Method decisions

Every rule tagged `{Mnn}` follows the recommended option of a method decision. They are listed so a lifter, or the AI working with them, can see which choices a draft rests on; preflight reports the ones each draft relied on (F-9).

| Decision | Status | Rules that depend on it |
|---|---|---|
| M1 main-lift frequency | recommended option | L-15 (and CT rules) |
| M2 rounding | recommended option | L-4 |
| M3 supplemental work | recommended option (BBB only on request) | L-14 |
| M4 deload | recommended option | L-7 |
| M5 warm-up | recommended option | L-6 |
| M6 e1RM input | recommended option | L-1, L-2 |
| M7 TM and progression | recommended option | L-3, L-9, L-10 |
| M8 accessory effort | recommended option | A-4 |
| M9 rest | recommended option | L-16 |
| M10 meet-prep template (top set and back-downs) | recommended option | CT-PLM-1, CT-PLM-2, CT-PLM-4 to CT-PLM-6, CT-PLM-14, CT-PLM-20 |
| M11 block length | recommended option | L-8 |
| M12 volume accounting | recommended option | P-2 to P-6 |
| M13 accessory progression | recommended option | A-6 |
| M14 hypertrophy rotation | recommended option | CT-HYP-1, CT-HYP-5, CT-HYP-6 |
| M15 Notes voice | recommended option (A, the fuller style) | VO-1, VO-2 |
| M16 squat default | recommended option | L-17 |
| M18 ADF preparation | recommended option | CT-ADF-1, CT-ADF-4 to CT-ADF-6, CT-ADF-9, CT-ADF-11 |
| M19 rugby | recommended option | CT-RGO-1, CT-RGO-6, CT-RGO-10, CT-RGO-13, CT-RGI-1, CT-RGI-2, CT-RGI-4, CT-RGI-10 |
| M20 warm-up blocks | recommended option | CT-PT-2, CT-RGO-7 |
| M26 close variants for powerlifters | recommended option | CT-PLO-1, CT-PLO-15 |
| M28 two-block progression | chosen: option A | OO-4 |

## G. Ground rules

- **G-1** [POL] The lifter decides. The skill drafts, checks and explains; the lifter chooses what to run
- **G-2** [POL] Present signals, options and counter-signals. Never present a single recommended action as the answer
- **G-4** [POL] No program is drafted until the lifter has completed Stage 1 of the Adult Pre-Exercise Screening System (APSS V2, ESSA, Fitness Australia and Sports Medicine Australia), which "may be self-administered and self-evaluated". Ask the six questions exactly as written in SKILL.md. A yes to any of them means the lifter should "seek guidance from an appropriate allied health professional or medical practitioner prior to undertaking exercise", and the skill drafts nothing until they have that guidance. `screen_cleared` is set only on six noes or the professional's go-ahead. A condition the lifter reports (for example pregnancy or osteoporosis) is recorded in `flags`, and the rules that depend on it act on it
- **G-6** [POL] All arithmetic comes from the skill's scripts, with their inputs shown. Never calculate loads, e1RMs, volumes, trends or thresholds in prose
- **G-7** [POL] Every draft passes pre-flight before the lifter sees it. Any departure from a rule carries a written reason, shown to the lifter
- **G-8** [POL] Cite research only by PMIDs listed in evidence.md. Never cite from a blog or from memory
- **G-9** [POL] Red flags (RF rules) come first, the moment the lifter mentions one, before any program work
- **G-10** [POL] Never diagnose injury, illness, disordered eating, RED-S, overtraining or a mental-health condition, and never give medical, physiotherapy or psychological advice. A red flag gets a referral pathway and nothing more. Nutrition follows the ironledger-nutrition-plan skill and its own referral hard stops
- **G-11** [POL] Never invent data, exercises, citations, credentials or results, and never fill missing data silently. Missing inputs are asked for once, as a single list
- **G-12** [POL] Never flag on a single data point except for safety, and never describe noise as a trend
- **G-13** [POL] Never compute ACWR, an injury-risk score or an opaque readiness score, and never label anyone a non-responder
- **G-14** [POL] Never write controlling, shaming or body-focused language
- **G-15** [POL] Never override the lifter's documented constraints: injuries, a clinician's advice, equipment, schedule and stated dislikes
- **G-16** [POL] Take the lifter's facts only from the current conversation's inputs. Never from memory or from anyone else's data, and the profile and program must be the same lifter's
- **G-17** [POL] Every flag shows its data sufficiency and a confidence level
- **G-20** [POL] When two rules can't both be met, this order wins: (1) G rules, RF rules and a clinician's limits; (2) the CT-NOV, CT-FEM and CT-PT safety rules; (3) the primary type's CT rules; (4) modifier CT rules; (5) rulebook L, A, P and W rules; (6) F, VO and IL format rules. Format rules never loosen a dose but always block the build. On effort, the higher RIR wins, and an AMRAP that a CT floor or ban rules out becomes a fixed-rep set at that floor. A disliked exercise that a CT rule makes mandatory is swapped for an allowed regression with the reason in Notes, or the lifter is asked

## RF. Red flags: stop and refer

When the lifter mentions any of these, stop the program work, quote their words back, give the pathway and nothing more (G-9, G-10). Emergency numbers: 000 in Australia, 911 in the US and Canada, 999 or 112 in the UK, 112 across the EU.

- **RF-5** [POL] Acute medical: chest pain or pressure, fainting, palpitations, unusual breathlessness, new neurological symptoms (numbness, weakness, speech or vision change) or severe headache with exertion. Pathway: stop training; the emergency number for urgent symptoms; otherwise a doctor before any further training
- **RF-6** [POL] Possible cauda equina syndrome: new saddle numbness or pins and needles, bladder or bowel disturbance (retention, incontinence, loss of sensation), or leg pain that starts on one side and becomes bilateral. Pathway: an emergency department the same day; no loaded spinal work until cleared (ev: 32438853)
- **RF-7** [POL] Other serious spinal pathology features: possible fracture (trauma, osteoporosis, long-term corticosteroid use), malignancy (a history of cancer, night pain with no comfortable position, unexplained weight loss) or infection (immunosuppression, IV drug use, fever, feeling systemically unwell). Pathway: a doctor or physiotherapist the same day; no loaded spinal work until cleared (ev: 32438853)
- **RF-8** [P] Other musculoskeletal red flags: a suspected fracture, a joint locking or giving way, or a hot, swollen joint. Pathway: stop the provoking work; a doctor, physiotherapist or sports doctor the same day
- **RF-9** [P/D] Pain or injury: new pain over 3/10 during a lift, any pain still present the next morning, pain rising week to week, a known niggle over 5/10, swelling, pain that changes how the lifter moves, or a pop or sudden onset. Pathway: remove or modify the provoking exercise and recommend a physiotherapist or sports doctor (ev: 17307888, 33632313)
- **RF-10** [W/P] A niggle the lifter already knows about is amber, not a red flag, while it stays at 5/10 or below and settles by the next morning: at 0 to 2/10 the lifter trains as planned; at 3 to 5/10 the lifter continues without progressing that pattern; a clinician-managed issue follows the clinician's limits (ev: 17307888, 33632313, 28596288)
- **RF-11** [M] Around any pain flag, the options keep everything pain-free in the program and swap the aggravating movement for a variation (range, grip or stance, implement, tempo, unilateral) within RF-10 limits; sprinting stays pain-free (ev: 27226389, 36650032)
- **RF-12** [POL] Suspected concussion: no training, and a doctor or sports doctor; the return to contact or heavy training follows the clinician's clearance (ev: 37316210)
- **RF-13** [POL] Illness: fever, chest symptoms or systemic symptoms, or chest pain, palpitations or breathlessness after a viral illness. Pathway: no training while feverish or systemically unwell, and a doctor if severe or persisting; chest pain, palpitations or breathlessness after a viral illness also need a medical review before hard training (ev: 35353361, 35863871)
- **RF-14** [POL] Disordered eating or RED-S. Any one of these raises the flag on its own: rapid unplanned weight loss; missed, lost or irregular periods; a bone stress injury, bone pain or recurrent injuries; fainting; frequent or recurrent illness; low libido; gastrointestinal problems; strength or performance falling despite training as planned, when unexplained; a restrictive eating pattern; preoccupation with food, weight or shape; compensatory exercise; secrecy around eating; extreme cuts for weigh-ins. Two or more of persistent fatigue or low mood, feeling cold and dizziness raise it together. Pathway: a doctor or sports physician first; in Australia, the Butterfly Helpline 1800 33 4673 (not a crisis line); no calorie deficit, and training load held (ev: 32661127, 37752011, 24563388)
- **RF-15** [POL] Mental health: persistent low mood or hopelessness, anxiety interfering with life, withdrawal, or substance misuse. Pathway: encourage a doctor or a psychologist; in Australia, Beyond Blue 1300 22 4636 (ev: 31097450, 32948518)
- **RF-16** [POL] Any mention of self-harm or suicide, in any wording, comes first. Pathway: the emergency number if there is immediate danger; crisis lines: in Australia, Lifeline 13 11 14; in the US, call or text 988; in the UK and Ireland, Samaritans 116 123 (ev: 31097450, 32948518)
- **RF-18** [D] A new health condition or a new medication means the lifter re-answers the G-4 screen before training continues

## F. Output and format hygiene

- **F-3** [H] Rep ranges use an ASCII hyphen (`10-12`) in a text-typed cell, so they can't become dates. Never write "10 to 12" or an en-dash range: IronLedger logs the first number of those. The import file follows IL-9
- **F-4** [H] Barbell work states its rest with the IL-14 tokens: `Rest 2 min` on bar and warm-up sets, and work-set rest per L-16. Accessory rest left unstated means IronLedger's 90 s default, which meets P-18
- **F-5** [H] Every barbell load is plate-loadable: a multiple of the L-4 step. A warm-up that would fall below the empty bar is the bar (`20` in the import). A work set below 20 kg is flagged to the lifter with a dumbbell or technique-bar option. Reject any 5/3/1 wave whose loads don't rise. Consecutive sets at the same load are allowed only for FSL, BBB, back-down and fixed-load accessory sets
- **F-6** [H] Build every program from a clean template. Never carry a previous lifter's code, name, email or numbers into a new file
- **F-7** [H] Every exercise name matches the canonical list exactly (see ironledger-import.md LB rules). Misspellings fail pre-flight
- **F-8** [H] Never output #REF!, a blank required cell or a negative RIR. RIR floors at 0
- **F-9** [POL] Preflight states every method decision the draft relied on, and the skill shows them to the lifter with the draft
- **F-10** [H] Loads are in kg unless the lifter profile says lb. Never mix units within one file
- **F-11** [D] For a lifter whose profile unit is lb: the load step is 5 lb (2.5 lb with microplates), the bar is 45 lb, TM increments are +10 lb lower body and +5 lb upper body, and CT-PLM-1's top-set ranges are 20 lb (squat, deadlift) and 10 lb (bench). Every other kg figure converts at 2.2046 and then rounds up to the lb step

## L. Load engine (5/3/1)

- **L-1** [H] {M6} e1RM = weight × reps × 0.0333 + weight, rounded up to the L-4 step
- **L-2** [M] {M6} The benchmark input is a set of 2 to 8 reps (10 at most, 6 or fewer preferred) done with technical form, taken to RIR 0 to 2 or as an AMRAP, within the last 8 weeks. A single counts as e1RM = the weight lifted, with no 0.0333 inflation (ev: 16937972, 7500624, 18714230, 37792272)
- **L-3** [H] {M7} TM = 90% of e1RM, rounded up. Use 85% for novice or returning lifters, and for an uncertain benchmark: older than 8 weeks, self-reported rather than logged, or rated RIR 3 or more. Every wave percentage is a percentage of TM, never of the true max (ev: 37792272)
- **L-4** [H] {M2} Every computed load rounds up (CEILING) to 2.5 kg, never to nearest and never down. 1.25 kg is allowed per lifter only when the profile records microplates
- **L-5** [H] The wave is: week 1 65/75/85% × 5/5/5+, week 2 70/80/90% × 3/3/3+, week 3 75/85/95% × 5/3/1+. The last work set is marked AMRAP and labelled "5+", "3+" or "1+"
- **L-6** [H/P] {M5} The main-lift warm-up is bar × 20, then 40/50/60% TM × 5/5/3, at 2 min rest
- **L-7** [H/W] {M4} The week 4 deload keeps the L-6 main-lift warm-up only, with no work sets and no AMRAP. Accessories keep the same exercises with 30 to 50% fewer sets at RIR +1 (at least 3). A deload is never complete rest for a strength-priority lifter (ev: 38499934, 37730925, 38274324)
- **L-8** [H] {M11} A block is 3 loading weeks and 1 deload week
- **L-9** [H] {M7} Between cycles, raise TM by 5 kg on squat and deadlift and 2.5 kg on bench and OHP, and only for lifts whose every AMRAP in the cycle met its minimum reps. A lift with a missed AMRAP holds its TM
- **L-10** [P] {M7} Downward rule: if an AMRAP falls below its minimum on 2 consecutive exposures, or e1RM falls across 3 or more exposures without planned fatigue, reset that lift's TM to 90% of the new e1RM or insert a deload, and tell the lifter. M7's reset replaces 03 r19's flat 5 to 10% cut
- **L-11** [M/P] Noise gate: a TM moves beyond its standard increment only when the cycle's heaviest AMRAP has 10 reps or fewer, technical form with no grind past RPE 9.5, and an e1RM that agrees with at least one prior exposure within about 5%. The TM then becomes 0.9 × that e1RM. Otherwise the lift takes the standard increment or holds (ev: 32681399)
- **L-12** [M] TM and e1RM updates from logged sets use only sets of 10 reps or fewer (6 or fewer preferred) done with technical form (ev: 16937972, 7500624, 18714230, 37792272)
- **L-13** [H] The AMRAP cue reads "as many strong reps as you can, leaving 1 to 2 in the tank". The reps are recorded and an e1RM is computed from them under L-12. This cue is the effort cap for 5/3/1 percentage sets (ev: 37792272)
- **L-14** [H/W] {M3} Supplemental work after the main sets defaults to FSL, 3 to 5 sets × 5 at the first work-set percentage. Hypertrophy-leaning lifters get FSL plus the CT-HYP-2 hard-set accessories. BBB is used only when the lifter asks for it, with its sets prescribed to end at RIR 2 or closer (P-8). Two- and three-day or time-poor programs get none
- **L-15** [H] {M1} The default split is 4 days, one main lift per day, in the order Squat, Bench, Deadlift, OHP. Powerlifters (CT-PLO, CT-PLM) and general lifters whose main goal is a barbell-lift number (CT-GEN-5) get template 531-2x, a second, lighter exposure of each competition lift. Every other type keeps one main-lift exposure a week (CT-GEN-1)
- **L-16** [H/M] {M9} Main work sets rest 3 min, rising to 3 to 5 min on heavy triples, singles and top sets. FSL, BBB and back-down sets rest 2 min (ev: 28933024, 39205815)
- **L-17** [H] {M16} Squat defaults to high bar for general and club lifters. Low bar is used only for powerlifters who already squat low bar
- **L-18** [H] Loads are computed when the program is generated. Editing a benchmark regenerates future weeks only; weeks already trained stay as prescribed

## A. Accessories

- **A-1** [H] After the main lift come 3 to 5 accessories: first 1 or 2 compound, same-pattern hard sets (default 3 × 10 to 12 at 2 RIR; variant 2 × 6 to 10 at 0 RIR, but only on a machine, cable or supported exercise; a free-weight compound stops at RIR 1), then isolation at 3 × 10 to 12 at 2 to 3 RIR, finishing with trunk work at 2 to 4 × 12 to 20 at 2 to 4 RIR
- **A-2** [H] Default pairings by day. Squat day: unilateral leg, goblet or front squat, core. Bench day: DB press, row or chin, laterals or triceps. Deadlift day: RDL or hamstring, a second squat pattern, core. OHP day: incline DB press, row, push-ups or core
- **A-3** [H] Put "AMRAP Last Set" on 1 or 2 isolation accessories per upper-body day. That set is its own row (IL-30: Sets 1, Reps such as `12+`, RIR `0-1`) and is left out of A-6's double-progression check
- **A-4** [H] {M8} Accessory RIR stays constant across the block for general lifters. Only the topset-backdown template changes it, using the CT-PLM-13 offsets
- **A-5** [H] Every program the lifter imports expresses effort as RIR, not RPE
- **A-6** [M] {M13} Accessories use double progression: add 2 to 10% load only when the top of the rep range is reached on every set at the target RIR (ev: 19204579)
- **A-7** [W/M] No planned failure on free-weight compound sets. Isolation, machine and supported work may reach 0 RIR (ev: 24998610, 32049887, 33497853)
- **A-8** [H] Never program an exercise the lifter listed as disliked. Any choice made because of an injury or a dislike gets its reason in Notes
- **A-9** [POL] Substitutions come only from the exercise library and its substitution table. An exercise that isn't in the library or the alias table fails pre-flight

## P. General programming (evidence rules)

- **P-1** [P] Every draft states the lifter's training-status class (novice, intermediate or advanced) and its basis: training age, rate of e1RM progress and RPE-rating experience (ev: 19204579, 34965513)
- **P-2** [M] {M12} Every draft includes a weekly table of fractional hard sets per muscle: direct sets count 1 and indirect sets 0.5. A hard set is one that ends at 4 RIR or closer (ev: 41343037, 38970765)
- **P-3** [S/M] {M12} For intermediate and advanced hypertrophy goals, priority muscles get 10 to 20 fractional hard sets a week and every other muscle at least 6 (ev: 41843416, 35291645, 41343037)
- **P-4** [W/M] {M12} More than 20 sets a week goes only to at most 2 specialisation muscles, and only when the log shows the lifter tolerated similar volume (stable RPE at fixed loads, no e1RM decline) (ev: 30153194, 37796222, 32058362)
- **P-5** [M] {M12} Novices get 4 to 10 fractional hard sets per muscle per week, full body, over 2 to 3 sessions (ev: 34125411, 12618576)
- **P-6** [W] {M12} Block volume starts from the lifter's last 2 to 4 weeks of logged volume and rises by no more than about 20% per block, or by 1 to 3 sets per muscle per week within a mesocycle (ev: 32108724, 31813190)
- **P-7** [P] Any muscle given more than 10 sets a week is trained in at least 2 sessions, and no muscle gets more than about 11 fractional sets in one session. Frequency itself is neutral at equal weekly volume; the split is a practical way to keep sessions productive (ev: 30558493, 41343037)
- **P-8** [S] Hypertrophy work uses 5 to 30 reps (default: compounds 5 to 12, isolation 8 to 20). Loads under 60% 1RM are used only when sets end at 2 RIR or closer (ev: 33433148, 28834797, 33671664, 34542869)
- **P-9** [S] Every working set has an RIR or RPE target or cap. No set is prescribed by percentage alone (5/3/1 sets meet this through L-13) (ev: 37792272)
- **P-10** [M] RIR bands: hypertrophy 0 to 3 RIR (isolation may reach 0; free-weight compounds 1 to 3). Main strength lifts 1 to 4 RIR (RPE 6 to 9), except test and peak singles (ev: 38970765, 36334240, 38393985, 33497853, 42410632)
- **P-11** [M/P] Novices under 6 months train free-weight compounds at RIR 2 or more. No RPE-derived e1RM is used until the lifter has had at least 4 weeks of RIR practice with rep-count feedback (ev: 26049792, 28301439, 34542869)
- **P-12** [P] Every program states its load-adjustment rule. A set that comes in at least 1 RPE over its cap reduces the next sets by 2.5 to 5%. Being at least 1 RPE under target for 2 sessions brings the next increase forward (ev: 35038063, 29628895)
- **P-13** [M] Every exercise names its progression model: linear load (novice main lifts), double progression (accessories), TM and AMRAP wave (intermediate main lifts), or RPE top set with back-off sets (advanced lifters and meet prep) (ev: 19204579, 36199287, 35038063)
- **P-14** [M] Programs longer than 6 weeks include planned variation in volume, intensity or both. The model is justified by the lifter's calendar or goal, never by a claim that it is superior (ev: 35044672, 28497285, 41843416, 25268290)
- **P-15** [P/W] A deload is planned every 4 to 8 weeks, or taken when the log shows performance falling. It reduces volume by 30 to 50%, keeps RIR at 3 or more, and keeps the same frequency and exercises. The L-7 main-lift deload (warm-up only) is the accepted house exception under M4 (ev: 38499934, 37730925, 38274324)
- **P-16** [M] The session's priority lift comes first (ev: 32077380, 41843416)
- **P-17** [M] Full range of motion by default, with lengthened-position emphasis for hypertrophy. Short-length partials are never the primary hypertrophy stimulus (ev: 34170576, 39959841, 33977835, 37015016)
- **P-18** [M] Rest is at least 2 to 3 min for strength sets (3 to 5 min on heavy compounds), at least 90 s for hypertrophy compounds and at least 60 s for isolation. Supersets are allowed when the session is time-limited (ev: 28933024, 39205815, 34125411, 19204579)
- **P-19** [M/P] Warm-ups ramp to the first working load of each main pattern. No static hold of 60 s or more comes right before heavy lifting unless dynamic work follows it (ev: 25694615, 26642915, 39864808, 34125411)
- **P-20** [P] True 1RM testing happens only at meets, mock meets or the end of a PEAK block. Everywhere else, use an e1RM or TM test (ev: 32681399)
- **P-21** [M] Female lifters get the same volume, intensity and percentage-to-reps assumptions. Loads and volume are not reduced by default (ev: 40028215, 32218059, 37792272)
- **P-22** [M] If velocity-based training is used, it only decides when a set stops. A daily squat or deadlift 1RM is never estimated from a load-velocity profile (ev: 29466270, 38088936, 36301878)
- **P-23** [M] A draft never claims that training to failure is required, that one periodization model is superior, that "5 to 10 sets is optimal" (the source was retracted), that autoregulation is clearly superior, or that MEV or MRV are measured values (ev: 33497853, 41843416, 35038063)

## W. Measurement (The Window)

- **W-1** [H/P] Every strength lifter starts from a measured number, never a guess: a 3RM (club), or a 2 to 8-rep benchmark under L-2. When neither exists, the lifter does a benchmark session: bar × 20, then 40% × 6, 50% × 4, 65% × 2, 70% × 2 and 80% × 1 of an estimated e1RM, then one set of 3 to 5 at RIR 1 to 2 (RIR 3 for novices and returning lifters, with TM at 85%). No single above 90% of e1RM is planned outside P-20's cases (ev: 32681399)
- **W-2** [H] Every AMRAP top set is logged, turned into an e1RM under L-12 and shown to the lifter as the block-to-block measure of their progress
- **W-3** [H/P] A program longer than one block closes with a re-test. By default that is an e1RM or TM test (a prime week at 70% × 3, 80% × 2, 87.5% × 1, 92.5% × 1 of TM, then an AMRAP or rep-max test), reported as the change against the starting e1RM. A max-attempt test week is used only at the end of a PEAK block or when the lifter asks (P-20) (ev: 32681399)
- **W-5** [D] A main lift with no benchmark gets a week-1 benchmark session under W-1. Weeks 2 onward for that lift are computed from its result and issued under IL-20 before the lifter's week-2 session. The draft never fills the gap with a guessed load (G-11)

> Note: W-3 reconciles two sources. The house test week builds to a max attempt, and the evidence rule keeps true 1RM tests for meets and PEAK blocks. The default is the e1RM test, and the max attempt needs the lifter to ask for it.

## O. Two blocks at once (OO)

`draft --two-blocks` writes an 8-week program in one go, for a lifter who won't come back after week 1. Nothing can be re-issued from a result the skill never sees, so these rules apply.

- **OO-1** [POL] A two-block program is 8 weeks: two 4-week blocks drafted and checked together, taking the lifter's next two block numbers (IL-2). Both files are handed over together
- **OO-2** [D] Two blocks are drafted only on a template with 4-week blocks whose loads never wait for a re-issue: `531-4day`, `531-2x`, `531-club`, `adf-prep` or `pt-general`. `topset-backdown` (a meet prep is planned one block at a time, with attempts chosen near the meet) and `hypertrophy-rotation` (6-week blocks) are refused
- **OO-3** [D] Every main lift needs a benchmark set under L-2 before drafting. A W-1 benchmark session or a CT-RGO-14 untested 3RM can't start a lift, because block 2 is written before week 1 is trained (W-5, IL-20). Without a set, ask the lifter for one (G-11), draft one block, or draft `pt-general`
- **OO-4** [H] {M28} Block 2's TMs are block 1's plus the L-9 standard increment, drafted in advance. The lifter applies L-9 themselves: a lift with any block 1 AMRAP below its minimum reps repeats its block 1 loads, week for week, through block 2
- **OO-5** [D] The hand-over states the check: block 1's AMRAP reps decide block 2's weights, and before block 2 starts the lifter compares each main lift's block 1 AMRAPs with their targets (the `self_check` in block 2's program.json)
- **OO-6** [D] On a double-progression template, block 2 repeats the layout and the lifter carries on from their own block 1 loads under A-6. CT-NOV-1's week 1 and 2 floor is block 1's only. Block 2's AMRAPs stand in for W-3's closing re-test, so no test week is added
