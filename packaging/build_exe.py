"""Bygger dist/AVM70Diagnostics.exe med PyInstaller (FEATURES.md #13).

Køres af build.ps1 i build-venv'et. Læser version.json (eneste versionskilde,
CLAUDE.md regel 1) og skriver den ind i exe'ens Windows-filegenskaber.
"""

import json
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent
PACKAGING = ROOT / "packaging"
BUILD = ROOT / "build"


def version_tuple(version: str, build: str) -> tuple[int, int, int, int]:
    parts = [int(p) for p in version.split(".")[:3]]
    parts += [0] * (3 - len(parts))
    return (*parts, int(build))


def write_version_file(path: Path, version: str, build: str) -> None:
    v = version_tuple(version, build)
    path.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={v}, prodvers={v}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Jan Green Larsen'),
      StringStruct('FileDescription', 'AVM70 Diagnostics'),
      StringStruct('FileVersion', '{version}.{int(build)}'),
      StringStruct('InternalName', 'AVM70Diagnostics'),
      StringStruct('OriginalFilename', 'AVM70Diagnostics.exe'),
      StringStruct('ProductName', 'AVM70 Diagnostics'),
      StringStruct('ProductVersion', '{version} build {build}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""", encoding="utf-8")


def main() -> int:
    info = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    BUILD.mkdir(exist_ok=True)
    version_file = BUILD / "version_info.txt"
    write_version_file(version_file, info["version"], info["build"])
    sep = ";"  # Windows-separator for --add-data
    PyInstaller.__main__.run([
        str(PACKAGING / "launcher.py"),
        "--name", "AVM70Diagnostics",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--paths", str(ROOT / "backend"),
        "--add-data", f"{ROOT / 'frontend'}{sep}frontend",
        "--add-data", f"{ROOT / 'version.json'}{sep}.",
        "--icon", str(PACKAGING / "avm70.ico"),
        "--version-file", str(version_file),
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(BUILD / "pyinstaller"),
        "--specpath", str(BUILD),
        # Moduler der kun importeres dynamisk og derfor ikke ses af analysen.
        "--hidden-import", "app.main",
        "--collect-submodules", "app",
        "--exclude-module", "pytest",
        "--exclude-module", "tkinter",
    ])
    print(f"\nBuilt: {ROOT / 'dist' / 'AVM70Diagnostics.exe'}  (v{info['version']} build {info['build']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
