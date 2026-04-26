# -*- coding: utf-8 -*-

import json


class Write:
    """Write .env files (key=value pairs)."""

    @staticmethod
    def write(content: str, filepath: str, encoding: str = "utf-8") -> str:
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
        return f"Successfully wrote .env file to '{filepath}'."

    @staticmethod
    def from_dict(data: dict, encoding: str = "utf-8") -> bytes:
        lines = [f"{k}={v}" for k, v in data.items()]
        return "\n".join(lines).encode(encoding)


class Read:
    """Read .env files. Returns JSON string."""

    @staticmethod
    def read(filepath: str, encoding: str = "utf-8") -> str:
        data = {}
        with open(filepath, "r", encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    data[key.strip()] = val.strip()
                else:
                    data[line.strip()] = ""
        return json.dumps(data, ensure_ascii=False, indent=2)
