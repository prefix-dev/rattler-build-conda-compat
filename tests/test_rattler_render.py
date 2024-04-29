import os
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


def test_environ_is_passed_to_rattler_build(env_recipe, snapshot):
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
        assert snapshot == all_used_variants

    finally:
        os.environ.pop("TEST_SHOULD_BE_PASSED", None)
