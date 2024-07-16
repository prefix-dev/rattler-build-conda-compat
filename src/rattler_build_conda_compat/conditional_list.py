from __future__ import annotations

from typing import Any, Callable, Generator, Generic, TypeVar, Union

T = TypeVar("T")


class IfStatement(Generic[T]):
    if_: Any
    then: T | list[T]
    else_: T | list[T] | None


ConditionalList = Union[T, "IfStatement[T]", list[Union[T, "IfStatement[T]"]]]


def visit_conditional_list(  # noqa: C901
    value: ConditionalList[T], evaluator: Callable[[Any], bool] | None = None
) -> Generator[T, None, None]:
    """
    A function that yields individual branches of a conditional list.

    Arguments
    ---------
    * `value` - The value to evaluate
    * `evaluator` - An optional evaluator to evaluate the `if` expression.

    Returns
    -------
    A generator that yields the individual branches.
    """

    def yield_from_list(value: list[T] | T) -> Generator[T, None, None]:
        if isinstance(value, list):
            yield from value
        else:
            yield value

    if not isinstance(value, list):
        value = [value]

    for element in value:
        if isinstance(element, dict):
            if (expr := element.get("if", None)) is not None:
                then = element.get("then")
                otherwise = element.get("else")
                # Evaluate the if expression if the evaluator is provided
                if evaluator:
                    if evaluator(expr):
                        yield from yield_from_list(then)
                    elif otherwise:
                        yield from yield_from_list(otherwise)
                # Otherwise, just yield the branches
                else:
                    yield from yield_from_list(then)
                    if otherwise:
                        yield from yield_from_list(otherwise)
            else:
                # In this case its not an if statement
                yield element
        # If the element is not a dictionary, just yield it
        else:
            # (tim) I get a pyright error here, but I don't know how to fix it
            yield element
