---
name: ironledger-nutrition-plan
description: Set evidence-based calorie and macro targets for a lifter, build an Excel meal plan with like-for-like swaps and a weekly check-in sheet (everyday Australian supermarket foods), and read their check-ins against published adjustment rules. Use when a lifter wants a nutrition plan for fat loss, a lean gain, maintenance or a sport season, or asks whether to change their calories after a few weeks.
---

# Nutrition plan for lifters

This skill sets calorie and macro targets from published evidence, builds the plan as an Excel workbook, and reads the lifter's own weekly check-ins against the same rules. The lifter decides: you present the targets, the options and the rules behind them.

House style: simple and clear. Everyday Australian supermarket foods (Woolworths, Coles, Aldi). No recipes, no exotic ingredients, no cooking instructions. The same few meals repeat, and the flexibility comes from swaps. Plan text is plain English, with no em dashes and no emojis.

**Every number comes from `scripts/nutrition_plan.py`, or from the workbook's own formulas.** Never work out calories, macros, averages or trends in prose. Run the script from the skill directory: `python3 scripts/nutrition_plan.py <command>`. Every command but `build` needs only Python's standard library; `build` needs openpyxl (`pip install openpyxl`). The rule numbers r1 to r25 are this skill's own; section 10 has the evidence behind them.

## 0. The gate. Check it before anything else

Before setting any target, ask the lifter whether any of these apply. Don't guess from what they've said:

- pregnant or breastfeeding;
- a medical condition, such as diabetes or kidney disease, or a medication that affects appetite or weight;
- a current or past eating disorder, or signs of low energy availability (RED-S): missed or irregular periods, bone stress injuries, frequent illness;
- under 18.

**Hard stop** (r1): if any one applies, write no plan and no calorie target. The script refuses and prints the referral: a doctor or a registered dietitian (in Australia, an Accredited Practising Dietitian, dietitiansaustralia.org.au), and for disordered eating, the Butterfly helpline on 1800 33 4673 (Australia) or the person's local eating disorder service. Pass the answers to the script as `--flags` (`targets`) or `flags` (the build spec and check-ins), using these words: `pregnancy`, `breastfeeding`, `medical condition`, `appetite medication`, `weight medication`, `disordered eating`, `red-s`.

Allergies, intolerances, vegetarian and vegan are fine: pick foods accordingly. This skill doesn't plan a weigh-in cut for a meet (section 8).

## 1. Commands

| Command | Use |
|---|---|
| `targets --sex M\|F --age A (--height CM \| --height-in IN) (--weight KG \| --weight-lb LB) --activity LEVEL --goal GOAL [--bf PCT] [--sport S] [--season off\|pre\|in] [--status novice\|intermediate\|advanced] [--exercise-kcal K] [--flags "a,b"] [--rest-days N]` | calories, macros, expected %/wk, fluid and fibre, with the rules it applied and its warnings |
| `swap FOOD QTY TO_FOOD... [--basis protein\|kcal\|carbs]` | like-for-like swaps |
| `meal food:qty food:qty ...` | total an alternative meal |
| `foods [CATEGORY]` | the food database |
| `check spec.json` / `build spec.json OUT.xlsx` | test day totals against targets, then build the workbook (build applies the section 0 gate) |
| `checkin checkins.json` | weekly averages, the trend, the gates and the options the section 7 rules list |

The script works in kilograms and centimetres. For pounds and inches, pass `--weight-lb` and `--height-in`; it converts them.

## 2. What to ask

Ask once, as a single list, for anything missing; never fill a gap with a guess.

| Ask for | Script input |
|---|---|
| Sex, age, height, weight | `--sex --age --height --weight` (or `--height-in --weight-lb`) |
| Goal | Lose body fat: `fat_loss`. Build muscle (lean gain): `lean_gain`. Maintain or recomp: `maintain`. Sport performance (in season): `performance` |
| Training (type and sessions a week), job or daily steps | `--activity` (table below) and `--sport` |
| Body fat %, and how it was measured | `--bf` only when measured reliably (DEXA or trained skinfolds) |
| Event date or plan length, meals a day, foods to avoid or allergies, supplements, set rest days, training time | the spec and the meal build |
| The section 0 questions | `--flags` |

Activity level:

| Level | Factor | Training sessions a week (desk job) |
|---|---|---|
| sedentary | 1.2 | 0-1 |
| light | 1.375 | 1-3 |
| moderate | 1.55 | 3-5 |
| hard | 1.725 | 6-7 |
| extreme | 1.9 | twice-daily training (8+ sessions) |

Count sessions (games count). A physical job or 12k+ steps moves the lifter up one level, capped at hard unless they train twice a day. When unsure, pick the lower level: the check-ins correct it (r4). Ignore wearable calorie counts. `--sport rugby` or `field` with `--season in` raises the factor to at least 1.725 (r4).

## 3. Set targets

Run `targets` and read its `rules` and `warnings`. What it applies:

* **BMR** (r3): Mifflin-St Jeor by default. `--formula cunningham` (500 + 22 x FFM) only with a measured body fat in a trained lifter. Harris-Benedict and Katch-McArdle stay for old plans only.
* **Fat-loss rate** (r5, r6): 0.75% of bodyweight a week by default; 0.6% for performance lifters (rugby, field sport, ADF, powerlifting) or advanced lifters; 0.5% for lean lifters (under 15% body fat for men, 23% for women); up to 1.0% for a BMI over 30 or high body fat. The deficit is at most 25% of TDEE, and about 500 kcal a day for lean or performance lifters.
* **Lean gain** (r7): surplus 15% for novices, 10% by default, 5% for advanced lifters, aiming for 0.25-0.5% a week (0.1-0.25% advanced).
* **Protein** (r9): in a deficit 2.3-3.1 g/kg of **fat-free mass** when body fat is measured (the script uses 2.5, or 2.8 for lean lifters), otherwise about 2.2 g/kg of bodyweight. 1.6-2.2 g/kg in a surplus or at maintenance. A BMI over 30 uses a reference weight (27.5 x height in m squared). Protein is never cut in an adjustment.
* **Fat** (r11): at least 20% of energy and 0.5 g/kg. 15-20% only briefly, for men, in a peak phase (`--peak`).
* **Carbohydrate** (r12): the remainder, checked against training load. Field-sport players and ADF candidates never go under 3 g/kg; the script raises carbohydrate and calories to meet it.
* **Floors** (r8): calories never go below estimated BMR; the script raises them to it. **Never use BMR x 0.8.** With a measured body fat and `--exercise-kcal`, it reports energy availability. Under 30 kcal/kg FFM a day, the lifter shouldn't start that target on their own: they eat more or train less, or see a sports dietitian or doctor.
* **Fluid and fibre** (r13): water at least the larger of 2.6 L (men) or 2.1 L (women) and 33 ml/kg, plus 500-750 ml per training hour; fibre at least 30 g (men) or 25 g (women).
* **In season** (r24): rugby and field sport in season sits at maintenance, with carbohydrate periodised by the day (about 3 g/kg off, 3-5 skills, 5-7 contact and the day before a game). The script warns about a fat-loss goal then.
* **ADF candidates** (r25), preparing for the Australian Defence Force fitness assessment: inside the BMI 18.5-32.9 band well before assessment day, at no more than 1% a week; carbohydrate 3-7 g/kg by running load; no crash cut before the medical.

**Training vs rest days** (optional): only with 2+ set rest days a week. `--rest-days N` keeps protein and fat the same, makes rest-day carbs 20% lower, and keeps the weekly average on goal. Put `training_day` in the top-level spec targets and `rest_day` in the rest-day sheet's `targets`. Game day uses the training day sheet; add a game-day line to the plan rules.

## 4. Structure the day

- 3-5 eating occasions, at least 4 protein feeds (r10) (Meal 1-3 or 4 plus 1-2 snacks).
- Protein spread evenly: ~0.4 g/kg per meal (roughly 30-50 g for most adults), every 3-4 h. Main meals carry most of it.
- Pre-training (1-3 h before): a meal or snack with carbs (~1 g/kg) and some protein, low fat and fibre if close to the session.
- Post-training (within ~2 h): a normal meal with 0.3-0.4 g/kg protein and carbs.
- Put more of the carbs around training; put fats and most veg away from the pre-session meal.

## 5. Build the meals

Use these patterns first. Adjust grams to hit targets.

**Breakfast A (bowl):** rolled oats OR Weet-Bix + protein powder scoop + banana OR 100 cal fruit + lite milk OR natural peanut butter.
**Breakfast B (OR/ line):** sourdough OR English muffins + eggs + lean ham + tasty cheese + butter + sauce + free veggies.
**Lunch/Dinner:** protein (chicken breast OR turkey breast mince OR 5 star beef mince OR tuna tins OR kangaroo mince OR lean rump steak) + carb (rice dry OR pasta dry OR potato OR sweet potato OR wrap OR microwave rice pouch) + 10 ml sauce of choice + 2.5-10 g butter/olive oil + 150 g free veggies (+ 20 g tasty cheese).
**Pasta/mince night:** 5 star beef mince + pasta (dry) + 100 g tomato pasta sauce + cheese + free veggies.
**Snacks:** Greek yoghurt OR YoPRO + frozen berries (+ peanut butter/almonds); rice cakes or Corn Thins + honey/jam; protein powder + fruit; LCM/Milo bar or snakes for quick pre-training carbs; Up&Go Protein as a grab-and-go.
**Lean gain extra calories:** bigger carb portions, full cream milk, peanut butter, muesli, extra snack; keep volume manageable (liquid calories help).

Food rules:
- Use only foods in the script's database (`python3 scripts/nutrition_plan.py foods`). If you must add one, use an Australian source (FSANZ AFCD or the Australian label) and add it to FOODS.
- Meat, fish, rice, pasta, oats and potato are weighed raw or dry. Say so in the plan rules.
- Free veggies are not counted (about 30-40 kcal per 150 g). Potato, sweet potato, corn, peas, pumpkin and avocado are counted.
- Rounding: meat/fish to 10 g (to 25 g for bigger portions), rice/pasta/oats to 5 g, oil/butter to 2.5 g, spreads to 5 g, milk/yoghurt to 10-50 g, whole items to 0.5.
- Swaps: generate with `python3 scripts/nutrition_plan.py swap chicken_breast 250 turkey_breast_mince beef_mince_5star tuna_tin` (proteins matched on protein, everything else on calories). It flags swaps that shift calories more than 15% or give huge portions; pick a different swap or split it (e.g. "OR/ 85g rice + 500g potato"). Put the first swap in the Food label ("Chicken breast OR 240g turkey breast mince") and extra ones as `swaps` lines. Offer 2-3 swaps on protein and carb items.
- Alternative meals (`alts`, e.g. the eggs-on-toast breakfast): size them with `python3 scripts/nutrition_plan.py meal sourdough:80 egg:2 ham:50 cheese_light:20` so they land within ~50 kcal and ~5 g protein of the main option.

Tolerance for each day (check and build test it): calories within 5% or 100 kcal (whichever is smaller), protein within 10 g, carbs and fat within 10% (min 15 g / 8 g).

Hitting targets fast: build the meals from the patterns, run `check`, then fix in this order: (1) protein portions, (2) carb portions (rice/pasta/oats), (3) fat (oil, butter, peanut butter, cheese). Usually 2-3 rounds.

## 6. Build and verify

1. Write a spec JSON (below), iterate with `python3 scripts/nutrition_plan.py check spec.json` until every day says OK, then `python3 scripts/nutrition_plan.py build spec.json "<Name> - <Phase> Plan.xlsx"` (or `"<Phase> Plan.xlsx"` without a name).
2. The build refuses a spec with a hard-stop flag, an age under 18, or no age.
3. **Reply** in a few lines: the targets (calories, P/C/F), the expected % a week, the inputs you used and any assumptions, the rules that fired, any warning, and the re-check date 2 weeks out. Then hand over the workbook.

Spec format:
```json
{
 "client": {"name": "Sam", "sex": "F", "age": 28, "height_cm": 168, "weight_kg": 65, "bodyfat_pct": null, "activity": "moderate", "formula": "mifflin"},
 "flags": [],
 "phase": "Fat Loss Phase", "start_date": "2026-09-21", "weeks": 8,
 "event_name": "", "event_date": "",
 "targets": {"calories": 1750, "protein": 145, "carbs": 170, "fat": 55},
 "notes": ["Weigh meat, rice, pasta, oats and potato raw/dry on scales.", "..."],
 "days": [
  {"sheet": "Training Day", "title": "Fat Loss Phase", "subtitle": "Training Day",
   "targets": {"calories": 1750, "protein": 145, "carbs": 170, "fat": 55},
   "meals": [
    {"name": "Meal 1",
     "items": [
      {"food": "oats", "qty": 50, "label": "Rolled oats OR 3 Weet-Bix"},
      {"food": "chicken_breast", "qty": 200, "label": "Chicken breast OR 190g turkey breast mince", "swaps": ["190g 5 star beef mince OR 3x 95g tins tuna"]}
     ],
     "alts": ["2 slices sourdough (80g) + 2 eggs + 50g ham + free veggies"]}
   ]}
 ]
}
```
`client.name` is optional; the Cover and the check-in sheet show it when given. `label` is optional (defaults to the database name). Day `targets` override the top-level targets for that day. `title` (optional) is the Cover title, default "Nutrition Plan". `weeks` sets how many check-in blocks.

Default plan rules (edit to suit, max 7): weigh raw/dry; use the OR/ swaps like-for-like; free veggies unlimited; water as `targets` gives it (`fluid_note`); weigh daily, judge the weekly average; steps target; alcohol is not in the plan, record it in the check-in.

## 7. Check-ins and adjustments

The lifter fills in the workbook's **Weekly check-in** sheet: a morning weight each day, daily steps, and 1-5 ratings for training performance, training recovery, diet adherence, sleep, energy and hunger. The sheet averages each week's weight and steps itself. Every 1-2 weeks, read it with `checkin`:

1. Turn the sheet (or what the lifter tells you) into `checkins.json`, one entry per week in order, without changing any number:
   ```json
   {"goal": "fat_loss", "age": 28, "status": "intermediate", "lean_or_performance": false, "in_season": false,
    "plan_start": "2026-09-21", "last_change": null, "as_of": "2026-10-18", "flags": [], "red_flags": [],
    "weeks": [{"start": "2026-09-21", "weights": [65.2, 65.0, 64.9, null, 65.1, 64.8, 64.7], "steps": [9000, 8500],
               "adherence": 4, "off_plan_meals": 0, "sleep": 3, "energy": 3, "hunger": 3, "training": 4,
               "performance_falling": false, "no_decision": null}]}
   ```
   `last_change` is the date of the last calorie or steps change. `no_decision` tags a week that shouldn't count (r21), such as `"travel"`. `red_flags` lists any r23 sign the lifter reports; ask about them at every check-in.
2. Run `python3 scripts/nutrition_plan.py checkin checkins.json`. It prints each week's average, the weekly % change, the 14-day trend, the gates, the rules that fired and the options. Present those; every number comes from that output.
3. The lifter chooses. Apply their choice by changing the grams in the existing meals (usually carbohydrate), rebuild, and note the change and its date in the sheet's **Changes made** box. That date is the next `last_change`.

The rules `checkin` applies:

* **Trend** (r14): aligned 7-day means, decided on a 14-21 day slope. No calorie change until 14 days after the plan starts or after any change, so a decision needs 3 weeks of weigh-ins. One change per 2 weeks.
* **Gates** (r15, r16): adherence 3/5 or less, fewer than 5 weigh-ins, or 2+ unplanned off-plan meals means no calorie change, only process fixes. If steps fell more than 15% from baseline, restore steps before any food cut.
* **Too slow** (r17): under 0.5% a week for 2 weeks with the gates passed: 5-10% fewer calories from carbohydrate or fat (respecting the fat and carbohydrate floors), or about 2,000 more steps a day.
* **Too fast** (r18): over 1.0% a week (0.7% for lean or performance lifters) for 2 weeks, or performance falling with sleep or energy at 2/5 or less: 5-10% more calories, carbohydrate first.
* **Lean gain** (r19): under 0.25% a week for 2 weeks, +100-200 kcal; over 0.5% (0.75% for novices), -100-200 kcal.
* **Maintenance or in season** (r20): adjust 100-200 kcal only for more than 1% drift over 2-3 weeks.
* **No-decision weeks** (r21): illness, travel, a big night, the first week of a plan, a diet-break week, a creatine start. For a naturally cycling lifter, compare like-phase to like-phase, and a jump in the menses week alone is a no-decision week.
* **Diet breaks** (r22): in a cut longer than 8-12 weeks, 1-2 weeks at maintenance every 3-6 weeks, or earlier when hunger, adherence and training are all 2/5 or less. They help adherence and appetite; in trained lifters they didn't change fat loss (ICECAP). MATADOR, in men with obesity, alternated 2 weeks on and 2 weeks off from the start. Pre-warn of a 0.5-1 kg scale rise and leave the break out of the rate.
* **Red flags** (r23): menstrual change, bone pain or a stress injury, fainting, recurrent illness, low libido, or falling performance despite adherence: maintenance calories and a doctor before any deficit.
* After a cut ends, reverse rather than jumping to maintenance: from current intake, +5-10% a week (mostly carbohydrate) until the weight trend rises, then hold.

## 8. Making weight for a meet

This skill doesn't plan a weigh-in cut: no fluid, fibre or fasting protocols in the days before a meet. Work with a coach or a sports dietitian for that. If the lifter is well over their class limit close to the meet, consider moving up a class.

## 9. Supplements (only if asked, AIS Group A evidence only)

- Protein powder (WPI/whey) to hit protein when food is hard.
- Creatine monohydrate 3-5 g/day, any time, every day.
- Caffeine 3 mg/kg (range 2-6) about 60 min pre-training; avoid late sessions if it hurts sleep.
- Sports drinks, gels, electrolytes for long or hot sessions (30-60 g carbs/h over 1 h, up to 90 g/h over 2.5 h).
- Iron, vitamin D, calcium only if a doctor's blood test shows a need.
- Tested athletes (e.g. rugby, powerlifting federations): batch-tested products only.
Do not recommend fat burners, test boosters, BCAAs or anything outside Group A.

## 10. Evidence base

Cite only these. Each was checked on PubMed. Never cite from memory.

* Protein in a deficit 2.3-3.1 g/kg FFM: Helms 2014, PMID 24092765. Contest prep rates and macros: Helms 2014, PMID 24864135. Higher protein in a deficit: Longland 2016, PMID 26817506.
* Protein plateau about 1.6 g/kg (upper CI 2.2): Morton 2018, PMID 28698222. Per-meal protein and distribution: Schoenfeld 2018, PMID 29497353; Areta 2013, PMID 23459753.
* Off-season surplus: Iraki 2019, PMID 31247944. Small vs large surplus: Helms 2023, PMID 37914977.
* Rates of loss in athletes: Garthe 2011, PMID 21558571. Energy deficit and lean-mass gain: Murphy 2022, PMID 34623696.
* BMR equations: Frankenfield 2005, PMID 15883556; Cunningham 1980, PMID 7435418; athletes, Jagim 2018, PMID 28682934.
* Field-sport energy expenditure: Skalitzky 2025, PMID 41440795; wearables under-estimate, Costello 2019, PMID 31895278.
* Carbohydrate by load, fat 20% or more, fluids: ACSM/AND/DC position stand, Thomas 2016, PMID 26891166.
* Energy availability threshold: Loucks 2003, PMID 12519869. RED-S: IOC consensus, Mountjoy 2023, PMID 37752011.
* Weight noise and trend: Turicchi 2020, PMID 32915155 and 32353079; glycogen water, Kreitzman 1992, PMID 1615908. Self-reported intake: Lichtman 1992, PMID 1454084. Activity falls in a deficit: Martin 2007, PMID 18198305. Fluid across the menstrual cycle: White 2011, PMID 21845193.
* Diet breaks: MATADOR, Byrne 2018, PMID 28925405; ICECAP, Peos 2021, PMID 33587549 and 33630880.
* Rugby and field sport: Impey 2018, PMID 29453741; Posthumus 2021, PMID 34070155; Bradley 2017, PMID 28238618.
* Supplements: AIS Sports Supplement Framework, Group A (ausport.gov.au). Food values: FSANZ AFCD Release 3 and Australian labels (checked Sep 2026).

## Be honest

- This is general guidance from published evidence, not medical or dietetic advice. A lifter with a health condition, or anyone in section 0, needs a doctor or a registered dietitian.
- Present the targets and options with their rules; the lifter decides.
- The food values are Australian. For foods from elsewhere, check the local label.
