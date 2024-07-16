import typing
from typing import Any, Iterator, Mapping, NotRequired, TypedDict

from .conditional_list import ConditionalList, visit_conditional_list

OptionalUrlList = str | list[str] | None


# TODO @tdejager: use the actual recipe type at some point
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
        sources = visit_conditional_list(sources, None)
        for source in sources:
            if "url" in source:
                yield source["url"]

    outputs = recipe.get("outputs", None)
    if outputs is None:
        return

    outputs = visit_conditional_list(outputs, None)
    for output in outputs:
        sources = output.get("source", None)
        sources = typing.cast(ConditionalList[Source], sources)
        if sources is None:
            return
        sources = visit_conditional_list(sources, None)
        for source in sources:
            if "url" in source:
                yield source["url"]
