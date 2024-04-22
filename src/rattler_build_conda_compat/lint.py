import re

from inspect import cleandoc
import os.path
import string
import textwrap
import ruamel.yaml
from typing import Any, Sequence
import requests
from conda.models.version import VersionOrder
from functools import cache
from jsonschema import Draft202012Validator
from jsonschema import ValidationError
from textwrap import indent

SCHEMA_URL = "https://raw.githubusercontent.com/prefix-dev/recipe-format/main/schema.json"

REQUIREMENTS_ORDER = ["build", "host", "run"]

ALLOWED_LICENSE_FAMILIES = """
AGPL
LGPL
GPL3
GPL2
GPL
BSD
MIT
APACHE
PSF
CC
MOZILLA
PUBLIC-DOMAIN
PROPRIETARY
OTHER
NONE
""".split()

# regular expressions
GPL2_REGEX = re.compile("GPL[^3]*2")  # match GPL2
GPL3_REGEX = re.compile("GPL[^2]*3")  # match GPL3
GPL23_REGEX = re.compile("GPL[^2]*>= *2")  # match GPL >= 2
CC_REGEX = re.compile(r"CC\w+")  # match CC
PUNK_REGEX = re.compile("[%s]" % re.escape(string.punctuation))  # removes punks

JINJA_VAR_PAT = re.compile(r"${{(.*?)}}")

def _format_validation_msg(error: ValidationError):
    return cleandoc(
        f"""
        In recipe.yaml: `{error.instance}`.
{indent(error.message, " " * 12 + "> ")}
        """
    )



@cache
def get_recipe_schema() -> dict[Any, Any]:
    return requests.get(SCHEMA_URL).json()


def yaml_reader():
    # define global yaml API
    # roundrip-loader and allowing duplicate keys
    # for handling # [filter] / # [not filter]
    # Don't use a global variable for this as a global
    # variable will make conda-smithy thread unsafe.
    yaml = ruamel.yaml.YAML(typ="rt")
    yaml.allow_duplicate_keys = True
    return yaml




def lint_recipe_yaml_by_schema(recipe_file):
    schema = get_recipe_schema()
    yaml = yaml_reader()

    with open(recipe_file) as fh:
        meta = yaml.load(fh)

    validator = Draft202012Validator(schema)

    lints = []

    for error in validator.iter_errors(meta):
        lints.append(_format_validation_msg(error))
    return lints



def lint_about_contents(about_section, lints):
    for about_item in ["homepage", "license", "summary"]:
        # if the section doesn't exist, or is just empty, lint it.
        if not about_section.get(about_item, ""):
            lints.append(
                "The {} item is expected in the about section."
                "".format(about_item)
            ) 



def lint_recipe_maintainers(maintainers_section, lints):
    if not maintainers_section:
        lints.append(
            "The recipe could do with some maintainers listed in "
            "the `extra/recipe-maintainers` section."
        )

    if not (
        isinstance(maintainers_section, Sequence)
        and not isinstance(maintainers_section, str) 
    ):
        lints.append("Recipe maintainers should be a json list.")

def lint_recipe_tests(test_section=dict(), outputs_section=list(), lints=list()) -> list[str]:
    TEST_KEYS = {"script", "python"}
    hints = []

    if not any(key in TEST_KEYS for key in test_section):
        if not outputs_section:
            lints.append("The recipe must have some tests.")
        else:
            has_outputs_test = False
            no_test_hints = []
            for section in outputs_section:
                test_section = section.get("test", {})
                if any(key in TEST_KEYS for key in test_section):
                    has_outputs_test = True
                else:
                    no_test_hints.append(
                        "It looks like the '{}' output doesn't "
                        "have any tests.".format(section.get("name", "???"))
                        )
            if has_outputs_test:
                hints.extend(no_test_hints)
            else:
                lints.append("The recipe must have some tests.")

    return hints

def lint_license_not_unknown(license: str, lints: list):
    license = license.lower()
    if "unknown" == license.strip():
        lints.append("The recipe license cannot be unknown.")


def lint_build_number(build_section: dict, lints: list):
    build_number = build_section.get("number", None)
    if build_number is None:
        lints.append("The recipe must have a `build/number` section.")

def lint_requirements_order(requirements_section: dict, lints: list):
    seen_requirements = [
        k for k in requirements_section if k in REQUIREMENTS_ORDER
    ]
    requirements_order_sorted = sorted(
        seen_requirements, key=REQUIREMENTS_ORDER.index
    )
    if seen_requirements != requirements_order_sorted:
        lints.append(
            "The `requirements/` sections should be defined "
            "in the following order: "
            + ", ".join(REQUIREMENTS_ORDER)
            + "; instead saw: "
            + ", ".join(seen_requirements)
            + "."
        )

def lint_package_version(package_section: dict, context_section: dict):
    package_ver = str(package_section.get("version"))
    context_ver = str(context_section.get("version"))
    ver = package_ver if package_ver is not None and not package_ver.startswith("$") else context_ver

    try:
        VersionOrder(ver)
    except:
        return "Package version {} doesn't match conda spec".format(ver)

def lint_files_have_hash(sources_section: list, lints: list):
    for source_section in sources_section:
        if "url" in source_section and not (
            {"sha1", "sha256", "md5"} & set(source_section.keys())
        ):
            lints.append(
                "When defining a source/url please add a sha256, sha1 "
                "or md5 checksum (sha256 preferably)."
            )

def lint_legacy_compilers(build_reqs):
    if build_reqs and ("toolchain" in build_reqs):
        return """Using toolchain directly in this manner is deprecated. Consider
            using the compilers outlined
            [here](https://conda-forge.org/docs/maintainer/knowledge_base.html#compilers)."""


def lint_has_recipe_file(about_section, lints):
    license_file = about_section.get("license_file", None)
    if not license_file:
        lints.append("license_file entry is missing, but is required.")

def lint_package_name(package_section: dict, context_section: dict):
    package_name = str(package_section.get("name"))
    context_name = str(context_section.get("name"))
    ver = package_name if package_name is not None and not package_name.startswith("$") else context_name

    recipe_name = package_section.get("name", "").strip()
    if re.match(r"^[a-z0-9_\-.]+$", recipe_name) is None:
        return """
            Recipe name has invalid characters. only lowercase alpha, numeric,
            underscores, hyphens and dots allowed """
    


def lint_legacy_patterns(requirements_section):
    lints = []
    build_reqs = requirements_section.get("build", None)
    if build_reqs and ("numpy x.x" in build_reqs):
        lints.append(
            "Using pinned numpy packages is a deprecated pattern.  Consider "
            "using the method outlined "
            "[here](https://conda-forge.org/docs/maintainer/knowledge_base.html#linking-numpy)."
        )
    return lints


def lint_usage_of_selectors_for_noarch(noarch_value, build_section, requirements_section):
    lints = []

    for section in requirements_section:
        section_requirements = requirements_section[section]

        if any(isinstance(req, dict) for req in section_requirements):
            lints.append(
                "`noarch` packages can't have skips with selectors. If "
                "the selectors are necessary, please remove "
                "`noarch: {}`.".format(noarch_value)
            )
            break
    
    if "skip" in build_section:
        lints.append(
            "`noarch` packages can't have skips with selectors. If "
            "the selectors are necessary, please remove "
            "`noarch: {}`.".format(noarch_value)
        )

    return lints

def lint_usage_of_single_space_in_pinned_requirements(requirements_section: dict):
    def verify_requirement(requirement):
        import re
        pattern = r'\b\w+\b(\s*(>=|>|<=|<|==)\s*\d+\.\d+)?'
        if re.match(pattern, requirement):
            return True
        return False

    lints = []
    for section, requirements in requirements_section.items():
        for req in requirements:
            is_valid = verify_requirement(req)
            if not is_valid:
                lints.append(f"``requirements: {section}: {req}`` should not "
                        "contain a space between relational operator and the version, i.e. "
                        "``{name} {pin}`` and must contain a space between the name and the pin")
    return lints

def lint_non_noarch_dont_constrain_python_and_rbase(requirements_section):
    check_languages = ["python", "r-base"]
    host_reqs = requirements_section.get("host") or []
    run_reqs = requirements_section.get("run") or []
    
    lints = []
    
    for language in check_languages:
        filtered_host_reqs = [req for req in host_reqs if req.startswith(f"{language} ")]
        filtered_run_reqs = [req for req in run_reqs if req.startswith(f"{language} ")]
        
        if filtered_host_reqs and not filtered_run_reqs:
            lints.append(f"If {language} is a host requirement, it should be a run requirement.")
        
        for reqs in [filtered_host_reqs, filtered_run_reqs]:
            if language not in reqs:
                for req in reqs:
                    constraint = req.split(" ", 1)[1]
                    if constraint.startswith(">") or constraint.startswith("<") or constraint.startswith("="):
                        lints.append(f"Non noarch packages should have {language} requirement without any version constraints.")
    
    return lints

def lint_variable_reference_should_have_space(recipe_dir, recipe_file):
    hints = []
    if recipe_dir is not None and os.path.exists(recipe_file):
        bad_vars = []
        bad_lines = []
        with open(recipe_file, "r") as fh:
            for i, line in enumerate(fh.readlines()):
                for m in JINJA_VAR_PAT.finditer(line):
                    if m.group(1) is not None:
                        var = m.group(1)
                        if var != " %s " % var.strip():
                            bad_vars.append(m.group(1).strip())
                            bad_lines.append(i + 1)
        if bad_vars:
            hints.append(
                "Jinja2 variable references are suggested to "
                "take a ``{{<one space><variable name><one space>}}``"
                " form. See lines %s." % (bad_lines,)
            )

    return hints

def lint_lower_bound_on_python(run_requirements, outputs_section):
    lints = []
    # if noarch_value == "python" and not outputs_section:
    for req in run_requirements:
        if (req.strip().split()[0] == "python") and (req != "python"):
            break
    else:
        lints.append(
            "noarch: python recipes are required to have a lower bound "
            "on the python version. Typically this means putting "
            "`python >=3.6` in **both** `host` and `run` but you should check "
            "upstream for the package's Python compatibility."
        )

def hint_pip_usage(build_section):
    hints = []

    if "script" in build_section:
        scripts = build_section["script"]
        if isinstance(scripts, str):
            scripts = [scripts]
        for script in scripts:
            if "python setup.py install" in script:
                hints.append(
                    "Whenever possible python packages should use pip. "
                    "See https://conda-forge.org/docs/maintainer/adding_pkgs.html#use-pip"
                )
    return hints


def hint_noarch_usage(build_section, requirement_section: dict):
    build_reqs = requirement_section.get("build_reqs", None)
    hints = []
    if (
        # move outside the call
        # noarch_value is None
        build_reqs
        and not any(["_compiler_stub" in b for b in build_reqs])
        and ("pip" in build_reqs)
        # move outside the call
        # and (is_staged_recipes or not conda_forge)
    ):
        no_arch_possible = True
        if "skip" in build_section:
            no_arch_possible = False
        
        for _, section_requirements in requirement_section.items():
            if any(isinstance(requirement, dict) for requirement in section_requirements):
                no_arch_possible = False
                break
        
        if no_arch_possible:
            hints.append(
                "Whenever possible python packages should use noarch. "
                "See https://conda-forge.org/docs/maintainer/knowledge_base.html#noarch-builds"
            )

    return hints   




def normalize_license(s):
    """Set to ALL CAPS, replace common GPL patterns, and strip"""
    s = s.upper()
    s = re.sub("GENERAL PUBLIC LICENSE", "GPL", s)
    s = re.sub("LESSER *", "L", s)
    s = re.sub("AFFERO *", "A", s)
    return s.strip()

def remove_special_characters(s):
    """Remove punctuation, spaces, tabs, and line feeds"""
    s = PUNK_REGEX.sub(" ", s)
    s = re.sub(r"\s+", "", s)
    return s

def indent(message):
    textwrap.fill(textwrap.dedent(message))

def ensure_valid_license_family(about_section):
    try:
        license_family = about_section["license_family"]
    except KeyError:
        return
    allowed_families = [
        remove_special_characters(normalize_license(fam)) for fam in ALLOWED_LICENSE_FAMILIES
    ]
    if remove_special_characters(normalize_license(license_family)) not in allowed_families:
        raise RuntimeError(
            indent(
                f"about/license_family '{license_family}' not allowed. "
                f"Allowed families are {", ".join(sorted(ALLOWED_LICENSE_FAMILIES))}."
            )
        )