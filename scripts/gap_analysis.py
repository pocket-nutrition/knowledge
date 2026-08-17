"""Knowledge base gap analysis — no services required.

Reads local YAML files to report which ingredients lack source_mappings or
cooking_relationships, so manual enrichment work can be prioritised.

Usage:
    python scripts/gap_analysis.py [--repo-root PATH]

Output sections (by priority):
    CRITICAL  fully orphaned (no mapping + no relation)
    HIGH      has mapping, no cooking_relationship
    MEDIUM    has cooking_relationship, no mapping
    LOW       source_mappings with null canonical_ingredient_id
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def _load_ingredient_ids(root: Path) -> set[str]:
    return {p.stem for p in (root / "ingredients").glob("*.yaml")}


def _load_mapped_ids(root: Path) -> tuple[set[str], list[str], dict[str, int]]:
    """Return (canonical_ingredient_ids, null_mapping_paths, per_source_linked_counts)."""
    mapped: set[str] = set()
    null_paths: list[str] = []
    per_source: dict[str, int] = {}
    for p in (root / "source_mappings").rglob("*.yaml"):
        data = yaml.safe_load(p.read_text())
        if not isinstance(data, dict):
            continue
        source = data.get("source", p.parent.name)
        cid = data.get("canonical_ingredient_id")
        if cid:
            mapped.add(cid)
            per_source[source] = per_source.get(source, 0) + 1
        else:
            null_paths.append(str(p.relative_to(root)))
    return mapped, null_paths, per_source


def _load_related_ids(root: Path) -> set[str]:
    related: set[str] = set()
    for p in (root / "cooking_relationships").glob("*.yaml"):
        data = yaml.safe_load(p.read_text())
        if isinstance(data, dict):
            raw_id = data.get("raw_id")
            if raw_id:
                related.add(raw_id)
    return related


def _print_section(label: str, items: list[str], max_shown: int = 30) -> None:
    print(f"\n[{label}] ({len(items)})")
    for item in items[:max_shown]:
        print(f"  {item}")
    if len(items) > max_shown:
        print(f"  ... and {len(items) - max_shown} more")


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge base gap analysis")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to the pocket-nutrition-knowledge repo root (default: parent of scripts/)",
    )
    args = parser.parse_args()
    root = args.repo_root

    ingredient_ids = _load_ingredient_ids(root)
    mapped_ids, null_canonical, per_source = _load_mapped_ids(root)
    related_ids = _load_related_ids(root)

    fully_orphaned = sorted(ingredient_ids - mapped_ids - related_ids)
    mapping_only   = sorted((mapped_ids & ingredient_ids) - related_ids)
    relation_only  = sorted((related_ids & ingredient_ids) - mapped_ids)
    trainable      = (mapped_ids & related_ids) & ingredient_ids

    source_lines = "".join(
        f"    {src:<20}: {cnt} linked\n"
        for src, cnt in sorted(per_source.items())
    )
    print(
        f"\n=== Knowledge Gap Analysis ===\n"
        f"  Ingredients total : {len(ingredient_ids)}\n"
        f"  Model-ready       : {len(trainable)} "
        f"({100 * len(trainable) // max(len(ingredient_ids), 1)}%)\n"
        f"  Source mappings   : {len(mapped_ids)} unique ingredients linked\n"
        f"{source_lines}"
        f"  Cooking relations : {len(related_ids)} unique raw_ids"
    )

    _print_section("CRITICAL — fully orphaned (no mapping + no relation)", fully_orphaned)
    _print_section("HIGH     — has mapping, no cooking_relationship", mapping_only)
    _print_section("MEDIUM   — has cooking_relationship, no mapping", relation_only)
    _print_section("LOW      — mappings with null canonical_ingredient_id", null_canonical)


if __name__ == "__main__":
    main()
