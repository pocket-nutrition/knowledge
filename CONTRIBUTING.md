# Contributing to Pocket Nutrition Knowledge

This repository is a **data-only** Git repository: a curated YAML knowledge base of canonical
food ingredients, cooking-transformation relationships, and mappings to public nutritional
databases. There is no application to build — contributions are almost always new or edited
YAML files.

## Repository layout

```
ingredients/                     one YAML file per canonical ingredient
cooking_relationships/           raw -> cooked yield_factor pairs
recipes/                         multi-ingredient dishes composed of existing ingredients
source_mappings/
  ciqual/                        Ciqual (ANSES, France) alim_code -> canonical ingredient_id
  mccance/                       McCance & Widdowson (UK) food_code -> canonical ingredient_id
  usda/                          USDA FNDDS fdc_id -> canonical ingredient_id
  usda_foundation/                USDA Foundation Foods fdc_id -> canonical ingredient_id
  usda_sr/                        USDA SR Legacy fdc_id -> canonical ingredient_id
schemas/                         JSON Schema definitions for every YAML type above
scripts/                         validation and gap-analysis tools
```

Every file under `ingredients/`, `cooking_relationships/`, `recipes/`, and `source_mappings/*/`
is validated against a corresponding schema in `schemas/` — see `scripts/validate.py`.

## Adding or editing an entry

Each contribution is a single new (or edited) YAML file. Do not batch unrelated ingredients or
mappings into one file — one canonical entity per file, one file per PR is the norm for small
contributions.

### Add a new ingredient

Create `ingredients/{id}.yaml` where `id` matches `^[a-z0-9_]{1,128}$`:

```yaml
id: sweet_potato
name_en: sweet potato
name_fr: patate douce
food_group: vegetable   # meat | fish | shellfish | vegetable | cereal | dairy | beverage | egg
                        # fat | fruit | legume | nut_seed | spice_herb | sweetener | baked_good
                        # sauce | processed_meat | prepared_dish | seaweed | alcohol | other
states:
  raw:
    portion_g: 180
  cooked:
    portion_g: 150
can_eat_raw: false
can_eat_cooked: true
typical_state: boiled
```

`states` is required and keyed by preparation state (`raw`, `cooked`, `processed`); each entry
may carry `portion_g` and/or `density_g_ml`. See `schemas/ingredient.schema.json` for every
optional field (`aliases_en`/`aliases_fr`, `serving_mode`, `absorption_factors`, etc.).

### Link an external source entry

Create `source_mappings/{source}/{source_id}.yaml`, where `source` is one of `ciqual`,
`mccance`, `usda`, `usda_foundation`, `usda_sr`, `reference`:

```yaml
source: ciqual
source_id: '20001'
canonical_ingredient_id: sweet_potato
label: Patate douce, crue
match_method: manual
confidence: 1.0
```

If the source row describes a cooked item (label contains "cuit", "cooked", "boiled", etc.),
set `cooking_method` explicitly (`boiled`, `steamed`, `grilled`, `roasted`, `fried`, `cooked`,
or `dry` for dehydrated foods) — `scripts/validate.py --warn-cooked` flags mismatches.

### Add a cooking relationship

Create `cooking_relationships/{raw_id}__{cooking_method}.yaml`:

```yaml
raw_id: sweet_potato
cooking_method: boiled   # boiled | steamed | grilled | roasted | fried | cooked
yield_factor: 0.97       # cooked weight / raw weight (0.1-5.0; >1 for water-absorbing foods)
confidence: 0.85
source: manual           # ciqual_pair | mccance_pair | usda_pair | usda_sr_pair
                         # usda_foundation_pair | usda_yield | usda_yield_mp_r2 | manual
```

### Add a recipe

Create `recipes/{id}.yaml`. Every `ingredient_id` referenced in `components` must already
exist as `ingredients/{ingredient_id}.yaml` — `scripts/validate.py` checks this cross-reference:

```yaml
id: sweet_potato_mash
name_en: sweet potato mash
name_fr: purée de patate douce
components:
- ingredient_id: sweet_potato
  weight_g: 200
  cooking_method: boiled
- ingredient_id: butter
  weight_g: 15
  cooking_method: raw
```

## Validating before submitting a PR

Install dependencies once:

```bash
pip install -r scripts/requirements.txt
```

Then run the schema validator (offline, reads local YAML only):

```bash
python scripts/validate.py
# OK — 24123 files validated successfully.
```

`scripts/validate.py` fails the build (non-zero exit code) if any YAML file does not match its
schema, or if a recipe references an ingredient that doesn't exist. Optionally, add
`--warn-cooked` to also surface source mappings whose label looks cooked but are tagged `raw`:

```bash
python scripts/validate.py --warn-cooked
```

**Every PR must pass `scripts/validate.py` with zero errors.**

`scripts/gap_analysis.py` reports which ingredients are missing a source mapping or cooking
relationship (offline, reads local YAML only) — useful for finding where to focus contribution
effort, but not required to submit a PR.

## Pull request process

1. Fork the repository and create a branch (`git checkout -b add-sweet-potato`).
2. Add or edit the relevant YAML file(s) — see above.
3. Run `python scripts/validate.py` and confirm it reports zero errors.
4. Commit with a descriptive message, e.g.:
   ```
   git commit -m "feat: add sweet_potato with Ciqual mapping and boiled relationship"
   ```
5. Push your branch and open a pull request describing what was added or changed and why
   (cite the source database and entry, e.g. "Ciqual alim_code 20001").
6. A maintainer reviews the diff and schema validation result before merging.

## Data quality expectations

- Prefer authoritative sources (Ciqual, USDA, McCance) over guesses for `yield_factor`,
  `density_g_ml`, and `portion_g` values; cite the source in `notes` when it isn't obvious.
- Keep `confidence` honest: `1.0` only for a verified, unambiguous match.
- Don't invent `canonical_ingredient_id` values that don't have a corresponding
  `ingredients/{id}.yaml` file — `source_mappings/` entries may point to `null` for
  "not yet mapped."

## Reporting issues

Use the issue templates under `.github/ISSUE_TEMPLATE/`:
- **Bug report** — wrong, missing, or inconsistent ingredient/mapping/relationship data.
- **Feature request** — propose a new ingredient, source mapping, or recipe to add.
