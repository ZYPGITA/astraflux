# -*- coding: utf-8 -*-

from pathlib import Path
from agents import function_tool

from astraflux.astra_agents.skill.files._txt import Read as TxtRead
from astraflux.astra_agents.skill.files._json import Read as JsonRead
from astraflux.astra_agents.skill.files._csv import Read as CsvRead
from astraflux.astra_agents.skill.files._yaml import Read as YamlRead
from astraflux.astra_agents.skill.files._toml import Read as TomlRead
from astraflux.astra_agents.skill.files._ini import Read as IniRead
from astraflux.astra_agents.skill.files._env import Read as EnvRead
from astraflux.astra_agents.skill.files._excel import Read as ExcelRead


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


_READERS = {
    'txt': TxtRead,
    'json': JsonRead,
    'csv': CsvRead,
    'xml': None,  # handled inline for XML→JSON transform
    'yaml': YamlRead,
    'toml': TomlRead,
    'ini': IniRead,
    'env': EnvRead,
    'excel': ExcelRead,
}


@function_tool
def read_file(filepath: str, encoding: str = "utf-8", file_type: str = None) -> str:
    """
    Unified entry point for reading files in various formats.

    Automatically detects the target format from the file extension or
    an explicit file_type argument, parses the content, and returns a
    JSON string representation.

    Supported formats:
      - txt / log / md / rst  — plain text (returns content as-is)
      - json                  — JSON
      - csv / tsv             — CSV (returns JSON array of objects)
      - xml                   — XML (returns JSON tree representation)
      - yaml / yml            — YAML
      - toml                  — TOML
      - ini / cfg / conf      — INI-style config
      - env                   — key=value environment file
      - xlsx / xls            — Excel (requires openpyxl)

    Args:
        filepath (str):  Path to the file to read.
        encoding (str):  Character encoding. Default is 'utf-8'.
        file_type (str, optional): Explicit format override. If omitted,
                        the format is inferred from the file extension.

    Returns:
        str: File content. For structured formats this is a JSON string;
             for plain text it is the raw text.
             On error, returns a descriptive error message.
    """
    if not file_type:
        file_type = _infer_file_type(filepath)
    else:
        file_type = file_type.lower()

    try:
        reader_class = _READERS.get(file_type)
        if reader_class is None and file_type == 'xml':
            # XML handled separately — return JSON tree
            from astraflux.astra_agents.skill.files._xml import Read as XmlRead
            reader_class = XmlRead
        if reader_class is None:
            supported = ', '.join(f"'{k}'" for k in _READERS)
            return f"Unsupported file type '{file_type}'. Supported: {supported}."

        return reader_class.read(filepath, encoding)

    except FileNotFoundError:
        return f"File not found: '{filepath}'."
    except PermissionError:
        return f"Permission denied: Cannot read '{filepath}'."
    except UnicodeDecodeError:
        return f"Unable to decode '{filepath}' with encoding '{encoding}'. Try a different encoding."
    except ImportError as e:
        pkg = str(e).rsplit(' ', 1)[-1].strip("'")
        return f"Missing dependency: {str(e)}. Install with: pip install {pkg}"
    except Exception as e:
        return f"Failed to read file: {str(e)}"
