from __future__ import annotations

import io
import itertools
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rattler_build_conda_compat.conditional_list import visit_conditional_list
from rattler_build_conda_compat.yaml import _yaml_object

if TYPE_CHECKING:
    from os import PathLike

SELECTOR_OPERATORS = ("and", "or", "not")


def _remove_empty_keys(some_dict: dict[str, Any]) -> dict[str, Any]:
    filtered_dict = {}
    for key, value in some_dict.items():
        if isinstance(value, list) and len(value) == 0:
            continue
        filtered_dict[key] = value

    return filtered_dict


def _flatten_lists(some_dict: dict[str, Any]) -> dict[str, Any]:
    result_dict: dict[str, Any] = {}
    for key, value in some_dict.items():
        if isinstance(value, dict):
            result_dict[key] = _flatten_lists(value)
        elif isinstance(value, list) and value and isinstance(value[0], list):
            result_dict[key] = list(itertools.chain(*value))
        else:
            result_dict[key] = value

    return result_dict


def load_yaml(content: str | bytes) -> Any:  # noqa: ANN401
    yaml = _yaml_object()
    with io.StringIO(content) as f:
        return yaml.load(f)


def _eval_selector(
    condition: str, namespace: dict[str, Any], *, allow_missing_selector: bool = False
) -> bool:
    # evaluate the selector expression
    if allow_missing_selector:
        namespace = namespace.copy()
        split_selectors = [
            selector for selector in condition.split() if selector not in SELECTOR_OPERATORS
        ]
        for selector in split_selectors:
            if namespace and selector not in namespace:
                cleaned_selector = selector.strip("(").rstrip(")")
                namespace[cleaned_selector] = True

    return eval(condition, namespace)  # noqa: S307


def _render_recipe(
    yaml_object: Any,  # noqa: ANN401
    context: dict[str, Any],
    *,
    allow_missing_selector: bool = False,
) -> Any:  # noqa: ANN401
    # recursively go through the yaml object, and convert any lists with conditional if/else statements
    # into a single list
    if isinstance(yaml_object, dict):
        for key, value in yaml_object.items():
            yaml_object[key] = _render_recipe(
                value, context, allow_missing_selector=allow_missing_selector
            )
    elif isinstance(yaml_object, list):
        # if the list is a conditional list, evaluate it
        yaml_object = list(
            visit_conditional_list(
                yaml_object,
                lambda x: _eval_selector(x, context, allow_missing_selector=allow_missing_selector),
            )
        )
    return yaml_object


def parse_recipe_config_file(
    path: PathLike[str], namespace: dict[str, Any] | None, *, allow_missing_selector: bool = False
) -> dict[str, Any]:
    yaml = _yaml_object()
    with Path(path).open() as f:
        raw_yaml_content = yaml.load(f)

    # render the recipe with the context
    rendered = _render_recipe(
        raw_yaml_content, namespace, allow_missing_selector=allow_missing_selector
    )
    return _flatten_lists(_remove_empty_keys(rendered))


def load_all_requirements(content: dict[str, Any]) -> dict[str, Any]:
    requirements_section = dict(content.get("requirements", {}))
    if not requirements_section:
        return {}

    for section in requirements_section:
        section_reqs = requirements_section[section]
        if not section_reqs:
            continue

        requirements_section[section] = list(visit_conditional_list(section_reqs))

    return requirements_section


def load_all_tests(content: dict[str, Any]) -> list[dict]:
    tests_section = content.get("tests", [])
    if not tests_section:
        return []

    evaluated_tests = []

    for section in tests_section:
        evaluated_tests.extend(list(visit_conditional_list(section)))

    return evaluated_tests
