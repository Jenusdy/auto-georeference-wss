# WSS Tool — Rename & Georeferensi Otomatis

Aplikasi untuk auto rename peta WSS menggunakan EasyOCR dan generate file world (.jgw) dari data GeoJSON.

## Fitur

- **Rename (OCR)** — Deteksi nomor SLS dari gambar peta menggunakan EasyOCR, salin + rename ke folder output.
- **Georeferensi** — Deteksi 4 titik sudut peta, hitung parameter affine, dan generate file .jgw / .pgw.
- **GUI** — Antarmuka PyQt5 untuk menjalankan kedua langkah secara berurutan.
- **CLI** — Subcommand `rename` dan `georef` untuk penggunaan via terminal.

## Struktur Folder

```
input/
  01_Peta WSS/              -- Folder gambar peta asli (JPG/JPEG/PNG)
  02_Peta Digital/          -- Folder data GeoJSON
    Final_SLS_*.geojson
output/                     -- Hasil rename & JGW (dibuat otomatis)
```

```
wss_tool/                   -- Paket utama
  __init__.py
  _io.py                    -- Utilitas pencarian file gambar
  geo.py                    -- Georeferensi (deteksi fitur, hitung parameter, write JGW)
  ocr.py                    -- OCR rename (deteksi ID, copy file)
  cli.py                    -- CLI entry point (subcommand: rename, georef)
  gui.py                    -- GUI PyQt5
```

## Persyaratan

- Python 3.10+
- (Opsional) GPU CUDA untuk EasyOCR — otomatis dipakai jika ada

## Instalasi

```bash
pip install -r requirements.txt
```

Atau install manual:

```bash
pip install opencv-python numpy easyocr pandas PyQt5
```

## Penggunaan

### CLI

```bash
# Rename via OCR
python -m wss_tool.cli rename -i "input/01_Peta WSS" -o output

# Generate JGW
python -m wss_tool.cli georef -o output -g "input/02_Peta Digital/Final_SLS_202513674.geojson"
```

Atau via entry point (jika package di-install):

```bash
wss-tool rename -i input -o output
wss-tool georef -o output -g "input/...geojson"
```

### GUI

```bash
python run_gui.py
```

Atau:

```bash
python -m wss_tool.gui
```

### Build .exe (standalone)

```bash
python build_exe.py
```

Hasil: `dist/wss-tool.exe` (CLI) dan `dist/wss-tool-gui.exe` (GUI).

## Catatan

- OCR membutuhkan PyTorch (+ ~2GB disk). Jika gagal load, GUI akan menampilkan pesan dan tetap menjalankan georeferensi.
- Untuk performa OCR terbaik, gunakan GPU dengan CUDA.
