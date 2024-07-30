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
    return jinja2.Environment(
        variable_start_string="${{",
        variable_end_string="}}",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=True,
        undefined=_MissingUndefined,
    )


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
