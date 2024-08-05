from __future__ import annotations

import sys
import typing
from typing import Any, List, TypedDict, Union

from .conditional_list import ConditionalList, visit_conditional_list

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired

if typing.TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

OptionalUrlList = Union[str, List[str], None]


class Source(TypedDict):
    url: NotRequired[str | list[str]]
    sha256: NotRequired[str]
    md5: NotRequired[str]


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
