from __future__ import annotations

from pathlib import Path

import pytest
from rattler_build_conda_compat.loader import load_yaml
from rattler_build_conda_compat.recipe_sources import get_all_url_sources


@pytest.mark.parametrize(
    ("partial_recipe", "expected_output"),
    [
        ("single_source.yaml", ["https://foo.com"]),
        ("multiple_sources.yaml", ["https://foo.com", "https://bar.com"]),
        ("if_then_source.yaml", ["https://foo.com", "https://bar.com"]),
        (
            "outputs_source.yaml",
            ["https://foo.com", "https://bar.com", "https://baz.com", "https://qux.com"],
        ),
    ],
)
def test_recipe_sources(partial_recipe: str, expected_output: list[str]) -> None:
    """Test that the recipe sources are correctly extracted from the recipe"""
    path = Path(f"{Path(__file__).parent}/data/{partial_recipe}")
    recipe = load_yaml(path.read_text())
    assert list(get_all_url_sources(recipe)) == expected_output
