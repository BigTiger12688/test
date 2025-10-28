"""查询模块，支持 JSONPath 与 JMESPath。"""
from __future__ import annotations

from typing import Any, List

try:
    import jmespath
except ModuleNotFoundError:
    jmespath = None
try:
    from jsonpath_ng.ext import parse as jsonpath_parse
except ModuleNotFoundError:
    jsonpath_parse = None


def query_jsonpath(data: Any, expression: str) -> List[Any]:
    """执行 JSONPath 查询。"""
    if jsonpath_parse is None:
        raise RuntimeError("当前环境缺少 jsonpath-ng，无法执行 JSONPath")
    parser = jsonpath_parse(expression)
    return [match.value for match in parser.find(data)]


def query_jmespath(data: Any, expression: str) -> Any:
    """执行 JMESPath 查询。"""
    if jmespath is None:
        raise RuntimeError("当前环境缺少 jmespath，无法执行 JMESPath")
    return jmespath.search(expression, data)
