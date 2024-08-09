from ruamel.yaml import YAML
from typing import Any
import io

def _yaml_object() -> YAML:
    yaml = YAML(typ="rt")
    yaml.allow_duplicate_keys = False
    yaml.preserve_quotes = True
    yaml.width = 320
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml

def _dump_yaml_to_string(data: Any) -> str:
    yaml = _yaml_object()
    with io.StringIO() as f:
        yaml.dump(data, f)
        return f.getvalue()
