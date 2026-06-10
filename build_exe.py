import PyInstaller.__main__
from pathlib import Path

ROOT = Path(__file__).parent

ENTRIES = [
    (str(ROOT / 'run_cli.py'), 'wss-tool', True),
    (str(ROOT / 'run_gui.py'), 'wss-tool-gui', False),
]

for script, name, console in ENTRIES:
    print(f'Building {name}...')
    PyInstaller.__main__.run([
        script,
        '--onefile',
        '--noconsole' if not console else '--console',
        '--name', name,
        '--distpath', str(ROOT / 'dist'),
        '--workpath', str(ROOT / 'build'),
        '--specpath', str(ROOT),
        '--clean',
        '--noconfirm',
    ])
    print(f'{name} selesai.\n')
