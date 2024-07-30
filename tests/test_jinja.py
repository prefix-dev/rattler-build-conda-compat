from pathlib import Path

import yaml
from rattler_build_conda_compat.jinja import load_yaml, render_recipe_with_context


def test_render_recipe_with_context(snapshot) -> None:
    recipe = Path("tests/data/context.yaml")
    with recipe.open() as f:
        recipe_yaml = load_yaml(f)

    rendered = render_recipe_with_context(recipe_yaml)
    into_yaml = yaml.dump(rendered)

    assert into_yaml == snapshot
