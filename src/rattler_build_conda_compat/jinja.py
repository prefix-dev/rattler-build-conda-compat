from __future__ import annotations

from typing import Any, TypedDict

import jinja2
import yaml
from jinja2 import DebugUndefined

from rattler_build_conda_compat.loader import load_yaml


class RecipeWithContext(TypedDict, total=False):
    context: dict[str, str]


class _MissingUndefined(DebugUndefined):
    def __str__(self) -> str:
        """
        By default, `DebugUndefined` return values in the form `{{ value }}`.
        `rattler-build` has a different syntax, so we need to override this method,
        and return the value in the form `${{ value }}`.
        """
        return f"${super().__str__()}"


def jinja_env() -> jinja2.Environment:
    """
    Create a `rattler-build` specific Jinja2 environment with modified syntax.
    """

    def stub_compatible_pin(*args, **kwargs) -> str:  # noqa: ARG001, ANN003, ANN002
        return f"compatible_pin {args[0]}"

    def stub_subpackage_pin(*args, **kwargs) -> str:  # noqa: ARG001, ANN003, ANN002
        return f"subpackage_pin {args[0]}"

    def version_to_build_string(some_string: str) -> str:
        """Converts some version by removing the . character and returning only the first two elements of the version)"""
        # We first split the string by whitespace and take the first part
        split = some_string.split()[0] if some_string.split() else some_string
        # We then split the string by . and take the first two parts
        parts = split.split(".")
        major = parts[0] if len(parts) > 0 else ""
        minor = parts[1] if len(parts) > 1 else ""
        return f"{major}{minor}"

    def split_filter(s: str, sep: str = " ") -> list[str]:
        """Filter that split a string by a separator"""
        return s.split(sep)

    env = jinja2.Environment(
        variable_start_string="${{",
        variable_end_string="}}",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=True,
        undefined=_MissingUndefined,
    )

    # inject rattler-build recipe functions in jinja environment
    env.globals.update(
        {
            "compiler": lambda x: x + "_compiler_stub",
            "stdlib": lambda x: x + "_stdlib_stub",
            "pin_subpackage": stub_subpackage_pin,
            "pin_compatible": stub_compatible_pin,
            "cdt": lambda *args, **kwargs: "cdt_stub",  # noqa: ARG005
        }
    )

    # inject rattler-build recipe filters in jinja environment
    env.filters.update(
        {
            "version_to_buildstring": version_to_build_string,
            "split": split_filter,
        }
    )
    return env


def load_recipe_context(context: dict[str, str], jinja_env: jinja2.Environment) -> dict[str, str]:
    """
    Load all string values from the context dictionary as Jinja2 templates.
    """
    # Process each key-value pair in the dictionary
    for key, value in context.items():
        # If the value is a string, render it as a template
        if isinstance(value, str):
            template = jinja_env.from_string(value)
            rendered_value = template.render(context)
            context[key] = rendered_value

    return context


def render_recipe_with_context(recipe_content: RecipeWithContext) -> dict[str, Any]:
    """
    Render the recipe using known values from context section.
    Unknown values are not evaluated and are kept as it is.

    Examples:
    ---
    ```python
    >>> from pathlib import Path
    >>> from rattler_build_conda_compat.loader import load_yaml
    >>> recipe_content = load_yaml((Path().resolve() / "tests" / "data" / "eval_recipe_using_context.yaml").read_text())
    >>> evaluated_context = render_recipe_with_context(recipe_content)
    >>> assert "my_value-${{ not_present_value }}" == evaluated_context["build"]["string"]
    >>>
    ```
    """
    env = jinja_env()
    context = recipe_content.get("context", {})
    # load all context templates
    context_templates = load_recipe_context(context, env)

    # render the rest of the document with the values from the context
    # and keep undefined expressions _as is_.
    template = env.from_string(yaml.dump(recipe_content))
    rendered_content = template.render(context_templates)
    return load_yaml(rendered_content)
