from __future__ import annotations

import sys
import typing
from dataclasses import dataclass
from typing import Any, List, Union

from rattler_build_conda_compat.jinja.jinja import render_recipe_with_context
from rattler_build_conda_compat.loader import _eval_selector
from rattler_build_conda_compat.variant_config import variant_combinations
from rattler_build_conda_compat.yaml import convert_to_plain_types

from .conditional_list import ConditionalList, visit_conditional_list

if sys.version_info < (3, 11):
    pass
else:
    pass

if typing.TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

OptionalUrlList = Union[str, List[str], None]


@dataclass(frozen=True)
class Source:
    url: str | list[str]
    sha256: str | None = None
    md5: str | None = None

    def __getitem__(self, key: str) -> str | list[str] | None:
        return self.__dict__[key]

    def __eq__(self, other: Source) -> bool:
        if not isinstance(other, Source):
            return NotImplemented
        return (self.url, self.sha256, self.md5) == (other.url, other.sha256, other.md5)

    def __hash__(self) -> int:
        return hash((tuple(self.url), self.sha256, self.md5))


def get_all_sources(recipe: Mapping[Any, Any]) -> Iterator[Source]:
    """
    Get all sources from the recipe. This can be from a list of sources,
    a single source, or conditional and its branches.

    Arguments
    ---------
    * `recipe` - The recipe to inspect. This should be a yaml object.

    Returns
    -------
    A list of source objects.
    """
    sources = recipe.get("source", None)
    sources = typing.cast(ConditionalList[Source], sources)

    # Try getting all url top-level sources
    if sources is not None:
        source_list = visit_conditional_list(sources, None)
        for source in source_list:
            yield source

    outputs = recipe.get("outputs", None)
    if outputs is None:
        return

    outputs = visit_conditional_list(outputs, None)
    for output in outputs:
        sources = output.get("source", None)
        sources = typing.cast(ConditionalList[Source], sources)
        if sources is None:
            continue
        source_list = visit_conditional_list(sources, None)
        for source in source_list:
            yield source


def get_all_url_sources(recipe: Mapping[Any, Any]) -> Iterator[str]:
    """
    Get all url sources from the recipe. This can be from a list of sources,
    a single source, or conditional and its branches.

    Arguments
    ---------
    * `recipe` - The recipe to inspect. This should be a yaml object.

    Returns
    -------
    A list of URLs.
    """

    def get_first_url(source: Mapping[str, Any]) -> str:
        if isinstance(source["url"], list):
            return source["url"][0]
        return source["url"]

    return (get_first_url(source) for source in get_all_sources(recipe) if "url" in source)


def render_all_sources(
    recipe: Mapping[Any, Any],
    variants: [Mapping[Any, Any]],
    override_version: str | None = None,
) -> set[Source]:
    """
    This function should render _all_ URL sources with the
    """
    if override_version is not None:
        recipe["context"]["version"] = override_version

    final_sources = set()
    for v in variants:
        combinations = variant_combinations(v)
        for combination in combinations:
            rendered = render_recipe_with_context(recipe, combination)
            # now evaluate the if / else statements
            sources = rendered.get("source")
            if sources:
                if not isinstance(sources, list):
                    sources = [sources]

                for elem in visit_conditional_list(
                    sources, lambda x, combination=combination: _eval_selector(x, combination)
                ):
                    if "url" in elem:
                        plain_elem = convert_to_plain_types(elem)
                        as_url = Source(
                            url=plain_elem["url"],
                            sha256=plain_elem.get("sha256"),
                            md5=plain_elem.get("md5"),
                        )
                        final_sources.add(as_url)

    return final_sources
