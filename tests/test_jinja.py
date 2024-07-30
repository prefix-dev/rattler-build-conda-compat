from pathlib import Path

from rattler_build_conda_compat.jinja import eval_recipe_using_context, load_yaml


def test_render_context(snapshot) -> None:
    recipe = Path("tests/data/context.yaml")
    with recipe.open() as f:
        recipe_yaml = load_yaml(f)

    rendered = eval_recipe_using_context(recipe_yaml)
    assert rendered == snapshot
