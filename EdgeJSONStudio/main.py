"""锋芒 JSON Studio / EdgeJSON Studio 主入口模块。
使用 QQmlApplicationEngine 加载主界面，负责应用初始化、主题、语言和异常捕获。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from app.logging_config import configure_logging
from app.settings import AppSettings
from app.theme import ThemeManager
from app.exceptions import install_global_exception_hook


APP_NAME = "EdgeJSON Studio"
APP_DISPLAY_NAME = "锋芒 JSON Studio"


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数，支持安全模式、语言和便携模式。"""
    parser = argparse.ArgumentParser(description="锋芒 JSON Studio 启动参数")
    parser.add_argument("files", nargs="*", help="启动时打开的 JSON 文件路径")
    parser.add_argument("--safe-mode", action="store_true", help="安全模式启动，禁用所有插件")
    parser.add_argument("--lang", default="auto", help="显式指定界面语言，例如 zh_CN 或 en_US")
    parser.add_argument("--portable", action="store_true", help="便携模式，配置保存在程序目录")
    return parser.parse_args()


def load_translator(app: QGuiApplication, lang: str) -> None:
    """根据命令行指定或系统语言加载翻译文件。"""
    translator = QTranslator(app)
    locale = QLocale.system().name() if lang == "auto" else lang
    translation_file = Path(__file__).resolve().parent / "i18n" / f"{locale}.qm"
    if translation_file.exists() and translator.load(str(translation_file)):
        app.installTranslator(translator)


def main() -> int:
    """应用主入口，初始化 Qt 应用与 QML 引擎。"""
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    args = parse_arguments()
    app = QGuiApplication(sys.argv)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setOrganizationName("EdgeJSON Studio")
    app.setQuitOnLastWindowClosed(False)

    configure_logging()
    install_global_exception_hook()

    settings = AppSettings(portable=args.portable)
    settings.load()

    load_translator(app, args.lang)

    theme_manager = ThemeManager(settings=settings)
    theme_manager.apply_initial_theme()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("AppSettings", settings)
    engine.rootContext().setContextProperty("ThemeManager", theme_manager)
    engine.rootContext().setContextProperty("SafeMode", args.safe_mode)
    engine.rootContext().setContextProperty("InitialFiles", args.files)

    qml_file = Path(__file__).resolve().parent / "qml" / "MainWindow.qml"
    engine.load(str(qml_file))

    if not engine.rootObjects():
        return 1

    # 延迟执行主题同步确保 QML 已初始化
    QTimer.singleShot(100, theme_manager.sync_system_palette)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
