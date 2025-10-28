"""数据转换模块，实现 JSON 与常见格式互转。"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    import tomllib as tomli
except ModuleNotFoundError:  # Python<3.11 兼容
    import tomli
try:
    import tomli_w
except ModuleNotFoundError:  # 兼容缺少 tomli-w 的运行环境
    tomli_w = None
try:
    import yaml
except ModuleNotFoundError:  # 允许无 PyYAML 环境运行基础功能
    yaml = None


def json_to_yaml(data: Any) -> str:
    """将 JSON 数据转换为 YAML。"""
    if yaml is None:
        raise RuntimeError("当前环境缺少 PyYAML，无法导出 YAML")
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def yaml_to_json(text: str) -> Any:
    """将 YAML 文本转换为 JSON 数据。"""
    if yaml is None:
        raise RuntimeError("当前环境缺少 PyYAML，无法导入 YAML")
    return yaml.safe_load(text)


def json_to_toml(data: Any) -> str:
    """JSON 转 TOML。"""
    if tomli_w is not None:
        return tomli_w.dumps(data)
    # 简单回退，仅支持字典的字符串写出
    if not isinstance(data, dict):
        raise ValueError("缺少 tomli-w 时仅支持字典转换")
    lines = []
    for key, value in data.items():
        if isinstance(value, str):
            lines.append(f"{key} = \"{value}\"")
        elif isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        else:
            lines.append(f"{key} = {value}")
    return "\n".join(lines) + "\n"


def toml_to_json(text: str) -> Any:
    """TOML 转 JSON。"""
    return tomli.loads(text)


def json_to_csv(data: Any) -> str:
    """将 JSON 数组转换为 CSV。"""
    if not isinstance(data, list):
        raise ValueError("仅支持数组转换为 CSV")
    output = io.StringIO()
    if data:
        fieldnames = sorted({key for item in data if isinstance(item, dict) for key in item.keys()})
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            if isinstance(row, dict):
                writer.writerow(row)
    return output.getvalue()


def csv_to_json(text: str) -> Any:
    """CSV 文本转换为 JSON 数组。"""
    output = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        output.append({k: v for k, v in row.items()})
    return output


def flatten_json(data: Any, parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """扁平化嵌套 JSON。"""
    items: Dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            items.update(flatten_json(value, new_key, sep=sep))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            new_key = f"{parent_key}{sep}{index}" if parent_key else str(index)
            items.update(flatten_json(value, new_key, sep=sep))
    else:
        items[parent_key] = data
    return items


def restore_json(flat_data: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """将扁平化结构还原。"""
    result: Dict[str, Any] = {}
    for key, value in flat_data.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part.isdigit():
                index = int(part)
                while len(current) <= index:
                    current.append({}) if isinstance(current, list) else None
            current = current.setdefault(part, {}) if isinstance(current, dict) else current[int(part)]
        last = parts[-1]
        if isinstance(current, dict):
            current[last] = value
        else:
            index = int(last)
            while len(current) <= index:
                current.append(None)
            current[index] = value
    return result


def decode_jwt(token: str) -> Dict[str, Any]:
    """解码 JWT 令牌。"""
    header, payload, *_ = token.split(".")
    return {
        "header": json.loads(base64.urlsafe_b64decode(header + "==")),
        "payload": json.loads(base64.urlsafe_b64decode(payload + "==")),
    }


def base64_decode(data: str) -> str:
    """Base64 解码。"""
    return base64.b64decode(data).decode("utf-8")


def base64_encode(text: str) -> str:
    """Base64 编码。"""
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def timestamp_to_datetime(value: int) -> str:
    """时间戳转换为 ISO 字符串。"""
    return datetime.fromtimestamp(value).isoformat()


def md5_hash(text: str) -> str:
    """计算 MD5 哈希。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def sha256_hash(text: str) -> str:
    """计算 SHA256 哈希。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
