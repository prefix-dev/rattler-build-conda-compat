import yaml
from rattler_build_conda_compat.loader import parse_recipe_config_file, load_all_requirements
from pathlib import Path


def test_load_variants(snapshot, unix_namespace):
    variants_path = Path("tests/data/variants.yaml")

    loaded_variants = parse_recipe_config_file(str(variants_path), unix_namespace)

    assert loaded_variants == snapshot


def test_load_all_requirements():
    recipe_path = Path("tests/data/recipe_requirements.yaml")

    content = load_all_requirements(recipe_path)
    print(content)
