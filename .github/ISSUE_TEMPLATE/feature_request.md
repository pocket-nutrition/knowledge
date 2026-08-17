---
name: Propose new ingredient / mapping / recipe
about: Suggest a new canonical ingredient, source mapping, cooking relationship, or recipe
title: "[proposal] "
labels: enhancement
assignees: ''
---

## What are you proposing

- [ ] New canonical ingredient (`ingredients/`)
- [ ] New source mapping (`source_mappings/{ciqual,mccance,usda,usda_foundation,usda_sr,reference}/`)
- [ ] New cooking relationship (`cooking_relationships/`)
- [ ] New recipe (`recipes/`)
- [ ] Other (describe below)

## Description

What ingredient, mapping, cooking transformation, or recipe should be added, and why is it
missing today? (e.g. "sweet potato is missing a boiled cooking_relationship" or "this common
dish has no recipe entry yet").

## Proposed data

```yaml
# Draft YAML for the new entry, if you have one. It doesn't need to be final —
# reviewers will help refine it against schemas/*.schema.json.
```

## Source / reference

Which database or reference does this come from (Ciqual alim_code, USDA fdc_id, McCance
food_code, a published nutrition table, etc.)? Mappings and relationships without a traceable
source are much harder to review and merge.

## Are you willing to submit a PR?

- [ ] Yes, I can open a PR with the YAML file(s)
- [ ] No, I'm reporting this for a maintainer or another contributor to pick up
