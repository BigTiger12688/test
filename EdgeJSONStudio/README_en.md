# EdgeJSON Studio

EdgeJSON Studio is a flagship JSON productivity suite built with PySide6 and QML. It delivers a Fluent-inspired user interface, Mica/Acrylic surfaces, and a plugin-capable architecture for parsing, diffing, querying, and transforming large JSON datasets.

## Highlights

- Multi-document workspace with tab restore and recent files
- Code editor, tree view, and diff layout with split panes
- Stream parsing for 200MB JSON while keeping UI responsive
- Strict JSON and permissive JSON5/JSONC parsing modes with auto fixes
- JSONPath and JMESPath query builders with highlighted results
- JSON Schema validation with offline Draft catalogs
- JSON↔YAML/TOML/CSV conversions plus handy data tools
- Plugin framework with enable/disable and crash isolation
- PyInstaller and Nuitka build scripts for Chinese Windows 10/11

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python EdgeJSONStudio/main.py
```

## Packaging

- PyInstaller onedir: `pyinstaller EdgeJSONStudio/build/edgejsonstudio_onedir.spec`
- PyInstaller onefile: `pyinstaller EdgeJSONStudio/build/edgejsonstudio_onefile.spec`
- Nuitka optimized build: `bash EdgeJSONStudio/build/nuitka_build.sh`

## Documentation

- [User Guide](docs/UserGuide_zh.md)
- [Developer Guide](docs/DeveloperGuide_zh.md)
- [Changelog](docs/CHANGELOG.md)

## Compliance

Refer to `LICENSE-THIRD-PARTY.md`, `EULA.md`, and `PRIVACY.md` for licensing and privacy statements. No telemetry is collected by default.
