# JSON 数据解析工具

一个基于 **PyQt5** 与 **qfluentwidgets** 构建的简单 JSON 数据解析器。界面提供文本输入、文件打开、格式化与树形结构浏览等能力，适合作为熟悉 Fluent 风格桌面界面的入门示例。

## 运行方式

```bash
pip install PyQt5 qfluentwidgets
python json_parser.py
```

启动后即可在左侧输入或粘贴 JSON 文本，点击“解析”查看树形结构，也可以通过“打开文件”按钮读取本地 JSON 文件。