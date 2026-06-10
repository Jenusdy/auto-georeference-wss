from __future__ import annotations

from pathlib import Path
from glob import glob


def find_images(directory: str | Path) -> list[str]:
    patterns = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    seen: set[str] = set()
    files: list[str] = []
    for pattern in patterns:
        for f in glob(str(Path(directory) / '**' / pattern), recursive=True):
            f_lower = f.lower()
            if f_lower not in seen:
                seen.add(f_lower)
                files.append(f)
    return files
