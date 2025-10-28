"""插件系统基础设施，定义 IPlugin 接口与加载器。"""
from __future__ import annotations

import importlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


class IPlugin(Protocol):
    """插件协议，要求实现元信息与入口方法。"""

    @property
    def meta(self) -> Dict[str, Any]:
        ...

    def activate(self) -> None:
        ...

    def deactivate(self) -> None:
        ...


@dataclass
class PluginInfo:
    """插件描述信息。"""

    name: str
    module: str
    enabled: bool = True


class PluginManager:
    """管理插件加载、启用与禁用。"""

    def __init__(self, plugins_dir: Path) -> None:
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.registry: Dict[str, IPlugin] = {}

    def discover(self) -> List[PluginInfo]:
        """发现插件目录下的插件。"""
        infos: List[PluginInfo] = []
        for init_file in self.plugins_dir.glob("*/plugin.json"):
            with init_file.open("r", encoding="utf-8") as fh:
                meta = json.load(fh)
            infos.append(PluginInfo(name=meta["name"], module=meta["module"], enabled=meta.get("enabled", True)))
        return infos

    def load(self, info: PluginInfo) -> Optional[IPlugin]:
        """加载插件模块。"""
        if not info.enabled:
            return None
        module = importlib.import_module(info.module)
        plugin: IPlugin = module.Plugin()
        plugin.activate()
        self.registry[info.name] = plugin
        logger.info("插件 %s 已启用", info.name)
        return plugin

    def unload(self, name: str) -> None:
        """卸载插件。"""
        plugin = self.registry.pop(name, None)
        if plugin:
            plugin.deactivate()
            logger.info("插件 %s 已禁用", name)
