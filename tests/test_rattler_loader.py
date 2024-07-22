from __future__ import annotations

from pathlib import Path
from typing import Any

from rattler_build_conda_compat.loader import (
    load_all_requirements,
    load_yaml,
    parse_recipe_config_file,
)


def test_load_variants(snapshot, unix_namespace: dict[str, Any]) -> None:
    variants_path = Path("tests/data/variants.yaml")

    loaded_variants = parse_recipe_config_file(str(variants_path), unix_namespace)

    assert loaded_variants == snapshot


def test_load_all_requirements() -> None:
    recipe_content = Path("tests/data/recipe_requirements.yaml").read_text()

    recipe_content = load_yaml(recipe_content)

    content = load_all_requirements(recipe_content)
    print(content)


def test_load_recipe_with_missing_selectors(snapshot) -> None:
    osx_recipe = Path("tests/data/osx_recipe.yaml")

    namespace = {"osx": True, "unix": True}

    loaded_variants = parse_recipe_config_file(
        str(osx_recipe), namespace, allow_missing_selector=True
    )

    assert loaded_variants == snapshot
