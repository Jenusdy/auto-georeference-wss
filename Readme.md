# auto-georeference-wss

Aplikasi untuk auto rename peta WS/WSS menggunakan EasyOCR dan generate file world (.jgw) dari data GeoJSON.

## Fitur

- **rename_maps.py** — Membaca nomor SLS dari gambar peta menggunakan EasyOCR, lalu menyalin/mengganti nama file ke folder output terstruktur.
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

## Instalasi

```bash
pip install easyocr opencv-python-headless pandas openpyxl numpy
```

## Penggunaan

### 1. Rename Peta

```bash
python rename_maps.py --input "input/01_Peta WSS" --output output
```

### 2. Generate JGW

```bash
python generate_jgw.py --output output --geojson "input/02_Peta Digital/Final_SLS_202513674.geojson"
```
