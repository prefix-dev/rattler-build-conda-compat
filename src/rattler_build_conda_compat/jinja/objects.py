from __future__ import annotations

import os

import jinja2
from jinja2 import DebugUndefined


class _MissingUndefined(DebugUndefined):
    def __str__(self) -> str:
        """
        By default, `DebugUndefined` return values in the form `{{ value }}`.
        `rattler-build` has a different syntax, so we need to override this method,
        and return the value in the form `${{ value }}`.
        """
        return f"${super().__str__()}"


class _Env:
    """A class to represent the env object used in rattler-build recipe."""

    def get(self, env_var: str, default: str | None) -> str:
        try:
            return str(os.environ[env_var])
        except KeyError:
            if default:
                return default
            return env_var

    def exists(self, env_var: str) -> bool:
        return env_var in os.environ


def _stub_compatible_pin(*args, **kwargs) -> str:  # noqa: ARG001, ANN003, ANN002
    return f"compatible_pin {args[0]}"


def _stub_subpackage_pin(*args, **kwargs) -> str:  # noqa: ARG001, ANN003, ANN002
    return f"subpackage_pin {args[0]}"


def _version_to_build_string(some_string: str | _MissingUndefined) -> str:
    """
    Converts some version by removing the . character and returning only the first two elements of the version.
    If piped value is undefined, it returns the undefined value as is.
    """
    if isinstance(some_string, _MissingUndefined):
        inner_value = f"{some_string._undefined_name} | version_to_build_string"  # noqa: SLF001
        return f"${{{{ {inner_value} }}}}"
    # We first split the string by whitespace and take the first part
    split = some_string.split()[0] if some_string.split() else some_string
    # We then split the string by . and take the first two parts
    parts = split.split(".")
    major = parts[0] if len(parts) > 0 else ""
    minor = parts[1] if len(parts) > 1 else ""
    return f"{major}{minor}"


def _split_filter(s: str, sep: str = " ") -> list[str]:
    """Filter that split a string by a separator"""
    return s.split(sep)


def jinja_env() -> jinja2.Environment:
    """
    Create a `rattler-build` specific Jinja2 environment with modified syntax.
    """

    env = jinja2.Environment(
        variable_start_string="${{",
        variable_end_string="}}",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=True,
        undefined=_MissingUndefined,
    )

    env_obj = _Env()

    # inject rattler-build recipe functions in jinja environment
    env.globals.update(
        {
            "compiler": lambda x: x + "_compiler_stub",
            "stdlib": lambda x: x + "_stdlib_stub",
            "pin_subpackage": _stub_subpackage_pin,
            "pin_compatible": _stub_compatible_pin,
            "cdt": lambda *args, **kwargs: "cdt_stub",  # noqa: ARG005
            "env": env_obj,
        }
    )

    # inject rattler-build recipe filters in jinja environment
    env.filters.update(
        {
            "version_to_buildstring": _version_to_build_string,
            "split": _split_filter,
        }
    )
    return env
