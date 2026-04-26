# -*- coding: utf-8 -*-

import io
import csv
import json


class Write:
    """Write CSV/TSV files. Content must be a JSON array of objects."""

    @staticmethod
    def write(content: str, filepath: str, encoding: str = "utf-8") -> str:
        data = json.loads(content)
        if not isinstance(data, list) or len(data) == 0:
            return "Data is empty or not a list. Nothing to write."
        with open(filepath, "w", encoding=encoding, newline="") as f:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return f"Successfully saved {len(data)} rows to CSV at '{filepath}'."

    @staticmethod
    def format(content: str, encoding: str = "utf-8") -> bytes:
        data = json.loads(content)
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Data must be a non-empty list of objects.")
        buf = io.StringIO()
        fieldnames = data[0].keys()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        return buf.getvalue().encode(encoding)


class Read:
    """Read CSV/TSV files. Returns JSON array of objects."""

    @staticmethod
    def read(filepath: str, encoding: str = "utf-8") -> str:
        with open(filepath, "r", encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
        return json.dumps(data, ensure_ascii=False, indent=2)
