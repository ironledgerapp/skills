# Lifter types

These are the drafting rules for each lifter type: how the skill picks a primary type, its modifiers and a template from the lifter's answers, and what each type's draft must contain on top of the general rules. The general programming rules live in `rulebook.md`, red flags live in `rulebook.md` (RF), and none of them is repeated here. A rule tagged `{Mnn}` follows the recommended option of that method decision.

Built 2026-09-23. Rule IDs are stable: never renumber; retire a rule with ~~strikethrough~~ and a dated note.

> Note: Conflicts with rulebook rules are settled by G-20.

## Selection table

Every lifter gets exactly one primary type (the first nine rows) and any number of modifiers (the last four). Modifiers change doses inside the primary type's template. They change the template only where CT-NOV-2 says so.

| Type | Template id | Default days | Key parameters |
|---|---|---|---|
| Powerlifter, off-season (CT-PLO) | `531-2x` (M1 variant) | 4 | Each competition lift at least 2× a week: one 5/3/1 exposure plus a lighter FSL-style one (M1); competition standard in every block |
| Powerlifter, meet 12 weeks out or less (CT-PLM) | `topset-backdown` (M10) | 4 | Top-set range + RPE target, written as RIR (CT-PLM-20); back-downs at about 88% of the midpoint; PREP 2 (4 loading weeks + deload), then PEAK with no deload; 7 to 10-day taper; OPENER and SECOND chosen with the ironledger-meet-attempts skill |
| Rugby, off-season or pre-season (CT-RGO) | `531-club` | 3 (2 to 4) | 5/3/1 main lifts reaching 80% of e1RM in every wave week (CT-RGO-1); sprints 1× and Nordics 2× a week; Activate 3× a week; neck 2× a week; Limber 11 (M20) |
| Rugby, in-season (CT-RGI) | `531-club`, in-season rules | 1 to 2 | 1 to 3 sets of 3 to 5 per main lift at 80 to 85% of e1RM, at RIR 3; no AMRAP and no 5/3/1 wave; main session on MD+2 or MD+3 |
| ADF candidate (CT-ADF) | `adf-prep` (M18) | 5 to 6 (2 to 3 strength, 3 run) | Named role standard + buffer; interval-heavy, capped running; push-up and sit-up practice 3 to 4× a week; mock PFA every 3 to 4 weeks |
| Under 18 (CT-JUN) | none | none | Refused: heavy lifting for under-18s needs a qualified coach's supervision (CT-JUN-3) |
| General strength (CT-GEN) | `531-4day` (`531-2x` for a lift target) | 4 (2- and 3-day layouts) | One main lift per day is fine (M1); every pattern at least 2× a week through accessories |
| Hypertrophy (CT-HYP) | `531-4day`; `hypertrophy-rotation` only with 5 or more days (CT-HYP-6) | 4; or 3 on, 1 off | Rep phases (M14) or hard-set accessories (CT-HYP-2); RIR 0 only on machine and isolation work |
| General PT and injury-aware (CT-PT) | `pt-general` | As the lifter says (usually 3) | 5 to 6 exercises × 3 sets at RIR 1 to 2; injury-driven variations with a reason; mobility-block warm-up (M20) |
| Novice, returning or 60+ (CT-NOV, modifier) | Primary type's template; `pt-general` for GEN or HYP novices | 2 to 3 | Weeks 1 and 2 at RIR 3 or more; TM 85% (L-3); older adults at least 2 sessions a week |
| Female (CT-FEM, modifier) | Primary type's template | As primary type | Same assumptions (P-21); no cycle-phase periodisation; RED-S screen |
| Concurrent goals (CT-CON, modifier) | Primary type's template | As primary type | Lift first or at least 6 h apart; fat loss keeps the top sets |
| Running add-on (CT-RUN, modifier) | Primary type's template + run sessions | Primary type + 1 to 3 runs | 2.4 km pacing tool; weekly running minutes rise 30% or less; no 10% rule |

## Selecting the type

- **CT-SEL-1** [D] Every draft states one primary type (PLO, PLM, RGO, RGI, ADF, JUN, GEN, HYP or PT), every modifier that applies (NOV, FEM, CON, RUN), the template id, one alternative template, and the signal from the lifter's answers behind each choice
- **CT-SEL-2** [D] The primary type is the first match in this order: (1) age under 18: JUN, which is refused (CT-JUN-1); (2) ADF role named and a PFA date 12 weeks away or less: ADF; (3) a powerlifting meet 12 weeks away or less: PLM; (4) rugby or another field sport with season dates: RGI if any week of the block falls in the competition season, otherwise RGO; (5) a competing or intending powerlifter: PLO; (6) a goal stated as size, physique or bulk: HYP; (7) an injury or limit that changes a main-lift pattern, or a goal of general fitness or wellbeing: PT; (8) otherwise: GEN

> Note: Dated events and safeguarding come first because they constrain everything else. A lifter whose limit touches only an accessory stays in their goal type; the CT-PT drafting rules and the rulebook's pain rules (RF-9 to RF-11) still apply to them.

- **CT-SEL-3** [D] Modifiers: NOV when consistent training age is under 6 months, the lifter is returning from a break of more than 3 weeks, or the lifter is 60 or older; FEM when the lifter is female; CON when the lifter names a second goal (fat loss, a running event, endurance or hybrid fitness); RUN when the draft contains any running or conditioning session
- **CT-SEL-4** [D] A lifter who fits two primary types: the type with the nearer dated event (meet, PFA or first match) leads, and the other goal gets the maintenance dose in CT-GEN-4. With no dated event, the lifter's stated main goal leads. If two dated events fall inside the same 12-week window (for example a meet during the rugby season), the skill drafts neither peak and asks the lifter to choose (ev: 33629972)
- **CT-SEL-5** [D] Weeks to an event are counted in whole weeks from the block start. Meet: more than 12 weeks out is PLO until 12 weeks out; 8 to 12 weeks is a full PLM prep; under 8 weeks drafts only PEAK and the taper and flags "short prep" to the lifter. PFA: more than 12 weeks out is the base type plus a CT-RUN aerobic base, with the role standard recorded; 12 weeks out switches to `adf-prep`; under 8 weeks is flagged "short prep"
- **CT-SEL-6** [D] Rugby phases come from the lifter's season calendar: pre-season runs from the start of team pre-season training to the week before the first competition match, in-season from that match to the last one, and off-season is the rest. A block that crosses the first match switches to CT-RGI rules from that week
- **CT-SEL-7** [D] Training days come from the lifter's answers and are never exceeded. Fewer days than the template default use that template's reduced-day layout (CT-GEN-2, CT-RGO-2), never a squeezed 4-day week. A template without one, or a lifter with 1 day, is refused, with CT-GEN-3 named as the time-minimum approach. Sessions under 45 min use CT-GEN-3 (ev: 34125411)
- **CT-SEL-8** [D] Equipment: `531-4day`, `531-2x`, `531-club`, `topset-backdown` and `adf-prep` need a barbell, rack, bench and plates. Without them the lifter goes to `pt-general`, with each substitution taken from the exercise library and noted with its reason
- **CT-SEL-9** [POL] Anyone under 18 is refused (CT-JUN-1)


## Powerlifter: off-season (CT-PLO)

The squat bar position follows L-17, and ACWR is barred by G-13.

- **CT-PLO-1** [M] {M1} Template `531-2x`: each competition lift is trained at least 2 times a week, as one 5/3/1 main exposure plus one lighter exposure of the same lift or a close variant (FSL-style, 3 to 5 sets × 5 at that week's first-set % of TM). Bench may go to 3 times a week, and deadlift's second exposure may be a variant (ev: 41343037, 37414459, 29470825, 41843416)

> Note: Three exposures a week are preferred for intermediate and advanced lifters; M1 B sets 2 as the floor, and bench is where a third fits best. The second exposure is lighter by design, so the >80% load the research asks for comes from the main exposure in 5/3/1 weeks 2 and 3 (90% and 95% of TM, about 81% and 86% of e1RM with TM at 90%). Week 1's top set is 85% of TM, about 76% of e1RM, so it does not supply that load.

- **CT-PLO-2** [S/W] Competition lifts are trained to competition standard in every block, off-season and meet prep alike. Variants and accessories rotate per block (every 4 to 8 weeks), never per session (ev: 40314751, 35438660)
- **CT-PLO-3** [M] A competition lift the lifter is maintaining rather than prioritising in a block still gets at least 1 set of 6 to 12 reps at about 70 to 85% 1RM, 2 to 3 times a week (ev: 31797219)
- **CT-PLO-4** [M] Pain on any lift is asked about (0 to 10) before drafting, and the lift is modified under rulebook RF-10 and RF-11, not dropped by default (ev: 33632313, 17307888, 29785405)
- **CT-PLO-5** [M] Conditioning in a PLO draft follows CT-CON-4, and running is capped by frequency and session length before any lifting intensity is cut, as CT-CON-5 sets out (ev: 28783467, 25546450, 22002517)
- **CT-PLO-6** [P] The draft shows each competition lift's TM beside its source set (weight × reps and date). When the lifter has a meet result, the hand-over shows it beside the e1RM so the lifter can calibrate the TM (ev: 16937972)
- **CT-PLO-7** [W/M] A planned break of 3 weeks or less costs at most 5% of TM on return. Longer breaks follow CT-NOV-4 (ev: 23053130)

## Powerlifter: meet prep (CT-PLM)

Meet prep starts 12 weeks out (CT-SEL-5). CT-PLO-2 and CT-PLO-4 still apply. The taper rules CT-PLM-7 to CT-PLM-11 apply whichever template is used.

- **CT-PLM-1** [P] {M10} Template `topset-backdown`: each competition lift gets one top set written as a load range (10 kg wide for squat and deadlift, 5 kg for bench) with an RPE target, then 2 to 3 back-down sets at one fixed load
- **CT-PLM-2** [M/D] {M10} A lifter with under 4 weeks of logged RPE or RIR ratings stays on a 5/3/1 template through meet prep, with `topset-backdown` offered as the alternative. The default for how that route peaks: in the 3 weeks before the taper, the main lift is scripted singles at 85, 90 and 92.5% of e1RM, one step a week, each at RIR 1 or more (ev: 28301439, 26049792)
- **CT-PLM-3** [M/D] The week 1 top-set range of each block is centred on the load the scripts derive from the lifter's current e1RM for that block's reps at its RPE target, using an RPE chart. Weeks 2 to 4 are computed at generation by raising the range midpoint by the template's weekly step. The RIR target autoregulates within the range. Logged top sets change later weeks only through the lifter's decision and an IL-20 re-issue (ev: 27243918)
- **CT-PLM-4** [P] {M10} The back-down load is the top-set range midpoint × 0.85 to 0.87 in 6 to 8-rep blocks, × 0.88 to 0.89 in 3 to 5-rep blocks and × 0.91 to 0.93 in PEAK, rounded per L-4 and computed by the scripts
- **CT-PLM-5** [P] {M10} Inside each block, reps fall and the top-set RPE target rises about 0.5 a week (for example 7.5, 7.5 to 8, 8, 8 to 8.5). The target stays at RPE 9 or below outside PEAK (ev: 38970765)

> Note: The rulebook caps main strength lifts at RPE 9 outside test and peak singles (P-10), so PREP blocks keep the cap and PEAK carries the heavier singles.

- **CT-PLM-6** [P] {M10} Blocks before PEAK are 4 loading weeks plus a deload of 2 to 3 sets × 3 at RPE 6 to 7 with no back-downs. PEAK (2, then 1, then OPENER) is 3 to 4 weeks with no deload and runs straight into the CT-PLM-8 taper. An 8 to 12-week prep is PREP 2 (3 to 1 or 2 reps), shortened as needed and flagged to the lifter when shortened, then PEAK. DEVELOPMENT, TECH and STRENGTH belong to CT-PLO

> Note: M11's 3 + 1 block (L-8) governs the 5/3/1 templates. This template keeps 4 + 1 so that the week 4 accessory step in CT-PLM-13 exists; M8 was chosen to keep each style whole.

- **CT-PLM-7** [W] Weekly volume peaks 4 to 8 weeks out, and intensity peaks 2 to 3 weeks out (ev: 26670988, 34846328, 42611173)
- **CT-PLM-8** [W] The taper is a 7 to 10-day step taper that cuts volume by 40 to 60% and keeps intensity (ev: 26670988, 34846328, 42611173, 30204523)
- **CT-PLM-9** [W] The last heavy (>85%) squat and deadlift fall 7 to 10 days out and the last heavy bench under 7 days out, with final heavy singles at about 90 to 92.5% 1RM. The last session of any kind falls 6 to 8 days out for deadlift (at about 70 to 75%), 5 to 6.5 days out for squat and 3 to 5 days out for bench, both at about 75 to 80% (ev: 34846328, 42611173)
- **CT-PLM-10** [W] Complete rest before the meet is 2 to 4 days, with the final session about 2.8 to 3.7 days out. No plan has 7 or more days off before a meet (ev: 26670988, 34846328, 42611173)
- **CT-PLM-11** [W] Accessories stop about 2 weeks out, leaving the competition lifts and close variants. Taper sessions use competition equipment and commands (ev: 26670988)
- **CT-PLM-12** [S] Every week of the PREP 2 and PEAK blocks (and of a CT-PLO STRENGTH block) has at least 1 exposure per competition lift at 80% 1RM or more, or at 5 reps or fewer at RPE 8 or more (ev: 41843416, 37414459, 33433148, 28834797)
- **CT-PLM-13** [P] {M8} Accessory RIR in this template is set against the week 1 base: weeks 2 and 3 at 0.5 below it, week 4 at 1 below it, never below 0, and the deload at 1 above it and at RIR 3 or more. Half-step values are written as ranges under CT-PLM-20. Most accessories get 2 sets

> Note: A-4 summarises this as a 0.5-a-week step down. The offsets above ("week 3 same as week 2") are what the scripts apply.

- **CT-PLM-14** [P] {M10} PEAK-week cells for the competition lifts read "OPENER" and "SECOND" in place of loads, and the designer never fills them; the lifter chooses them with the ironledger-meet-attempts skill
- **CT-PLM-15** [POL] Attempt selection is not part of the training program. The meet attempts themselves are planned with the ironledger-meet-attempts skill, from published federation rules and coaching ranges

> Note: The training program leaves OPENER and SECOND out (M10); the meet attempts skill plans them.

- **CT-PLM-16** [W] The hand-over states that peaking evidence is mostly self-report and trial and error. When a log from a previous meet exists, it shows that taper's timing beside the defaults (ev: 32917000)
- **CT-PLM-17** [M] The draft records the federation, the weigh-in timing (2 h or 24 h, confirmed from the meet pack every time), the class limit and the latest 7-day mean bodyweight (ev: 41320256)
- **CT-PLM-18** [M] If the 7-day mean bodyweight about 2 weeks out is more than 3% above the class limit (5% for a lifter with a previous cut on record), the hand-over lists "change class" as an option. It lists the options and never recommends one (G-2) (ev: 41320256)
- **CT-PLM-19** [POL] This skill never plans a weight cut and never prescribes fluid, sodium or sweat manipulation. A lifter planning a cut works with a coach or sports dietitian. A cut mentioned with an eating-disorder or RED-S sign is raised as an RF-14 red flag (ev: 41320256)
- **CT-PLM-20** [D] {M10} In the import, each RPE target is written as RIR = 10 − RPE, and a half value becomes a range (RPE 7.5 is `2-3`; RPE 8 to 8.5 is `1-2`). CT-PLM-13's half-steps round the same way. A top set's import Load is the lower bound of its range, as a number, with `Top set 175-185` in Notes. OPENER and SECOND rows stay out of the import until the lifter fills them in, and the block is then re-issued under IL-20

## Rugby: off-season and pre-season (CT-RGO)

These rules cover rugby union, rugby league and other field sports.

- **CT-RGO-1** [M] {M19} Template `531-club`: at least 2 strength sessions a week (target 3) built on 5/3/1 main lifts. Weeks 2 and 3 of the wave reach at least 80% of e1RM. Week 1 adds one set of 3 at 80% of e1RM after the AMRAP, or the hand-over states that week 1 sits at about 76% (ev: 37414459, 21873897, 20072043)
- **CT-RGO-2** [D] Reduced-day layouts keep one 5/3/1 exposure per main lift: 2 days are squat + bench, then deadlift + OHP; 3 days add a short upper-body, power and sprint session
- **CT-RGO-3** [M] Lower-body strength (a squat pattern, a hinge and unilateral leg work) is a primary target in every block (ev: 25059334)
- **CT-RGO-4** [M] Max-velocity sprinting happens at least once a week, before lifting or on a non-lifting day. Sleds are optional for acceleration and never replace unresisted sprints (ev: 29926369)
- **CT-RGO-5** [S/W] The Nordic hamstring exercise (or a regression) is done at least 2 times a week, introduced progressively and built to about 29 to 64 reps a week. More than 64 is only for proficient athletes (ev: 30808663, 31502142, 40991853)
- **CT-RGO-6** [M] {M19} An Activate-style neuromuscular warm-up (World Rugby Activate or equivalent, about 25 min for adults and 20 min for youth) happens at least 3 times a week in every phase, counting team trainings. Where the team does not run it, the gym sessions do. If there are fewer than 3 exposures a week, the hand-over says so; no day is added (ev: 28515056, 29055883, 37316182)
- **CT-RGO-7** [H] {M20} Rugby gym sessions open with Limber 11. It does not count toward CT-RGO-6, and it is labelled mobility preparation

> Note: Limber 11 is foam rolling, mobility drills and short stretches. It has none of Activate's running, balance, landing and neck parts, which carry the injury and concussion effects, so M19's Activate and M20's Limber 11 are both kept.

- **CT-RGO-8** [S] No draft for any lifter type labels static stretching as injury prevention. Mobility work is labelled as range or preparation (ev: 10694106, 24100287)
- **CT-RGO-9** [M] Conditioning includes repeated high-intensity efforts with decelerations. Forwards get more collision and strength-biased work (including contact or wrestle conditioning when the team program lacks it), and backs get more high-speed running (ev: 31506901, 35050440, 26714810, 32497130)
- **CT-RGO-10** [M] {M19} Hard conditioning comes after lifting in the same session, or at least 6 h away from it. Conditioning less than 6 h before lifting is never scheduled (ev: 28783467, 25546450, 34757594)
- **CT-RGO-11** [W/P] Neck work (isometric or dynamic) is done 2 times a week and labelled as performance and robustness work, never as concussion prevention (ev: 37428807, 40345809)
- **CT-RGO-12** [M] Jumps, throws, Olympic-lift derivatives, supplemental sets and every strength set other than the 5/3/1 AMRAP stop at 20 to 25% velocity loss or at RIR 3 or more (ev: 36178597, 35038063, 32049887)
- **CT-RGO-13** [D] {M19} Off-season and pre-season 5/3/1 AMRAP sets stop at RIR 2, cued "leave 2 in the tank" (ev: 36178597)

> Note: A stricter rule would have power athletes stop strength sets at RIR 3 or more; the house AMRAP cue (L-13) allows 1 to 2 in the tank, and M19 keeps 5/3/1 with AMRAP-driven TMs off-season. RIR 2 is a default, to tune.

- **CT-RGO-14** [H] The club program's week 1 is technique plus a 3RM benchmark on each main lift. A 3RM the lifter reports is used only when they confirm it was tested
- **CT-RGO-15** [H] Club drafts assume a basic club gym and never go beyond it: barbells, racks, benches, dumbbells and a dip attachment, with no machines, cables or pull-up bar. The lifter's own equipment list narrows it further (G-15)

## Rugby: in-season (CT-RGI)

CT-RGO-6, CT-RGO-7, CT-RGO-8, CT-RGO-11 and CT-RGO-12 continue in-season, and G-13 bars ACWR.

- **CT-RGI-1** [M] {M19} At least 1 strength session every week, and 2 for players with under about 2 years' training age or a goal to improve. A week with none (a bye or a double fixture) needs a stated reason and never happens 2 weeks in a row (ev: 21873897, 33629972, 19620903)

> Note: The research ranges from every week to tolerating one missed week. The rule takes the stricter default and allows one stated exception.

- **CT-RGI-2** [M] {M19} Each major movement gets 1 to 3 hard sets at 80% 1RM or more, each stopped at about RIR 3 or at 20 to 25% velocity loss (ev: 33629972, 21131862, 36178597)

> Note: One rule asks for at least 80% 1RM or RIR 3 or closer, and another asks power athletes to stop at RIR 3 or more. Heavy loads stopped at about RIR 3 satisfy both.

- **CT-RGI-3** [D] In-season drafts have no AMRAP sets, and TMs are held until the off-season unless the lifter raises them
- **CT-RGI-4** [M] {M19} Volume goes before intensity: supplemental work is cut first, then accessories, and top-set loads are kept (ev: 33629972)
- **CT-RGI-5** [M/P] No heavy or eccentric lower-body lifting on MD+1. The main strength session falls 48 to 72 h or more after the last match and at least 48 h before the next. For a Saturday match: Sunday recovery or off, the main session on Monday or Tuesday, a short upper-body and power session on Wednesday or Thursday with no heavy eccentric lower-body work, and Friday a primer or off (ev: 33003172)
- **CT-RGI-6** [S/M] The Nordic hamstring exercise is done at least once a week at a low dose (ev: 30808663, 31502142)
- **CT-RGI-7** [P] The weekly plan lists team training and collision load. In a high-contact week, lifting volume drops first (ev: 35050440, 31970529)
- **CT-RGI-8** [POL] No rugby draft contains a return-to-contact decision. After a suspected concussion (rulebook RF-12), the draft holds contact-related and heavy work until a clinician's clearance, and may include only the light-exercise stage of a graded return, after medical input (ev: 37316210)
- **CT-RGI-9** [P] The draft names its monitoring markers (top-set RIR or bar speed, the weekly wellness ratings, and CMJ where available) so the lifter can move load within their week-to-week range (ev: 33003172, 42390026)
- **CT-RGI-10** [D] {M19} In-season main lifts are 1 to 3 sets of 3 to 5 at 80 to 85% of e1RM (the held TM ÷ 0.9, or ÷ 0.85 where L-3 set the TM at 85%), each at RIR 3, with no 5/3/1 wave in-season

## ADF candidates (CT-ADF)

Role standards from <https://adfcareers.gov.au/careers/joining/fitness-requirements>, fetched 2026-09-23. The page shows no "last updated" date. Sit-ups are done with the feet held.

| Service and role | Sit-ups | Push-ups | Shuttle (beep) level | Other |
|---|---|---|---|---|
| Army: General Entry Combat and Officer Entry | 45 | M 15, F 8 | 7.5 | |
| Army: Combat Support and Specialist Service Officer | 20 | M 8, F 4 | 6.1 | |
| Army: Graduate, Postgraduate and Undergraduate Officer | 20 | M 8, F 4 | 6.1 | |
| Army: Special Forces | 60 | 40 | 10.1 | 6 over-grasp heaves |
| Air Force: general roles | 20 | not tested | M 6.1, F 5.1 | |
| Air Force: Security Forces Officer | 20 | 10 | 6.5 | |
| Air Force: PTI | 30 | M 20, F 10 | 9.5 | |
| Navy: Diver | 25 | 30 | 10.1 | |
| Navy: PTI | 25 | M 25, F 20 | M 10.1, F 8.5 | |
| Navy: all other roles | no PFA | | | In-service tests during initial training: 2.4 km run, shuttle, 1-min forearm plank, swim (male under 29: shuttle 7.4, 2.4 km under 13:00) |

> Note: M18 supplies the ADF rules, and they follow its recommended option. Conditioning placement follows CT-CON-4, and running follows CT-RUN.

- **CT-ADF-1** [POL] {M18} The draft names the service, the role and the exact PFA standard from the ADF Careers fitness-requirements page with its fetch date, plus the PFA date. The plan peaks for the PFA, which can fall up to 12 weeks before enlistment, not for the enlistment date
- **CT-ADF-2** [D] The ADF standards change. Before using them, tell the lifter to check the current ADF Careers page for their role
- **CT-ADF-3** [POL] Navy roles other than Diver and PTI need no PFA. The draft says so, and targets the in-service initial-training tests only if the lifter asks
- **CT-ADF-4** [P] {M18} Targets beat the standard: at least 1 shuttle level above it and about 25% more push-ups and sit-ups than required, rounded up (ev: 10544625, 10694106, 11404660)
- **CT-ADF-5** [P] {M18} The weekly frame is 5 to 6 days: 3 run days (one 200 to 800 m interval session, one shuttle-specific session with 20 m turns at test pace, and one easy 20 to 40 min run) and 2 to 3 strength days (ev: 26243014)
- **CT-ADF-6** [P/W] {M18} Push-ups and sit-ups are practised to the exact test technique 3 to 4 times a week, as short sets or finishers stopped 2 to 3 reps short of failure. Incline push-up regressions are used until the lifter can meet the standard, and one timed or max test to the exact standard happens each week (ev: 24983847, 29466268)
- **CT-ADF-7** [POL] Practice cues follow the PFA brochure and are marked "confirm with Defence Force Recruiting". Push-ups: feet no more than 30 cm apart, body straight from shoulders to ankles, upper arms parallel to the ground at the bottom, no resting on the ground. Sit-ups: knees at 90°, feet held, hands sliding up the thighs until the wrists touch the knees, shoulder blades to the floor; Army candidates may rest the head between reps, Navy and Air Force candidates may not
- **CT-ADF-8** [POL] Unverified test details (push-up and sit-up cadence or time limit, and the beep-test version) are flagged "confirm with Defence Force Recruiting" in the draft, and shuttle scores are never converted to VO2max in lifter text (ev: 3184250)
- **CT-ADF-9** [M] {M18} 2 to 3 strength sessions a week on 5/3/1 main lifts include a squat, a hinge, pull-ups (mandatory for Special Forces), a lift to a platform and loaded carries (ev: 39952091)
- **CT-ADF-10** [M] Load carriage is optional before entry. If included, it is at most 1 session every 10 to 14 days, and it progresses speed, gradient and terrain before load (ev: 33920426, 26506174)
- **CT-ADF-11** [P] {M18} A mock PFA to the exact standard runs before the program starts (week 0) and every 3 to 4 weeks. The last hard session falls 7 to 10 days before the PFA, followed by a taper that cuts volume by 40 to 50% and keeps intensity
- **CT-ADF-12** [P] If a mock PFA stalls while soreness or pain markers rise, running volume is cut first
- **CT-ADF-13** [M/D] Female candidates: weekly running minutes rise by 20% or less, strength work is emphasised, and the CT-FEM-4 questions are asked before every block (ev: 10332180, 11404660, 28986086, 24563388)
- **CT-ADF-14** [P] Special Forces candidates add pull-up (heave) practice at least 3 times a week and more aerobic volume, under the same running caps
- **CT-ADF-15** [P] A candidate far below the standard at the baseline mock PFA is shown the Army Pre-Conditioning Program (Army General Entry) and the UniSport S&C sessions as options. APCP entry minimums are brochure-sourced and marked "confirm with Defence Force Recruiting"
- **CT-ADF-16** [POL] A BMI outside 18.5 to 32.9 (Army and Air Force) is flagged to the lifter as an entry issue, and any nutrition work goes to the ironledger-nutrition-plan skill

## Under 18 (CT-JUN)

- **CT-JUN-1** [POL] No program is drafted for anyone under 18
- **CT-JUN-3** [M] Heavy or technical lifting for under-18s happens only in sessions supervised by a qualified coach, which a self-serve program can't provide; that is why CT-JUN-1 refuses (ev: 24055781)

## General strength (CT-GEN)

The engine, accessories and volume rules are in `rulebook.md`, the warm-up is CT-PT-2, and fat-loss or running co-goals add CT-CON.

- **CT-GEN-1** [M] {M1} One 5/3/1 exposure per main lift a week is acceptable for general lifters, but every major muscle group and movement pattern is trained at least 2 times a week, with accessories supplying the second exposure, for example a squat pattern on deadlift day and a press on bench or OHP day (ev: 37414459)

> Note: The research asks for 2 exposures per pattern, and M1 keeps one main-lift exposure for general lifters. Counting the pattern rather than the barbell lift satisfies both.

- **CT-GEN-2** [D] Reduced-day layouts keep one 5/3/1 exposure per main lift: 3 days are squat + bench, deadlift + OHP, then a full-body accessory day; 2 days are squat + bench, then deadlift + OHP
- **CT-GEN-3** [W/M] The time-minimum plan (sessions under 45 min, or where CT-SEL-7 offers it) covers a squat or leg-press pattern, an upper push and an upper pull each week, with at least 4 sets per muscle a week at 6 to 15RM. Warm-ups are exercise-specific only, and supersets are allowed (ev: 34125411)
- **CT-GEN-4** [M] The maintenance dose (travel, busy weeks, or the non-lead goal under CT-SEL-4) is at least 1 session a week with 1 to 3 hard sets per major movement at 80% 1RM or more, or at RIR 3 or closer (ev: 33629972, 21131862, 31797219)
- **CT-GEN-5** [D] {M1} A general lifter whose main goal is a strength number on a barbell lift gets `531-2x`; other general lifters get `531-4day` (ev: 41343037, 37414459)

## Hypertrophy (CT-HYP)

Volume, rep ranges, RIR bands and rest are in `rulebook.md` (P-3 to P-10). Supplemental work after 5/3/1 main sets follows L-14: hypertrophy-leaning lifters get FSL plus the CT-HYP-2 hard-set accessories, and BBB only when the lifter asks for it, with sets prescribed to end at RIR 2 or closer.

- **CT-HYP-1** [H] {M14} Template `hypertrophy-rotation`: 3 days on and 1 off (Lower, Push, Pull, rest), with the rep and RIR phase changing every 2 rotations: 13 to 15 at RIR 3, then 10 to 12 at RIR 2, then 5 to 6 at RIR 0 under CT-HYP-3
- **CT-HYP-2** [H] The alternative is `531-4day` with hard-set accessories: 5/3/1 main lifts, then 2 hard sets of 6 to 10 at RIR 0 on 1 or 2 compounds (under CT-HYP-3), then 3 sets × 10 to 12 at RIR 2 to 3, with "AMRAP Last Set" and "Full ROM" notes
- **CT-HYP-3** [M] RIR 0 sets in CT-HYP-1 and CT-HYP-2 go only on machine, cable, supported or isolation exercises. A free-weight compound in one of those slots stops at RIR 1 (ev: 38970765, 36334240, 38393985)

> Note: Some hypertrophy programs put compounds at RIR 0. The rulebook keeps free-weight compounds at RIR 1 to 3 (P-10) and bars planned failure on them at 85% 1RM or more (A-7), so the designer moves the failure sets to exercises where failure is safe.

- **CT-HYP-4** [D] The draft names 2 to 4 priority muscles from the lifter's focus areas, and every other muscle counts as non-priority under P-3
- **CT-HYP-5** [H] {M14} The Saturday 10 × 10 volume day is retired unless the lifter asks for it
- **CT-HYP-6** [D] {M14} `hypertrophy-rotation` is offered only to lifters with 5 or more available days, written as one rotation per Week (Days 1 to 3) in the import. Otherwise the draft uses CT-HYP-2

## General PT and injury-aware lifters (CT-PT)

CT-PT-4 to CT-PT-7 apply to every lifter type. Pain thresholds, red flags and pathways during a block are in rulebook.md (RF-5 to RF-18), and diagnosis is barred by G-10.

- **CT-PT-1** [H] Template `pt-general`: days and session length exactly as the lifter states, and 5 to 6 exercises × 3 sets a session at RIR 2 on compounds and RIR 1 on isolation (RIR 3 on core and mobility work), finishing with a carry or a core exercise
- **CT-PT-2** [H] {M20} The warm-up for PT, general, hypertrophy and novice lifters is 5 min on a rower or bike, three 1-set mobility drills matched to the day's pattern, then "Shoulder Big 3" (Prone T, Palms Up, Palms Down) 1 × 15 each
- **CT-PT-3** [H/M] An injury or limit the lifter lists changes only the movements it aggravates, and every pain-free pattern stays in. Each swap names its training reason in Notes, for example a trap-bar deadlift to reduce lower-back shear, a box squat for a controlled knee depth, or a reverse lunge or high-foot leg press to reduce knee stress (ev: 27226389)
- **CT-PT-4** [POL] The G-4 screen is APSS Stage 1, with any yes answer resolved by a health professional's guidance. A draft for a lifter with known osteoporosis, pregnancy or a clinician-managed injury also needs that clearance or plan before it is built


- **CT-PT-5** [M/POL] Every hand-over carries this pain rule. 0 to 2 out of 10: train as planned. A known niggle at 3 to 5 that settles by the next morning: keep going, but don't add load to that movement. Stop that movement and see a physiotherapist or sports doctor for any of these: new pain above 3 during a lift, pain still there the next morning, pain above 5, pain getting worse week to week, swelling, a pop, or pain that changes how you move. It also carries the red-flag line: chest pain, fainting or new numbness means stop and get medical help (ev: 33632313, 17307888, 32438853)
- **CT-PT-6** [POL] For a clinician-managed injury, the draft follows the clinician's plan for the injured area and trains the healthy tissue around it, and return to sport is a shared decision with the clinician. No draft prescribes manual therapy, medication, supplements, an individual diet, or clinical exercise for a diagnosed condition beyond the clinician's plan (ev: 27226389)
- **CT-PT-7** [M] Sprinting is programmed only when it is pain-free; other movements may continue within the CT-PT-5 limits (ev: 28596288, 36650032)
- **CT-PT-8** [D] `pt-general` blocks are written week by week, with a named progression for every exercise (P-13). One week repeated for the whole block is not used

## Novices, returners and older adults (CT-NOV)

- **CT-NOV-1** [M] In weeks 1 and 2 of a novice's or returner's first block, every set stops at RIR 3 or more, with no sets to failure and no high-volume eccentric work (ev: 27782911)
- **CT-NOV-2** [M/D] A GEN or HYP novice (training age under 6 months) starts on `pt-general`, 2 to 3 full-body days a week at 8 to 12RM-equivalent loads. A 5/3/1 template is used only with a measured 2 to 8-rep benchmark on each main lift and at least 3 training days. Novices in other types keep their type's template with TM at 85% under L-3 (ev: 19204579, 37414459)
- **CT-NOV-3** [M] Novice RIR cues carry a margin ("stop at about RIR 3"), and working weights are checked against the reps actually done, not against self-rated RIR alone (ev: 34542869, 26049792)
- **CT-NOV-4** [M] {M7} Returning after a break: 3 weeks or less keeps the TM or drops it by up to 5%; more than 3 weeks and up to 6 months re-estimates the TM from a new benchmark set at 85%; more than 6 months runs the novice rules for 2 weeks, then re-estimates (ev: 23053130, 16937972, 23347054)

> Note: The research gives 80 to 85% for novices and returners, and M7 fixes 85% (L-3). It is silent between 3 weeks and 1 month, so the designer re-estimates there.

- **CT-NOV-5** [M] The draft tells a lifter returning after 1 to 6 months to expect prior strength back in about 6 to 8 weeks, and never says that "muscle memory" means old loads straight away (ev: 1827108, 32017951, 30991013)
- **CT-NOV-6** [M] Older adults (60 or older) train at least 2 sessions a week, starting at 2 to 3 sets of about 7 to 9 reps at 70 to 79% 1RM and progressing. A maintenance phase never drops below 2 sessions and 2 to 3 sets (ev: 26420238, 31343601, 33629972, 23347054)

> Note: The research draws the line at 60 or 65. The designer uses 60, so fewer lifters fall through.

- **CT-NOV-7** [M] Heavy loading (above 85% 1RM) for a lifter with known osteopenia or osteoporosis needs medical clearance and supervised technique progression first (ev: 28975661)
- **CT-NOV-8** [S] An older adult who is losing weight gets both resistance and aerobic training in the draft (ev: 28514618)

## Female lifters (CT-FEM)

The general rules in `rulebook.md` apply unchanged, including P-21: the same volume, intensity and percentage-to-reps assumptions, with no default reduction. Light lifters may use 1.25 kg steps under L-4.

- **CT-FEM-1** [M] No draft periodises load or volume around menstrual-cycle phase by default (ev: 32661839, 37033884)
- **CT-FEM-2** [P] Cycle symptoms are handled on the day through the RIR caps and the AMRAP, and noted in the log. A lifter who asks for phase-based training is shown the evidence summary, including the contrary reviews (ev: 32661839, 38251305, 35471634)
- **CT-FEM-3** [M] Oral contraceptive use changes nothing in the draft (ev: 32666247)
- **CT-FEM-4** [M] Every lifter, female or male, is asked about the signs of low energy availability in rulebook RF-14 before drafting, and a positive answer follows the RF-14 pathway (ev: 37752011, 37752002, 24563388)
- **CT-FEM-5** [P] While a RED-S signal is open, the training draft does not raise load and pauses body-composition goals. Participation then follows the clinician's CAT2 traffic light: green, yellow, orange or red (ev: 37752002, 37752011)

> Note: Some guidance acts on any positive signal and some refers on two or more. Rulebook RF-14 is the one list: it marks which signs act alone and which count toward 2, and CT-FEM-5 holds load from the moment an RF-14 flag is raised.

- **CT-FEM-6** [S] Female field-sport lifters get an ACL-focused neuromuscular program of about 20 to 25 min, 2 to 3 times a week in-season, built on lower-body strength (Nordics, lunges, calf raises) and landing stabilisation such as jump or hop and hold (ev: 29737024, 30001501)

> Note: Male collision-sport data are not carried over to women without checking (Dane 2022, PMID 35767989).

- **CT-FEM-7** [POL] For a lifter who is pregnant, no draft is built until she confirms clearance from her obstetric care provider. After that, the draft modifies training without making clinical decisions, keeps muscle strengthening on at least 2 days a week, and includes pelvic-floor exercises (ev: 35418334)
- **CT-FEM-8** [P/POL] Postpartum: no running, plyometrics or heavy loaded bracing work until the lifter confirms clearance from a pelvic-health physiotherapist and a GP. The return starts after the 6-week postnatal check and is gradual (ev: 28642221)

## Concurrent goals (CT-CON)

- **CT-CON-1** [M] Strength plus fat loss: the main-lift top sets and their loads stay, accessory volume is trimmed first if recovery suffers, and conditioning never replaces lifting (ev: 34623696)
- **CT-CON-2** [M] With a fat-loss co-goal, the hand-over states the ironledger-nutrition-plan skill's target loss rate (0.5 to 1% of body mass a week, 0.5 to 0.7% for lean or performance-focused lifters) and flags any deficit above about 500 kcal a day as costing lean mass (ev: 34623696, 21558571, 24864135)
- **CT-CON-3** [P/D] In a block where the nutrition plan cuts calories, weekly conditioning minutes rise by 20% or less
- **CT-CON-4** [M] Hard conditioning or hard runs and heavy or explosive lifting are placed in this order of preference: different days (24 h or more apart), at least 6 h apart, at least 3 h apart, or the same session with lifting first (ev: 25546450, 34757594, 28783467, 28917030)

> Note: One rule uses 3 h (Schumann 2022: the explosive-strength cost disappears at 3 h or more), and another uses 6 h, preferably 24 h (Robineau 2016, a rugby RCT). The ladder keeps both. Rugby is stricter under M19 (CT-RGO-10).

- **CT-CON-5** [M/D] Strength-first lifters who run have running frequency and duration capped before lifting intensity is touched. The default is 3 runs a week or fewer, with easy runs of 20 to 40 min (ev: 34757594, 22002517, 35476184)

> Note: "3 runs a week or fewer" is a default and not a finding of Wilson 2012 (22002517), which reports only that interference rose with running frequency and duration.

- **CT-CON-6** [M] Lifters whose main goal is running get 2 to 3 strength sessions a week, presented as a performance tool and not only as injury prevention (ev: 29249083)
- **CT-CON-7** [M] Hybrid lifters get one primary quality per block, and the others get a maintenance dose: strength under CT-GEN-4, and endurance at 2 or more sessions a week or with volume cut by 33 to 66% (13 to 26 min a session) while intensity is kept (ev: 33629972)
- **CT-CON-8** [M] The conditioning mode is chosen for the sport or goal. The draft never claims that a mode avoids interference, and makes no AMPK or mTOR mechanism claims (ev: 29658408, 27506998)

## Running and conditioning add-ons (CT-RUN)

These rules cover running added to a strength program. The designer has no standalone endurance template.

- **CT-RUN-1** [H] 2.4 km pacing: the split per 400 m is the goal time divided by 6, and the interval target is that split minus 5 s. The sessions are 6 × 400 m with 2 min rest, 4 × 800 m with 3 min rest and 2 × 1.2 km with 4 min rest
- **CT-RUN-2** [H] Run times are written as mm:ss text (for example "1:45 per 400 m"), never as a time of day, and every split comes from the scripts
- **CT-RUN-3** [H/P] Aerobic and interval sessions come from the A1 to A6 and RS1 to RS7 libraries, and a speed or sprint session is never scheduled after strength work on the same day
- **CT-RUN-4** [M/D] Weekly running minutes start from the lifter's current running and rise by 30% or less a week, or 20% or less for novice or returning runners and female ADF candidates, with every 3rd or 4th week lighter (ev: 25155475, 17940147)
- **CT-RUN-5** [M] Running volume is capped and interval-heavy: long steady road runs are replaced by 200 to 800 m intervals plus one easy run of 20 to 40 min (ev: 10495636, 9232977, 10332180, 19528858, 16895139, 26243014)
- **CT-RUN-6** [M] No draft cites the 10% rule as injury protection (ev: 17940147)
- **CT-RUN-7** [P] Running stops and the lifter is referred to a physiotherapist or doctor for focal bone pain, pain that worsens with impact, focal shin or foot tenderness, or groin or hip pain when running (ev: 10332180, 10091275)
- **CT-RUN-8** [D] A lifter whose main goal is a running event gets strength under CT-CON-6, and the running plan itself is not drafted by this skill
