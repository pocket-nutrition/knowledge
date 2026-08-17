---
name: Data bug report
about: Report wrong, missing, or inconsistent ingredient/mapping/cooking data
title: "[data] "
labels: bug
assignees: ''
---

## What is wrong

A clear description of the incorrect, missing, or inconsistent data.

## Affected file(s)

- `ingredients/____.yaml`
- `source_mappings/____/____.yaml`
- `cooking_relationships/____.yaml`
- `recipes/____.yaml`

## Current value

```yaml
# paste the relevant field(s) from the file above
```

## Expected value

```yaml
# what the value should be, with a source if possible
```

## Source / reference

Where does the correct value come from? (e.g. Ciqual alim_code, USDA fdc_id, a published
nutrition table, direct measurement). Link or cite it if possible — data changes without a
source are harder to review.

## Additional context

Anything else relevant (e.g. this affects other ingredients with the same pattern, this makes
`scripts/validate.py` fail, etc.).
