import re
import shutil
import argparse
from pathlib import Path
from glob import glob

import cv2
import pandas as pd
import easyocr

_reader = None


def get_reader():
    global _reader
    if _reader is None:
        print('Memuat EasyOCR (pertama kali butuh download model)...')
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def detect_sls(image_path):
    img = cv2.imread(image_path)
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

    reader = get_reader()
    results = reader.readtext(cropped, detail=1)
    all_text = " ".join([r[1] for r in results])
    numbers = "".join(re.findall(r"\d+", all_text))
    return numbers if numbers else None


def copy_file(source_path, output_dir, idsls):
    dest = Path(output_dir) / idsls[:4] / idsls[4:7] / idsls[7:10]
    dest.mkdir(parents=True, exist_ok=True)
    suffix = Path(source_path).suffix
    shutil.copy2(source_path, dest / f"{idsls}{suffix}")
    return str(dest / f"{idsls}{suffix}")


def main():
    parser = argparse.ArgumentParser(description='Rename peta WS menggunakan OCR')
    parser.add_argument('--input', '-i', default='input', help='Folder input gambar')
    parser.add_argument('--output', '-o', default='output', help='Folder output hasil rename')
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    patterns = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    seen = set()
    image_files = []
    for pattern in patterns:
        for f in glob(str(input_dir / '**' / pattern), recursive=True):
            f_lower = f.lower()
            if f_lower not in seen:
                seen.add(f_lower)
                image_files.append(f)

    if not image_files:
        print(f'Tidak ada gambar ditemukan di folder {input_dir}')
        return

    results = []
    print(f'Ditemukan {len(image_files)} gambar')
    for img_path in sorted(image_files):
        filename = Path(img_path).name
        idsls = detect_sls(img_path)
        if idsls:
            copy_file(img_path, str(output_dir), idsls)
            results.append([filename, idsls, 'Berhasil', 'Berhasil melakukan rename file!'])
            print(f'[OK] {filename} -> {idsls}')
        else:
            results.append([filename, '', 'Gagal', 'Tidak ada nomor SLS ditemukan!'])
            print(f'[FAIL] {filename} -> GAGAL')

    df = pd.DataFrame(results, columns=['Nama File', 'Nama Hasil', 'Status', 'Info'])
    df.to_excel(output_dir / 'Hasil.xlsx', index=False)
    print(f'\nSelesai. {len(results)} file diproses. Laporan: {output_dir / "Hasil.xlsx"}')


if __name__ == '__main__':
    main()
