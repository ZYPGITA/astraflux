# -*- coding: utf-8 -*-

import json

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore
import tomli_w


class Write:
    """Write TOML files. Content must be valid TOML string."""

    @staticmethod
    def write(content: str, filepath: str, encoding: str = "utf-8") -> str:
        parsed = tomllib.loads(content)
        with open(filepath, "wb") as f:
            tomli_w.dump(parsed, f)
        return f"Successfully saved TOML data to '{filepath}'."

    @staticmethod
    def from_dict(data: dict) -> bytes:
        return tomli_w.dumps(data).encode("utf-8")


class Read:
    """Read TOML files. Returns JSON string."""

    @staticmethod
    def read(filepath: str, encoding: str = "utf-8") -> str:
        with open(filepath, "rb") as f:
            data = tomllib.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
