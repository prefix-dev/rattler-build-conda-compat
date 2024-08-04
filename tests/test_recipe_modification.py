from pathlib import Path

from rattler_build_conda_compat.modify_recipe import update_build_number, update_version


def test_build_number_mod(data_dir: Path) -> None:
    tests = data_dir / "build_number"
    result = update_build_number(tests / "test_1/recipe.yaml", 0)
    expected = tests / "test_1/expected.yaml"
    assert result == expected.read_text()

    result = update_build_number(tests / "test_2/recipe.yaml", 0)
    expected = tests / "test_2/expected.yaml"
    assert result == expected.read_text()


def test_version_mod(data_dir: Path) -> None:
    tests = data_dir / "version"
    test_recipes = tests.glob("**/recipe.yaml")
    for recipe in test_recipes:
        result = update_version(recipe, "0.25.0", None)
        expected = recipe.parent / "expected.yaml"
        assert result == expected.read_text()
