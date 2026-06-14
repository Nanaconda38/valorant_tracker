# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "static"), "static"),
    (str(ROOT / "data" / "__init__.py"), "data"),
    (str(ROOT / "data" / "predict_trs_generated.py"), "data"),
]

hiddenimports = [
    "data.predict_trs_generated",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "webview",
    "webview.platforms.edgechromium",
]

excludes = [
    "calibrate_nonlinear",
    "calibrate_tracker_score",
    "calibration_store",
    "capture_scoreboards",
    "extract_tracker_scoreboards",
    "asset_sync",
    "rapidocr_onnxruntime",
    "onnxruntime",
    "cv2",
    "numpy",
    "pandas",
    "matplotlib",
    "pytest",
]


a = Analysis(
    ["desktop_main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ValorantTracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ValorantTracker",
)
