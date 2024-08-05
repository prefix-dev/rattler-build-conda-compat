from __future__ import annotations

import hashlib
import io
import re
from typing import TYPE_CHECKING, Any, Generator

import requests
from ruamel.yaml import YAML

if TYPE_CHECKING:
    from pathlib import Path

yaml = YAML()
yaml.preserve_quotes = True


def _update_build_number_in_context(recipe: dict[str, Any], new_build_number: int) -> bool:
    for key in recipe.get("context", {}):
        if key.startswith("build_") or key == "build":
            recipe["context"][key] = new_build_number
            return True
    return False


def _update_build_number_in_recipe(recipe: dict[str, Any], new_build_number: int) -> bool:
    is_modified = False
    if "build" in recipe and "number" in recipe["build"]:
        recipe["build"]["number"] = new_build_number
        is_modified = True

    if "outputs" in recipe:
        for output in recipe["outputs"]:
            if "build" in output and "number" in output["build"]:
                output["build"]["number"] = new_build_number
                is_modified = True

    return is_modified


def update_build_number(file: Path, new_build_number: int) -> str:
    # This function should be called to update the build number of the recipe
    # in the meta.yaml file.
    with file.open("r") as f:
        data = yaml.load(f)
    build_number_modified = _update_build_number_in_context(data, new_build_number)
    if not build_number_modified:
        build_number_modified = _update_build_number_in_recipe(data, new_build_number)

    with io.StringIO() as f:
        yaml.dump(data, f)
        return f.getvalue()


class CouldNotUpdateVersionError(Exception):
    NO_CONTEXT = "Could not find context in recipe"
    NO_VERSION = "Could not find version in recipe context"

    def __init__(self, message: str = "Could not update version") -> None:
        self.message = message
        super().__init__(self.message)


class Hash:
    def __init__(self, hash_type: str, hash_value: str) -> None:
        self.hash_type = hash_type
        self.hash_value = hash_value

    def __str__(self) -> str:
        return f"{self.hash_type}: {self.hash_value}"


def has_jinja_version(url: str) -> bool:
    """Check if the URL has a jinja `${{ version }}` in it."""
    pattern = r"\${{\s*version"
    return re.search(pattern, url) is not None


def flatten_all_sources(sources: list[dict[str, Any]]) -> Generator[dict[str, Any], None, None]:
    """
    Flatten all sources in a recipe. This is useful when a source is defined
    with an if/else statement. Will yield both branches of the if/else
    statement if it exists.
    """
    for source in sources:
        if "if" in source:
            yield source["then"]
            if "else" in source:
                yield source["else"]
        else:
            yield source


def update_hash(source: dict[str, Any], url: str, hash_type: Hash | None) -> None:
    # kick out any hash that is not the one we are updating
    potential_hashes = {"sha256", "md5"}
    for key in potential_hashes:
        if key in source:
            del source[key]
    if hash_type is not None:
        source[hash_type.hash_type] = hash_type.hash_value
    else:
        # download and hash the file
        hasher = hashlib.sha256()
        with requests.get(url, stream=True, timeout=100) as r:
            for chunk in r.iter_content(chunk_size=4096):
                hasher.update(chunk)
        source["sha256"] = hasher.hexdigest()


def update_version(file: Path, new_version: str, hash_type: Hash | None) -> str:
    # This function should be called to update the version of the recipe
    # in the meta.yaml file.

    with file.open("r") as f:
        data = yaml.load(f)

    if "context" not in data:
        raise CouldNotUpdateVersionError(CouldNotUpdateVersionError.NO_CONTEXT)
    if "version" not in data["context"]:
        raise CouldNotUpdateVersionError(CouldNotUpdateVersionError.NO_VERSION)

    data["context"]["version"] = new_version

    sources = data.get("source", [])
    if isinstance(sources, dict):
        sources = [sources]

    for source in flatten_all_sources(sources):
        if has_jinja_version(source.get("url", "")):
            # render the whole URL and find the hash
            urls = source["url"]
            if not isinstance(urls, list):
                urls = [urls]

            rendered_url = urls[0].replace("${{ version }}", new_version)

            update_hash(source, rendered_url, hash_type)

    with io.StringIO() as f:
        yaml.dump(data, f)
        return f.getvalue()
