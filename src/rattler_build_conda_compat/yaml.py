import io
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq


# Custom constructor for loading floats as strings
def float_as_string_constructor(loader, node) -> str:  # noqa: ANN001
    return loader.construct_scalar(node)


def convert_to_plain_types(data: Any) -> Any:  # noqa: ANN401
    if isinstance(data, CommentedMap):
        return {convert_to_plain_types(k): convert_to_plain_types(v) for k, v in data.items()}
    if isinstance(data, (CommentedSeq, list)):
        return [convert_to_plain_types(item) for item in data]
    if isinstance(data, dict):
        return {convert_to_plain_types(k): convert_to_plain_types(v) for k, v in data.items()}
    return data


def _yaml_object() -> YAML:
    yaml = YAML(typ="rt")
    yaml.Constructor.add_constructor("tag:yaml.org,2002:float", float_as_string_constructor)
    yaml.allow_duplicate_keys = False
    yaml.preserve_quotes = True
    yaml.width = 320
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def _dump_yaml_to_string(data: Any) -> str:  # noqa: ANN401
    yaml = _yaml_object()
    with io.StringIO() as f:
        yaml.dump(data, f)
        return f.getvalue()
