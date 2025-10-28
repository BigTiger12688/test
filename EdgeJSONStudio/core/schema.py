"""JSON Schema 校验模块。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from jsonschema import Draft7Validator
except ModuleNotFoundError:  # 允许缺少 jsonschema 时仍可导入模块
    Draft7Validator = None


class SchemaValidator:
    """封装 JSON Schema 校验流程。"""

    def __init__(self, schema: Dict[str, Any]) -> None:
        self.schema = schema
        if Draft7Validator is None:
            raise RuntimeError("当前环境缺少 jsonschema，无法执行校验")
        self.validator = Draft7Validator(schema)

    def iter_errors(self, data: Any) -> List[Dict[str, Any]]:
        """返回校验错误列表。"""
        errors: List[Dict[str, Any]] = []
        for error in self.validator.iter_errors(data):
            errors.append(
                {
                    "path": "/".join(str(p) for p in error.absolute_path),
                    "message": error.message,
                }
            )
        return errors

    @classmethod
    def from_file(cls, path: Path) -> "SchemaValidator":
        """从本地文件加载 Schema。"""
        with path.open("r", encoding="utf-8") as fh:
            return cls(json.load(fh))
