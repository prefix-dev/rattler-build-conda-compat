from __future__ import annotations

from typing import Any

import jinja2
import yaml

from rattler_build_conda_compat.loader import load_yaml


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
    )


def render_context(context: dict[str, str], jinja_env: jinja2.Environment) -> dict[str, str]:
    """
    Render all string values in the context dictionary as Jinja2 templates.
    """
    # Process each key-value pair in the dictionary
    for key, value in context.items():
        # If the value is a string, render it as a template
        if isinstance(value, str):
            template = jinja_env.from_string(value)
            rendered_value = template.render(context)
            context[key] = rendered_value

    return context


def eval_recipe(recipe_content: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate a recipe content using values from context section.
    """
    env = jinja_env()
    context = recipe_content.get("context", {})
    # render the context
    rendered_context = render_context(context, env)

    # render the rest of the document with the values from the context
    # and keep undefined expressions _as is_.
    template = env.from_string(yaml.dump(recipe_content))
    rendered_content = template.render(rendered_context)

    return load_yaml(rendered_content)
