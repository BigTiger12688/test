"""许可证校验接口定义。"""
from __future__ import annotations

from typing import Protocol


class ILicenseProvider(Protocol):
    """定义可选的许可证校验接口。"""

    def validate(self, token: str) -> bool:
        """返回许可证是否合法。"""
        ...


class DummyLicenseProvider:
    """默认实现，总是返回 True，保持离线。"""

    def validate(self, token: str) -> bool:
        return True
