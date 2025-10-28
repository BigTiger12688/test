"""JSON 解析与流式加载模块。"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Tuple

try:
    import ijson
except ModuleNotFoundError:  # 允许在无 ijson 环境下运行基础功能
    ijson = None
try:
    import json5
except ModuleNotFoundError:  # 宽松解析可选
    json5 = None

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="parser")


def parse_json_stream(path: Path, strict: bool = True) -> Tuple[Any, List[str]]:
    """解析 JSON 文件，返回数据与解析日志。"""
    log: List[str] = []
    try:
        if strict:
            with path.open("r", encoding="utf-8") as fh:
                log.append("使用标准 json 解析器。");
                return json.load(fh), log
        log.append("使用 json5 宽松解析器。")
        if json5 is None:
            log.append("当前环境缺少 json5，已回退到标准解析。")
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh), log
        with path.open("r", encoding="utf-8") as fh:
            return json5.load(fh), log
    except Exception as exc:  # noqa: BLE001
        log.append(f"解析失败: {exc}")
        raise


def stream_tree_nodes(path: Path) -> Iterator[Tuple[str, Any]]:
    """增量读取大 JSON，逐条产出节点路径与值。"""
    with path.open("rb") as fh:
        if ijson is None:
            raise RuntimeError("当前环境缺少 ijson，无法流式遍历")
        parser = ijson.parse(fh)
        stack: List[str] = []
        for prefix, event, value in parser:
            if event == "map_key":
                if stack:
                    stack[-1] = value
            elif event in {"start_map", "start_array"}:
                stack.append("")
            elif event in {"end_map", "end_array"}:
                if stack:
                    stack.pop()
            elif event in {"string", "number", "boolean", "null"}:
                path_str = ".".join(filter(None, stack))
                yield path_str, value


def submit_parse(path: Path, strict: bool = True):
    """提交解析任务到线程池。"""
    return _executor.submit(parse_json_stream, path, strict)


def submit_stream(path: Path):
    """提交流式节点遍历任务到线程池。"""
    return _executor.submit(lambda: list(stream_tree_nodes(path)))
