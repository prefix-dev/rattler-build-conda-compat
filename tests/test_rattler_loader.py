from pathlib import Path

from rattler_build_conda_compat.loader import (
    load_all_requirements,
    load_yaml,
    parse_recipe_config_file,
)


def test_load_variants(snapshot, unix_namespace) -> None:
    variants_path = Path("tests/data/variants.yaml")

    loaded_variants = parse_recipe_config_file(str(variants_path), unix_namespace)

    assert loaded_variants == snapshot


def test_load_all_requirements() -> None:
    recipe_content = Path("tests/data/recipe_requirements.yaml").read_text()

    recipe_content = load_yaml(recipe_content)

    content = load_all_requirements(recipe_content)
    print(content)
