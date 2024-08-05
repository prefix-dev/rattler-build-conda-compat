from pathlib import Path

import yaml
from rattler_build_conda_compat.jinja.filters import _version_to_build_string
from rattler_build_conda_compat.jinja.jinja import render_recipe_with_context
from rattler_build_conda_compat.jinja.utils import _MissingUndefined
from rattler_build_conda_compat.loader import load_yaml


def test_render_recipe_with_context(snapshot) -> None:
    recipe = Path("tests/data/mamba_recipe.yaml")
    with recipe.open() as f:
        recipe_yaml = load_yaml(f)

    rendered = render_recipe_with_context(recipe_yaml)
    into_yaml = yaml.dump(rendered)

    assert into_yaml == snapshot


def test_version_to_build_string() -> None:
    assert _version_to_build_string("1.2.3") == "12"
    assert _version_to_build_string("1.2") == "12"
    assert _version_to_build_string("nothing") == "nothing"
    some_undefined = _MissingUndefined(name="python")
    assert _version_to_build_string(some_undefined) == "python_version_to_build_string"


def test_context_rendering(snapshot) -> None:
    recipe = Path("tests/data/context.yaml")
    with recipe.open() as f:
        recipe_yaml = load_yaml(f)

    rendered = render_recipe_with_context(recipe_yaml)
    into_yaml = yaml.dump(rendered)

    assert into_yaml == snapshot
