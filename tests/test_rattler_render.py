from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any
from pathlib import Path

from rattler_build_conda_compat.loader import parse_recipe_config_file, load_yaml, eval_jinja
from rattler_build_conda_compat.render import render

if TYPE_CHECKING:
    from pathlib import Path


def test_render_recipe(python_recipe: Path, unix_namespace: dict[str, Any], snapshot) -> None:
    variants = parse_recipe_config_file(str(python_recipe / "variants.yaml"), unix_namespace)

    rendered = render(str(python_recipe), variants=variants, platform="linux", arch="64")

    all_used_variants = [meta[0].get_used_variant() for meta in rendered]

    assert len(all_used_variants) == 2

    assert snapshot == all_used_variants


def test_environ_is_passed_to_rattler_build(env_recipe, snapshot) -> None:
    try:
        os.environ["TEST_SHOULD_BE_PASSED"] = "false"
        rendered = render(str(env_recipe), platform="linux", arch="64")
        all_used_variants = [meta[0].meta for meta in rendered]
        assert len(all_used_variants) == 1
        # for this scenario recipe should not be rendered
        assert snapshot == all_used_variants

        os.environ["TEST_SHOULD_BE_PASSED"] = "true"

        rendered = render(str(env_recipe), platform="linux", arch="64")

        all_used_variants = [meta[0].meta for meta in rendered]
        assert len(all_used_variants) == 1
        # for this scenario recipe should be rendered
        assert snapshot == all_used_variants[0]["build_configuration"]["variant"]

    finally:
        os.environ.pop("TEST_SHOULD_BE_PASSED", None)


def test_render_context(snapshot) -> None:
    recipe = Path("tests/data/context.yaml")
    with recipe.open() as f:
        recipe_yaml = load_yaml(f)

    rendered = eval_jinja(recipe_yaml)
    assert rendered == snapshot