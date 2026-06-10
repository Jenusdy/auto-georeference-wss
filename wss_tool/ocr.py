from __future__ import annotations

import re
import shutil
from pathlib import Path

import cv2

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import warnings
        warnings.filterwarnings('ignore', message='.*pin_memory.*')
        import easyocr
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def detect_id(image_path: str | Path) -> str | None:
    img = cv2.imread(str(image_path))
    if img is None:
        return None

    height, width = img.shape[:2]

    if height > width:
        img = cv2.resize(img, (904, 1280))
        h, w = img.shape[:2]
        crop_h = round(h * 0.04)
        crop_w = round(w * 0.70)
    else:
        img = cv2.resize(img, (1280, 904))
        h, w = img.shape[:2]
        crop_h = round(h * 0.05)
        crop_w = round(w * 0.80)

    cropped = img[0:crop_h, crop_w:w - 1]
    reader = _get_reader()
    results = reader.readtext(cropped, detail=1)
    all_text = ' '.join(r[1] for r in results)
    numbers = ''.join(re.findall(r'\d+', all_text))
    return numbers if numbers else None


def rename_and_copy(source_path: Path, output_dir: Path, idsubsls: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = source_path.suffix
    dest = output_dir / f'{idsubsls}_WSS{suffix}'
    shutil.copy2(source_path, dest)
    return dest


def process_all(input_dir: str | Path, output_dir: str | Path):
    from wss_tool._io import find_images

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image_files = find_images(input_dir)
    if not image_files:
        return

    for img_path in sorted(image_files):
        source = Path(img_path)
        idsubsls = detect_id(str(source))
        if idsubsls:
            rename_and_copy(source, output_path, idsubsls)
            yield source, {'status': 'ok', 'idsubsls': idsubsls}
        else:
            yield source, {'status': 'fail', 'reason': 'Tidak ada nomor ID ditemukan'}
