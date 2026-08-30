import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    base_dir = Path(sys.executable).parent
    internal_dir = base_dir / '_internal'
    
    candidates = [
        internal_dir / 'onnxruntime' / 'capi',
        internal_dir,
        base_dir / 'onnxruntime' / 'capi',
        base_dir,
    ]
    if hasattr(sys, '_MEIPASS'):
        candidates.insert(0, Path(sys._MEIPASS) / 'onnxruntime' / 'capi')
        candidates.insert(1, Path(sys._MEIPASS))

    for p in candidates:
        if p.is_dir():
            p_str = str(p.resolve())
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(p_str)
                except Exception:
                    pass
            os.environ['PATH'] = p_str + os.pathsep + os.environ.get('PATH', '')

    try:
        import onnxruntime  # noqa: F401
    except Exception:
        pass
