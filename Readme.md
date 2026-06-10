# PetaWSRename-QR

Aplikasi untuk rename peta WS menggunakan OCR (Optical Character Recognition) dan generate file world (.jgw) dari data GeoJSON.

## Fitur

- **rename_maps.py** — Membaca nomor SLS dari gambar peta menggunakan OCR, lalu menyalin/mengganti nama file ke folder output terstruktur.
- **generate_jgw.py** — Membuat file .jgw (world file) dari gambar hasil rename berdasarkan data koordinat di GeoJSON.

## Struktur Folder

```
input/
  01_Peta WSS/          -- Folder gambar peta (JPG)
  02_Peta Digital/      -- Folder data GeoJSON
    Final_SLS_*.geojson
output/                 -- Hasil rename & JGW
```

## Persyaratan

- Python 3.10+
- Tesseract-OCR (https://github.com/tesseract-ocr/tesseract)

## Instalasi

```bash
pip install -r requirements.txt
```

Install Tesseract-OCR dan pastikan path `tesseract.exe` tersedia di system PATH atau di:
- `C:\Program Files\Tesseract-OCR\tesseract.exe`
- `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`

## Penggunaan

### 1. Rename Peta

```bash
python rename_maps.py --input "input/01_Peta WSS" --output output
```

### 2. Generate JGW

```bash
python generate_jgw.py --output output --geojson "input/02_Peta Digital/Final_SLS_202513674.geojson"
```

## Lisensi

Copyright 2023 Jenusdy. Apache License 2.0.
