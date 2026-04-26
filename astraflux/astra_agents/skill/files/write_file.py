# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from agents import function_tool
import xml.etree.ElementTree as Et

from astraflux.astra_agents.skill.files._txt import Write as TxtWrite
from astraflux.astra_agents.skill.files._json import Write as JsonWrite
from astraflux.astra_agents.skill.files._csv import Write as CsvWrite
from astraflux.astra_agents.skill.files._yaml import Write as YamlWrite
from astraflux.astra_agents.skill.files._toml import Write as TomlWrite
from astraflux.astra_agents.skill.files._ini import Write as IniWrite
from astraflux.astra_agents.skill.files._env import Write as EnvWrite
from astraflux.astra_agents.skill.files._excel import Write as ExcelWrite


def _ensure_dir(filepath: str) -> None:
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)


def _infer_file_type(filepath: str) -> str:
    fname = Path(filepath).name.lower()
    ext = Path(filepath).suffix.lower()
    if fname == '.env':
        return 'env'
    mapping = {
        '.txt': 'txt', '.log': 'txt', '.md': 'txt', '.rst': 'txt',
        '.json': 'json',
        '.csv': 'csv', '.tsv': 'csv',
        '.xml': 'xml', '.plist': 'xml',
        '.yaml': 'yaml', '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini', '.cfg': 'ini', '.conf': 'ini',
        '.xlsx': 'excel', '.xls': 'excel',
    }
    return mapping.get(ext, 'txt')


_WRITERS = {
    'txt':   TxtWrite,
    'json':  JsonWrite,
    'csv':   CsvWrite,
    'xml':   None,  # handled inline
    'yaml':  YamlWrite,
    'toml':  TomlWrite,
    'ini':   IniWrite,
    'env':   EnvWrite,
    'excel': ExcelWrite,
}


@function_tool
def write_file(content: str, filepath: str, encoding: str = "utf-8", file_type: str = None) -> str:
    """
    Unified entry point for writing files in various formats.

    Automatically detects the target format from the file extension or
    an explicit file_type argument, parses/validates the content, and
    writes it to disk with proper formatting.

    Supported formats:
      - txt / log / md / rst  — plain text (written as-is)
      - json                  — JSON (content must be valid JSON string)
      - csv / tsv             — CSV  (content must be JSON array of objects)
      - xml                   — XML  (content must be well-formed XML)
      - yaml / yml            — YAML (content must be valid YAML)
      - toml                  — TOML (requires tomli-w; content must be valid TOML)
      - ini / cfg / conf      — INI-style config
      - env                   — key=value environment file
      - xlsx / xls            — Excel (requires openpyxl; content must be JSON array of objects)

    Args:
        content (str):  The content to write. For structured formats (json, csv,
                        yaml, toml) this must be a valid serialized string.
        filepath (str): Output file path. Parent directories created automatically.
        encoding (str): Character encoding. Default is 'utf-8'.
        file_type (str, optional): Explicit format override. If omitted, the
                        format is inferred from the file extension.

    Returns:
        str: A human-readable message describing the result or error.
    """
    # 1. Determine file type
    if not file_type:
        file_type = _infer_file_type(filepath)
    else:
        file_type = file_type.lower()

    # 2. Ensure directory exists
    try:
        _ensure_dir(filepath)
    except PermissionError:
        return f"Permission denied: Cannot create directory for '{filepath}'."
    except OSError as e:
        return f"Failed to create directory: {str(e)}"

    # 3. Select writer
    writer_class = _WRITERS.get(file_type)
    if writer_class is None and file_type == 'xml':
        from astraflux.astra_agents.skill.files._xml import Write as XmlWrite
        writer_class = XmlWrite
    if writer_class is None:
        supported = ', '.join(f"'{k}'" for k in _WRITERS)
        return f"Unsupported file type '{file_type}'. Supported: {supported}."

    # 4. Write with format-specific error handling
    try:
        return writer_class.write(content, filepath, encoding)
    except json.JSONDecodeError as e:
        return f"JSON parse error: {str(e)}. Content must be valid JSON."
    except Et.ParseError as e:
        return f"XML parse error: {str(e)}. Content must be well-formed XML."
    except PermissionError:
        return f"Permission denied: Cannot write to '{filepath}'."
    except ImportError as e:
        pkg = str(e).rsplit(' ', 1)[-1].strip("'")
        return f"Missing dependency: {str(e)}. Install with: pip install {pkg}"
    except Exception as e:
        return f"Failed to write file: {str(e)}"


@function_tool
def show_format_example(file_type: str = "json") -> str:
    """
    Returns a template/example snippet for a given file format.

    Args:
        file_type (str): One of: json, csv, yaml, toml, xml, ini, env, txt.

    Returns:
        str: An example or schema description for the requested format.
    """
    examples = {
        "json":     '{"name": "Alice", "age": 30, "skills": ["Python", "Go"]}',
        "csv":      '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]',
        "yaml":     "name: Alice\nage: 30\nskills:\n  - Python\n  - Go",
        "toml":     'title = "Example"\n[owner]\nname = "Alice"\n',
        "xml":      "<root><item id='1'>value</item></root>",
        "ini":      "[section]\nkey = value\n",
        "env":      "DATABASE_URL=postgres://localhost\nDEBUG=true\n",
        "txt":      "Plain text content, written as-is.",
    }
    return examples.get(file_type.lower(), f"Unknown type '{file_type}'.")
