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
    url: NotRequired[str]


def get_all_url_sources(recipe: Mapping[Any, Any]) -> Iterator[str]:
    """
    Get all url sources from the recipe. This can be from a list of sources,
    a single source, or conditional and its branches.

    Arguments
    ---------
    * `recipe` - The recipe to inspect. This should be a yaml object.

    Returns
    -------
    A list of sources.
    """

    sources = recipe.get("source", None)
    sources = typing.cast(ConditionalList[Source], sources)

    # Try getting all url top-level sources
    if sources is not None:
        source_list = visit_conditional_list(sources, None)
        for source in source_list:
            if url := source.get("url"):
                yield url

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
            if url := source.get("url"):
                yield url
