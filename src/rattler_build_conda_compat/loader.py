from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import yaml

from rattler_build_conda_compat.conditional_list import visit_conditional_list
from rattler_build_conda_compat.utils import flatten_lists, remove_empty_keys

if TYPE_CHECKING:
    from collections.abc import Iterator
    from os import PathLike

SELECTOR_OPERATORS = ("and", "or", "not")


class RecipeLoader(yaml.BaseLoader):
    _namespace: dict[str, Any] | None = None
    _allow_missing_selector: bool = False

    @classmethod
    @contextmanager
    def with_namespace(
        cls: type[RecipeLoader],
        namespace: dict[str, Any] | None,
        *,
        allow_missing_selector: bool = False,
    ) -> Iterator[None]:
        try:
            cls._namespace = namespace
            cls._allow_missing_selector = allow_missing_selector
            yield
        finally:
            del cls._namespace

    def construct_sequence(  # noqa: C901, PLR0912
        self,
        node: yaml.ScalarNode | yaml.SequenceNode | yaml.MappingNode,
        deep: bool = False,  # noqa: FBT002, FBT001,
    ) -> list[yaml.ScalarNode]:
        """deep is True when creating an object/mapping recursively,
        in that case want the underlying elements available during construction
        """
        # find if then else selectors
        for sequence_idx, child_node in enumerate(node.value[:]):
            # if then is only present in MappingNode

            if isinstance(child_node, yaml.MappingNode):
                # iterate to find if there is IF first

                the_evaluated_one = None
                for idx, (key_node, value_node) in enumerate(child_node.value):
                    if key_node.value == "if":
                        # we catch the first one, let's try to find next pair of (then | else)
                        then_node_key, then_node_value = child_node.value[idx + 1]

                        if then_node_key.value != "then":
                            msg = "cannot have if without then, please reformat your variant file"
                            raise ValueError(msg)

                        try:
                            _, else_node_value = child_node.value[idx + 2]
                        except IndexError:
                            _, else_node_value = None, None

                        to_be_eval = f"{value_node.value}"

                        if self._allow_missing_selector:
                            split_selectors = [
                                selector
                                for selector in to_be_eval.split()
                                if selector not in SELECTOR_OPERATORS
                            ]
                            for selector in split_selectors:
                                if self._namespace and selector not in self._namespace:
                                    cleaned_selector = selector.strip("(").rstrip(")")
                                    self._namespace[cleaned_selector] = True

                        evaled = eval(to_be_eval, self._namespace)  # noqa: S307
                        if evaled:
                            the_evaluated_one = then_node_value
                        elif else_node_value:
                            the_evaluated_one = else_node_value

                        if the_evaluated_one:
                            node.value.remove(child_node)
                            node.value.insert(sequence_idx, the_evaluated_one)
                        else:
                            # neither the evaluation or else node is present, so we remove this if
                            node.value.remove(child_node)

        if not isinstance(node, yaml.SequenceNode):
            raise TypeError(
                None,
                None,
                f"expected a sequence node, but found {node.id!s}",
                node.start_mark,
            )

        return [self.construct_object(child, deep=deep) for child in node.value]


def load_yaml(content: str | bytes) -> Any:  # noqa: ANN401
    return yaml.load(content, Loader=yaml.BaseLoader)  # noqa: S506


def parse_recipe_config_file(
    path: PathLike[str], namespace: dict[str, Any] | None, *, allow_missing_selector: bool = False
) -> dict[str, Any]:
    with open(path) as f, RecipeLoader.with_namespace(
        namespace, allow_missing_selector=allow_missing_selector
    ):
        content = yaml.load(f, Loader=RecipeLoader)  # noqa: S506
    return flatten_lists(remove_empty_keys(content))


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
