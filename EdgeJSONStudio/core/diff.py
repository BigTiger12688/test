"""JSON 差异对比与合并模块。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class DiffEntry:
    """差异项，记录路径、类型与值。"""

    path: str
    change_type: str
    value_a: Any
    value_b: Any


def diff(a: Any, b: Any, prefix: str = "") -> List[DiffEntry]:
    """递归计算两个 JSON 对象差异。"""
    results: List[DiffEntry] = []
    if isinstance(a, dict) and isinstance(b, dict):
        keys = set(a.keys()) | set(b.keys())
        for key in sorted(keys):
            next_prefix = f"{prefix}.{key}" if prefix else key
            if key not in a:
                results.append(DiffEntry(next_prefix, "add", None, b[key]))
            elif key not in b:
                results.append(DiffEntry(next_prefix, "remove", a[key], None))
            else:
                results.extend(diff(a[key], b[key], next_prefix))
    elif isinstance(a, list) and isinstance(b, list):
        for idx, (item_a, item_b) in enumerate(zip(a, b)):
            results.extend(diff(item_a, item_b, f"{prefix}[{idx}]"))
        if len(a) > len(b):
            for idx in range(len(b), len(a)):
                results.append(DiffEntry(f"{prefix}[{idx}]", "remove", a[idx], None))
        elif len(b) > len(a):
            for idx in range(len(a), len(b)):
                results.append(DiffEntry(f"{prefix}[{idx}]", "add", None, b[idx]))
    else:
        if a != b:
            results.append(DiffEntry(prefix, "change", a, b))
    return results


def three_way_merge(base: Any, a: Any, b: Any) -> Dict[str, Any]:
    """执行三方合并，返回结果与冲突列表。"""
    result = {"merged": a, "conflicts": []}
    diffs_a = diff(base, a)
    diffs_b = diff(base, b)
    conflict_paths = {d.path for d in diffs_a} & {d.path for d in diffs_b}
    result["conflicts"] = sorted(conflict_paths)
    return result
