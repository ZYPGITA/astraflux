# -*- coding: utf-8 -*-

import json


class Write:
    """Write JSON files."""

    @staticmethod
    def write(content: str, filepath: str, encoding: str = "utf-8") -> str:
        parsed = json.loads(content)
        with open(filepath, "w", encoding=encoding) as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        return f"Successfully saved JSON data to '{filepath}'."

    @staticmethod
    def format(content: str, encoding: str = "utf-8") -> bytes:
        parsed = json.loads(content)
        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
        return formatted.encode(encoding)


class Read:
    """Read JSON files."""

    @staticmethod
    def read(filepath: str, encoding: str = "utf-8") -> str:
        with open(filepath, "r", encoding=encoding) as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
