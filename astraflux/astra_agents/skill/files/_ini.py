# -*- coding: utf-8 -*-

import io
import json
from configparser import ConfigParser


class Write:
    """Write INI/CFG files. Content must be valid INI-style string."""

    @staticmethod
    def write(content: str, filepath: str, encoding: str = "utf-8") -> str:
        parser = ConfigParser()
        parser.read_string(content)
        with open(filepath, "w", encoding=encoding) as f:
            parser.write(f)
        return f"Successfully wrote INI/CFG file to '{filepath}'."

    @staticmethod
    def from_dict(data: dict, encoding: str = "utf-8") -> bytes:
        parser = ConfigParser()
        for section, options in data.items():
            parser[section] = options
        buf = io.StringIO()
        parser.write(buf)
        return buf.getvalue().encode(encoding)


class Read:
    """Read INI/CFG files. Returns JSON string."""

    @staticmethod
    def read(filepath: str, encoding: str = "utf-8") -> str:
        parser = ConfigParser()
        parser.read(filepath, encoding=encoding)
        data = {section: dict(parser[section]) for section in parser.sections()}
        return json.dumps(data, ensure_ascii=False, indent=2)
