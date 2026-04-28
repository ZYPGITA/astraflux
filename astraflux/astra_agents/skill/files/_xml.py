# -*- coding: utf-8 -*-

import json
import xml.etree.ElementTree as Et


def _element_to_dict(elem: Et.Element) -> dict | str:
    """Convert an XML element to a JSON-compatible dict."""
    result = {}
    # Attributes
    if elem.attrib:
        result["@attr"] = dict(elem.attrib)
    # Children
    children = list(elem)
    if children:
        child_dict = {}
        for child in children:
            tag = child.tag
            sub = _element_to_dict(child)
            if tag in child_dict:
                if not isinstance(child_dict[tag], list):
                    child_dict[tag] = [child_dict[tag]]
                child_dict[tag].append(sub)
            else:
                child_dict[tag] = sub
        result.update(child_dict)
    # Text
    text = (elem.text or "").strip()
    if text and not children:
        return text
    if text:
        result["#text"] = text
    if not result and text:
        return text
    return result


def _dict_to_xml(tag: str, data) -> Et.Element:
    """Convert a JSON-compatible dict/primitive back to an XML element."""
    elem = Et.Element(tag)
    if isinstance(data, str):
        elem.text = data
    elif isinstance(data, dict):
        for key, val in data.items():
            if key == "@attr":
                for ak, av in val.items():
                    elem.set(ak, str(av))
            elif key == "#text":
                elem.text = str(val)
            else:
                elem.append(_dict_to_xml(key, val))
    elif isinstance(data, list):
        for item in data:
            elem.append(_dict_to_xml(tag, item))
    return elem


class Write:
    """Write XML files. Content must be valid XML string."""

    @staticmethod
    def write(content: str, filepath: str, encoding: str = "utf-8") -> str:
        Et.fromstring(content)  # validate first
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
        return f"Successfully wrote XML to '{filepath}'."

    @staticmethod
    def format(content: str, encoding: str = "utf-8") -> bytes:
        Et.fromstring(content)
        return content.encode(encoding)

    @staticmethod
    def from_dict(root_tag: str, data: dict) -> str:
        """Build an XML string from a dict structure."""
        elem = _dict_to_xml(root_tag, data)
        return Et.tostring(elem, encoding="unicode")


class Read:
    """Read XML files. Returns JSON string representing the XML tree."""

    @staticmethod
    def read(filepath: str, encoding: str = "utf-8") -> str:
        tree = Et.parse(filepath)
        root = tree.getroot()
        result = {root.tag: _element_to_dict(root)}
        return json.dumps(result, ensure_ascii=False, indent=2)
