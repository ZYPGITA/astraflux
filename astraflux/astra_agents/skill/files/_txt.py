# -*- coding: utf-8 -*-


class Write:
    """Write plain text files (.txt, .log, .md, .rst)."""

    @staticmethod
    def write(content: str, filepath: str, encoding: str = "utf-8") -> str:
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{filepath}'."

    @staticmethod
    def format(content: str, encoding: str = "utf-8") -> bytes:
        return content.encode(encoding)


class Read:
    """Read plain text files (.txt, .log, .md, .rst)."""

    @staticmethod
    def read(filepath: str, encoding: str = "utf-8") -> str:
        with open(filepath, "r", encoding=encoding) as f:
            content = f.read()
        return content
