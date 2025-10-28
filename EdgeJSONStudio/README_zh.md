# 锋芒 JSON Studio

锋芒 JSON Studio（EdgeJSON Studio）是一款面向专业数据工程师的现代化 JSON 工具套件，采用 PySide6 与 QML 打造 Fluent 风格界面，支持大文件流式解析、JSONPath/JMESPath 查询、Schema 校验、差异对比与多格式转换。

## 特性概览

- 多文档标签页，支持会话恢复与最近文件
- 语法高亮编辑器、树状浏览、对比视图
- 流式解析 200MB JSON，主线程无阻塞
- JSON5/JSONC 宽松解析，常见错误修复提示
- JSONPath 与 JMESPath 查询构建器
- JSON Schema 校验与常见 Draft 库
- JSON 与 YAML/TOML/CSV 互转，附加工具集
- 插件体系，支持启用/禁用与崩溃隔离
- PyInstaller 与 Nuitka 打包脚本，适配中文 Windows

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
pip install -r requirements.txt
python EdgeJSONStudio/main.py
```

## 打包

- PyInstaller onedir: `pyinstaller EdgeJSONStudio/build/edgejsonstudio_onedir.spec`
- PyInstaller onefile: `pyinstaller EdgeJSONStudio/build/edgejsonstudio_onefile.spec`
- Nuitka: `bash EdgeJSONStudio/build/nuitka_build.sh`

## 文档

- [用户手册](docs/UserGuide_zh.md)
- [开发者指南](docs/DeveloperGuide_zh.md)
- [变更记录](docs/CHANGELOG.md)

## 许可

项目遵循 LGPL 兼容依赖，详见 `LICENSE-THIRD-PARTY.md`，并附示例 `EULA.md` 与 `PRIVACY.md`。
