import sys
import shutil
from pathlib import Path

sys.setrecursionlimit(5000)

import PyInstaller.depend.bindepend as bindepend
import PyInstaller.building.build_main as build_main

_real_get_imports = bindepend.get_imports
_real_get_imports_pefile = bindepend._get_imports_pefile

def fast_get_imports(filename, search_paths=None):
    fn_str = str(filename).lower()
    if 'windows\\system32' in fn_str or 'windows\\syswow64' in fn_str or 'windows\\winsxs' in fn_str:
        return set()
    try:
        p = Path(filename)
        if p.is_file() and p.stat().st_size > 20 * 1024 * 1024:
            return set()
    except Exception:
        pass
    return _real_get_imports(filename, search_paths)

def fast_get_imports_pefile(filename, search_paths=None, *args, **kwargs):
    fn_str = str(filename).lower()
    if 'windows\\system32' in fn_str or 'windows\\syswow64' in fn_str or 'windows\\winsxs' in fn_str:
        return set()
    try:
        p = Path(filename)
        if p.is_file() and p.stat().st_size > 20 * 1024 * 1024:
            return set()
    except Exception:
        pass
    return _real_get_imports_pefile(filename, search_paths, *args, **kwargs)

bindepend.get_imports = fast_get_imports
bindepend._get_imports_pefile = fast_get_imports_pefile
build_main.bindepend.get_imports = fast_get_imports
build_main.bindepend._get_imports_pefile = fast_get_imports_pefile

import PyInstaller.__main__

ROOT = Path(__file__).parent
DIST_DIR = ROOT / 'dist'
BUILD_DIR = ROOT / 'build'
SPEC_FILE = ROOT / 'wss-tool.spec'

print('Building release package (wss-tool-gui and wss-tool CLI)...')
PyInstaller.__main__.run([
    str(SPEC_FILE),
    '--distpath', str(DIST_DIR),
    '--workpath', str(BUILD_DIR),
    '--clean',
    '--noconfirm',
])
print('PyInstaller build completed successfully.\n')

# Create ZIP archive for distribution
RELEASE_NAME = 'wss-tool-v1.0.3-windows-x64'
ZIP_PATH = DIST_DIR / RELEASE_NAME

print(f'Creating release archive ({RELEASE_NAME}.zip)...')
if (DIST_DIR / 'wss-tool').exists():
    shutil.make_archive(str(ZIP_PATH), 'zip', DIST_DIR / 'wss-tool')

    print('\n================================================--')
    print('RELEASE BUILD SUCCESSFUL!')
    print(f'Release Folder: {DIST_DIR / "wss-tool"}')
    print(f'Release ZIP:    {ZIP_PATH}.zip')
    print('================================================--\n')
else:
    print('Error: Output directory not found!')


