# PyInstaller build for the FreeFlow desktop app.
#   python packaging/make_icon.py
#   pyinstaller packaging/freeflow.spec --noconfirm
# Produces dist/FreeFlow.app (macOS) or dist/FreeFlow/FreeFlow.exe (Windows).

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

ROOT = Path(SPECPATH).parent
sys.path.insert(0, str(ROOT))
from freeflow import __version__  # noqa: E402

datas, binaries, hiddenimports = [], [], []
for package in ("faster_whisper", "ctranslate2"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h
# pynput and keyring pick their platform backend at runtime. collect_submodules
# skips backends that fail to import on the build machine, so name them too.
hiddenimports += collect_submodules("pynput")
hiddenimports += [
    f"pynput.{kind}._{backend}"
    for kind in ("keyboard", "mouse")
    for backend in ("darwin", "win32", "xorg")
] + ["pynput._util.darwin", "pynput._util.darwin_vks", "pynput._util.win32",
     "pynput._util.win32_vks", "pynput._util.xorg", "pynput._util.xorg_keysyms"]
hiddenimports += collect_submodules("keyring.backends")
datas += copy_metadata("keyring")  # backends are registered as entry points

icons = ROOT / "packaging" / "build"
icon = str(icons / ("icon.icns" if sys.platform == "darwin" else "icon.ico"))

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    runtime_hooks=[str(ROOT / "packaging" / "rthook_av_stub.py")],
    excludes=[
        "av",  # see rthook_av_stub.py
        # Pulled in by optional code paths FreeFlow never uses.
        "PIL", "onnxruntime.transformers", "onnxruntime.quantization", "onnxruntime.tools",
        "huggingface_hub.inference",
        "tkinter", "matplotlib", "IPython", "pytest",
        "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtWebEngineCore", "PySide6.QtPdf",
        "PySide6.Qt3DCore",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FreeFlow",
    console=False,
    icon=icon,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="FreeFlow", upx=False)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="FreeFlow.app",
        icon=icon,
        bundle_identifier="com.freeflow.app",
        version=__version__,
        info_plist={
            "CFBundleDisplayName": "FreeFlow",
            "CFBundleShortVersionString": __version__,
            "CFBundleVersion": __version__,
            "LSUIElement": True,  # menu-bar app: no Dock icon
            "LSMinimumSystemVersion": "12.0",
            "NSHighResolutionCapable": True,
            "NSMicrophoneUsageDescription":
                "FreeFlow listens while you hold the dictation key and turns your voice into text.",
        },
    )
