# 开发者指南

## 架构概览

- `app/`：Python 侧启动逻辑、设置管理、主题与异常捕获。
- `core/`：解析、查询、差异、转换与 Schema 校验等纯逻辑模块。
- `qml/`：Qt Quick UI，包括自定义标题栏、导航、骨架屏组件。
- `plugins/`：插件接口与示例，实现 `IPlugin` 协议。
- `assets/`：图标、字体与插画资源（可按需扩展）。
- `i18n/`：Qt 翻译文件，使用 `pyside6-lupdate`/`pyside6-lrelease` 维护。
- `tests/`：pytest 单元测试样例，覆盖核心逻辑。

## 数据流

1. `main.py` 启动 `QQmlApplicationEngine`，注入 `AppSettings` 与 `ThemeManager` 到 QML 上下文。
2. QML 中通过 `Connections` 与 `Qt.callLater` 调用 Python 暴露的方法，操作线程池任务。
3. 大文件解析通过 `core.parser.submit_parse` 提交到线程池，完成后通过信号返回结果。
4. 差异、查询、转换等操作保持纯函数，便于单元测试与插件复用。

## 插件 API

```python
from plugins import IPlugin

class Plugin(IPlugin):
    @property
    def meta(self):
        return {"name": "示例", "version": "1.0.0"}

    def activate(self):
        # 注册菜单或命令
        pass

    def deactivate(self):
        pass
```

- 插件以 `plugin.json` 声明元信息：

```json
{
  "name": "示例工具",
  "module": "plugins.sample_plugin.plugin",
  "enabled": true
}
```

- 插件若发生异常，`PluginManager` 会记录日志并避免影响主线程。

## 构建流程

1. 安装依赖：`pip install -r requirements.txt`
2. 运行测试：`pytest EdgeJSONStudio/tests`
3. 构建翻译：`pyside6-lrelease EdgeJSONStudio/i18n/zh_CN.ts`
4. 打包：执行相应 PyInstaller/Nuitka 脚本。

## 目录清单

```
EdgeJSONStudio/
  app/
  core/
  qml/
  plugins/
  assets/
  docs/
  build/
  tests/
```

## 代码风格

- Python 使用 `ruff`/`black`（可选）维护格式。
- QML 注释使用中文，遵循驼峰命名。
- 不在主线程执行长耗时操作，统一使用线程池或 QtConcurrent。
