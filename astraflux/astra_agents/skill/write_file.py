# -*- coding: utf-8 -*-
from agents import function_tool


@function_tool
def write_to_file(content: str, filename: str = "output.txt"):
    """
    将指定内容写入本地文件。

    Args:
        content: 需要写入文件的内容。
        filename: 文件名。
    Returns:
        操作结果的字符串信息。
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"成功将内容写入文件 '{filename}'。"
    except Exception as e:
        return f"写入文件失败：{str(e)}"
