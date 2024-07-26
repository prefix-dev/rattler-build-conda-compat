from __future__ import annotations

import re
import subprocess
import sys

import tomli


def get_current_branch() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])  # noqa: S603, S607
        .decode("utf-8")
        .strip()
    )


def extract_version_from_branch(branch_name: str) -> str | None:
    match = re.match(r"release/v(\d+\.\d+\.\d+)", branch_name)
    return match.group(1) if match else None


def get_version_from_file(file_path: str, field: str = "version") -> str | None:
    try:
        config = tomli.load(file_path)
        return (
            config.get("project", {}).get(field)
            or config.get("package", {}).get(field)
            or config.get(field)
        )
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except tomli.TomlDecodeError:
        print(f"Error: Unable to parse {file_path}.")
        return None


def check_for_version_changes(file_path: str) -> bool:
    diff = subprocess.check_output(["git", "diff", "--cached", file_path]).decode("utf-8")  # noqa: S607, S603
    return "version" in diff


def main() -> None:
    current_branch = get_current_branch()
    branch_version = extract_version_from_branch(current_branch)

    if not branch_version:
        # Not on a release branch, check if version is being updated
        if check_for_version_changes("pyproject.toml") or check_for_version_changes("pixi.toml"):
            print("Error: Version update detected outside of a release branch.")
            print("Please create a release branch (release/vX.Y.Z) to update the version.")
            sys.exit(1)
        print("Not on a release branch. Skipping version check.")
        sys.exit(0)

    # On a release branch, perform version check
    pyproject_version = get_version_from_file("pyproject.toml")
    pixi_version = get_version_from_file("pixi.toml")

    if pyproject_version is None or pixi_version is None:
        sys.exit(1)

    if branch_version != pyproject_version or branch_version != pixi_version:
        print("Version mismatch:")
        print(f"  Branch version: {branch_version}")
        print(f"  pyproject.toml version: {pyproject_version}")
        print(f"  pixi.toml version: {pixi_version}")
        sys.exit(1)

    print("Version check passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
