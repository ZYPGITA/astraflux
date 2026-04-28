# -*- coding: utf-8 -*-

import yaml
import json


class Write:
    """Write YAML files. Content must be valid YAML string."""

    @staticmethod
    def write(content: str, filepath: str, encoding: str = "utf-8") -> str:
        parsed = yaml.safe_load(content)
        with open(filepath, "w", encoding=encoding) as f:
            yaml.dump(parsed, f, allow_unicode=True, default_flow_style=False)
        return f"Successfully saved YAML data to '{filepath}'."

    @staticmethod
    def from_dict(data: dict, encoding: str = "utf-8") -> bytes:
        return yaml.dump(data, allow_unicode=True, default_flow_style=False).encode(encoding)


class Read:
    """Read YAML files. Returns JSON string."""

    @staticmethod
    def read(filepath: str, encoding: str = "utf-8") -> str:
        with open(filepath, "r", encoding=encoding) as f:
            data = yaml.safe_load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
