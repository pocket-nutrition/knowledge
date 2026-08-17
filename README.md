# Pocket Nutrition Knowledge

Curated YAML knowledge base for the Pocket Nutrition nutritional prediction platform.
This repository is the single source of truth for the canonical ingredient catalogue.
`pocket-nutrition/community` clones it at startup and materialises it into Redis; `pocket-nutrition/ingest`
reads Redis to train the ML model and build the Elasticsearch product search index.

---

## Repository layout

```
ingredients/              one YAML per canonical ingredient
cooking_relationships/    raw→cooked yield_factor pairs
recipes/                  multi-ingredient dishes composed of existing ingredients
source_mappings/
  ciqual/                 Ciqual alim_code → canonical ingredient_id
  mccance/                McCance food_code → canonical ingredient_id
  usda/                   USDA FNDDS fdc_id → canonical ingredient_id
  usda_foundation/        USDA Foundation Foods fdc_id → canonical ingredient_id
  usda_sr/                USDA SR Legacy fdc_id → canonical ingredient_id
schemas/                  JSON Schema definitions for all four YAML types (ingredient,
                          source_mapping, cooking_relationship, recipe)
scripts/
  validate.py             validate all YAML files against their schemas
  gap_analysis.py         report ingredients missing mappings or cooking_relationships
```

> Note: there is currently no Open Food Facts (`off/`) source mapping folder — mappings cover
> Ciqual, McCance, and USDA (FNDDS, Foundation, SR Legacy) only.

---

## How this knowledge base was built

The initial corpus was seeded from Mealie's bilingual food lists (French and English exports),
which produced ~2,900 canonical ingredient stubs under `ingredients/`.

Source mappings (`source_mappings/`) were then created to link each external database entry
(Ciqual alim_code, USDA fdc_id, McCance food_code) to a canonical ingredient ID.
This was done in two passes:

1. **Automated first pass** — a now-removed script matched database entries to ingredients
   via normalized French/English name similarity (exact name, name before first comma,
   leading token). This produced ~860 linked Ciqual mappings and ~70 cooking relationships
   derived from Ciqual raw/cooked kcal pairs.

2. **Manual curation** — remaining mappings are linked manually, entry by entry, using
   syntactic matching against the ingredient catalogue. This is the ongoing work.

Cooking relationships (`cooking_relationships/`) encode the yield_factor (cooked weight /
raw weight) for each raw ingredient × cooking method pair. Most were originally derived from
raw/cooked kcal pairs found in each nutritional database, then reviewed; new ones are now
added by hand (see "Adding or editing knowledge" below).

---

## Pipeline position

```
pocket-nutrition/knowledge (this repo, YAML)
        │
        └── pocket-nutrition/community  ──► Redis  (knowledge:ingredient:*, knowledge:mapping:*, ...)
                                            │
                                            └── pocket-nutrition/ingest
                                                  ├── train model  ──► model.joblib
                                                  └── index_search ──► product_search (Elasticsearch)
```

`pocket-nutrition/community` reloads this repo on demand via `POST /admin/reload`.
`pocket-nutrition/ingest` is a pure consumer — it never writes back to this repository or to Redis.

---

## Adding or editing knowledge

### Add a new ingredient

Create `ingredients/{id}.yaml` (id must match `^[a-z0-9_]+$`):

```yaml
id: sweet_potato
name_en: sweet potato
name_fr: patate douce
food_group: vegetable   # meat | fish | shellfish | vegetable | cereal | dairy | beverage | egg
                        # fat | fruit | legume | nut_seed | spice_herb | sweetener | other …
states:
  raw:
    portion_g: 180
  cooked:
    portion_g: 150
can_eat_raw: false
can_eat_cooked: true
typical_state: boiled
```

See `schemas/ingredient.schema.json` for the full field list (`aliases_en`/`aliases_fr`,
`serving_mode`, `density_g_ml`, `absorption_factors`, …).

### Link an external source entry

Create `source_mappings/{source}/{source_id}.yaml`:

```yaml
source: ciqual
source_id: '20001'
canonical_ingredient_id: sweet_potato
label: Patate douce, crue
match_method: manual
confidence: 1.0
```

### Add a cooking relationship

Create `cooking_relationships/{raw_id}__{cooking_method}.yaml`:

```yaml
raw_id: sweet_potato
cooking_method: boiled   # boiled | steamed | grilled | roasted | fried | cooked
yield_factor: 0.97       # cooked weight / raw weight (0.1–5.0; >1 for water-absorbing foods)
confidence: 0.85
source: manual           # ciqual_pair | mccance_pair | usda_yield | manual
```

### Deploy changes

```bash
git add .
git commit -m "feat: add sweet_potato with Ciqual mapping and boiled relationship"
git push

# Reload Community (picks up the new YAML files)
curl -X POST https://community.your-host/admin/reload \
     -H "Authorization: Bearer $RELOAD_TOKEN"

# Rebuild the Elasticsearch product_search index (no model retrain needed)
docker compose --profile search run pocket-nutrition-ingest-search
```

---

## Scripts

Install dependencies once:
```bash
pip install -r scripts/requirements.txt
```

### `validate.py` — schema validation

Offline — reads local YAML files only. Checks all YAML files against their JSON schemas (`schemas/`). Run before committing.

```bash
python scripts/validate.py
# OK — 24123 files validated successfully.
```

### `gap_analysis.py` — coverage report

Offline — reads local YAML files only. Shows which ingredients lack source_mappings or cooking_relationships,
so manual enrichment work can be prioritised.

```bash
python scripts/gap_analysis.py
```

Output sections:

| Section | Meaning |
|---|---|
| CRITICAL | no mapping + no cooking_relationship → model returns `unknown: true` |
| HIGH | has mapping, no cooking_relationship → nutritional lookup works, no cooking prediction |
| MEDIUM | has cooking_relationship, no mapping → cooking ratio known, raw profile missing |
| LOW | source mapping exists but is not linked to any ingredient |

---

## Current coverage (approximate, 2026-05-14)

| Metric | Count |
|---|---|
| Canonical ingredients | ~2,900 |
| Linked source mappings — Ciqual | ~857 / ~858 total |
| Linked source mappings — McCance (UK) | ~408 / 544 total |
| Linked source mappings — USDA FNDDS | ~1,974 / 4,441 total |
| Linked source mappings — USDA SR Legacy | 0 / ~1,400 raw foods (soft-match only) |
| Cooking relationships | ~310 |
| Model-ready (mapping + relationship) | ~280 (~10%) |

**Pending work:** McCance and USDA source_mappings are not fully indexed — see
`scripts/gap_analysis.py`'s output for what's missing, and "Adding or editing knowledge" above
for how to add a mapping or cooking relationship by hand.

After adding entries, reload Community and retrain the model:

```bash
curl -X POST https://community.your-host/admin/reload -H "Authorization: Bearer $RELOAD_TOKEN"
# then re-run pocket-nutrition/ingest
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the directory layout, how to add a new ingredient,
source mapping, cooking relationship, or recipe, and the validation/PR process.

## License

AGPL-3.0 — see [LICENSE](LICENSE).
