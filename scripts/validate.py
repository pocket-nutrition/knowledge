"""Validate all YAML files in pocket-nutrition-knowledge against their JSON schemas.

Usage:
    python scripts/validate.py [--repo-root PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml


SCHEMA_MAP: dict[str, str] = {
    "ingredients": "ingredient.schema.json",
    "source_mappings": "source_mapping.schema.json",
    "cooking_relationships": "cooking_relationship.schema.json",
    "recipes": "recipe.schema.json",
}

# A source_mapping whose label matches any of these tokens describes a
# *cooked* nutritional row and must carry a non-`raw` `cooking_method` so the
# community UI can group references on the canonical ingredient correctly.
_COOKED_LABEL_RE = re.compile(
    r"\b(cuit|cuite|cuits|cuites|cooked|boiled|grilled|roasted|"
    r"fried|steamed|braised|sauté|saute|baked)\b",
    re.IGNORECASE,
)


def _load_schema(schemas_dir: Path, schema_file: str) -> dict:
    with open(schemas_dir / schema_file) as f:
        return json.load(f)


def validate_repo(repo_root: Path) -> list[str]:
    schemas_dir = repo_root / "schemas"
    errors: list[str] = []

    for folder, schema_file in SCHEMA_MAP.items():
        schema = _load_schema(schemas_dir, schema_file)
        validator = jsonschema.Draft7Validator(schema)

        for yaml_path in sorted((repo_root / folder).rglob("*.yaml")):
            with open(yaml_path) as f:
                try:
                    data = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    errors.append(f"{yaml_path}: YAML parse error: {exc}")
                    continue

            for err in validator.iter_errors(data):
                errors.append(f"{yaml_path}: {err.message} (path: {list(err.path)})")

    errors.extend(_validate_recipe_references(repo_root))
    return errors


def _validate_recipe_references(repo_root: Path) -> list[str]:
    """Every recipe component must reference an existing ingredient YAML."""
    errors: list[str] = []
    ingredients_dir = repo_root / "ingredients"

    for yaml_path in sorted((repo_root / "recipes").rglob("*.yaml")):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError:
            continue  # already reported as a schema/parse error
        if not isinstance(data, dict):
            continue
        for component in data.get("components") or []:
            ingredient_id = (component or {}).get("ingredient_id")
            if ingredient_id and not (ingredients_dir / f"{ingredient_id}.yaml").exists():
                errors.append(
                    f"{yaml_path}: component references unknown ingredient "
                    f"'{ingredient_id}' (no ingredients/{ingredient_id}.yaml)"
                )

    return errors


def find_warnings(repo_root: Path) -> list[str]:
    """Non-fatal checks reported separately from hard schema errors."""
    warnings: list[str] = []

    mappings_dir = repo_root / "source_mappings"
    for yaml_path in sorted(mappings_dir.rglob("*.yaml")):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        label = data.get("label") or ""
        if not _COOKED_LABEL_RE.search(label):
            continue
        cooking_method = data.get("cooking_method", "raw")
        if cooking_method == "raw":
            warnings.append(
                f"{yaml_path}: label looks cooked ({label!r}) but "
                f"cooking_method is 'raw'"
            )

    return warnings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).parent.parent)
    parser.add_argument(
        "--warn-cooked",
        action="store_true",
        help="Report cooked-looking source mappings without an explicit cooking_method.",
    )
    args = parser.parse_args()

    errors = validate_repo(args.repo_root)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        print(f"\n{len(errors)} validation error(s) found.", file=sys.stderr)
        sys.exit(1)

    if args.warn_cooked:
        warnings = find_warnings(args.repo_root)
        for w in warnings:
            print(f"WARN: {w}", file=sys.stderr)
        if warnings:
            print(
                f"\n{len(warnings)} cooked-label warning(s) — re-tag with "
                f"cooking_method.",
                file=sys.stderr,
            )

    yaml_count = sum(
        len(list((args.repo_root / folder).rglob("*.yaml")))
        for folder in SCHEMA_MAP
    )
    print(f"OK — {yaml_count} files validated successfully.")


if __name__ == "__main__":
    main()
