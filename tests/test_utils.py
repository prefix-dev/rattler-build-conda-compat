from rattler_build_conda_compat.utils import has_recipe


def test_recipe_is_present(recipe_dir):
    assert has_recipe(recipe_dir)


def test_recipe_is_absent(old_recipe_dir):
    assert has_recipe(old_recipe_dir) is False
