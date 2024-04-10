from rattler_build_conda_compat.render import render
from rattler_build_conda_compat.loader import parse_recipe_config_file


def test_render_recipe(python_recipe, unix_namespace, snapshot):
    variants = parse_recipe_config_file(
        str(python_recipe / "variants.yaml"), unix_namespace
    )

    rendered = render(
        str(python_recipe), variants=variants, platform="linux", arch="64"
    )

    all_used_variants = [meta[0].get_used_variant() for meta in rendered]

    assert len(all_used_variants) == 2

    assert snapshot == all_used_variants
