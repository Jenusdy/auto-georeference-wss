# WSS Tool — Rename & Georeferensi Otomatis

Aplikasi untuk auto rename peta WSS menggunakan RapidOCR (ONNXRuntime) dan generate file world (.jgw) dari data GeoJSON Poligon SLS.

## Fitur

- **Rename (OCR)** — Deteksi nomor Sub SLS (`idsubsls`) dari gambar peta menggunakan RapidOCR (`rapidocr_onnxruntime`), lalu salin + rename dengan format `[idsubsls]_WSS.[ext]` ke folder output.
- **Georeferensi** — Deteksi 4 titik sudut peta menggunakan contour detection OpenCV (multi-epsilon approximation), hitung parameter transformasi affine dari koordinat GeoJSON, dan generate file world (`.jgw` / `.pgw`).
- **GUI** — Antarmuka PyQt5 interaktif dengan indikator progress dan validasi input.
- **CLI** — Subcommand `rename` dan `georef` untuk penggunaan via terminal / otomatisasi skrip.

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
  geo.py                    -- Georeferensi (deteksi kontur 4 titik, hitung affine, write JGW)
  ocr.py                    -- OCR rename (RapidOCR ONNXRuntime, regex idsubsls, copy file)
  cli.py                    -- CLI entry point (subcommand: rename, georef)
  gui.py                    -- GUI PyQt5
```

## Persyaratan

- Python 3.10+
- Dependencies (lihat `requirements.txt`):
  - `rapidocr-onnxruntime`
  - `opencv-python`
  - `numpy`
  - `pandas`
  - `PyQt5`

## Instalasi

```bash
pip install -r requirements.txt
```

Atau install paket dalam mode editable:

```bash
pip install -e .
```

## Tutorial Video

Berikut adalah video panduan penggunaan aplikasi:

https://github.com/user-attachments/assets/tutorial.mp4

> [!NOTE]
> Jika video di atas tidak dapat diputar langsung di GitHub/Markdown viewer, Anda dapat mengakses berkas video secara lokal di [`docs/tutorial.mp4`](docs/tutorial.mp4).

## Cara Penggunaan (Portable Release .exe)

1. **Download** `wss-tool-v1.0.3-windows-x64.zip` dari halaman Releases.
2. **Extract** file zip tersebut ke folder pilihan Anda.
3. **Run** file `wss-tool-gui.exe`.
4. **Pilih Input & Output**:
   - **Poligon Peta SLS (GeoJSON)**: Pilih file GeoJSON yang berisi data spasial poligon SLS (contoh: `Final_SLS_*.geojson`).
   - **Folder Peta WSS**: Pilih folder yang berisi file gambar peta asli (`.jpg`, `.jpeg`, `.png`).
   - **Folder Lokasi Output**: Pilih folder tempat menyimpan hasil rename peta & file world (`.jgw` / `.pgw`).
5. **Jalankan Proses**: Klik tombol **Running** untuk memulai proses OCR rename dan pembuatan file georeferensi otomatis. Indikator progress akan menampilkan status pengerjaan.

## Penggunaan (Source Code)

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

### Build .exe (Standalone Windows Release)

```bash
python build_exe.py
```

Hasil build berada di `dist/wss-tool/` yang berisi `wss-tool-gui.exe` (GUI) dan `wss-tool.exe` (CLI) serta zip archive `dist/wss-tool-v1.0.3-windows-x64.zip`.

## Catatan

- OCR menggunakan engine lightweight RapidOCR ONNXRuntime yang cepat tanpa perlu PyTorch/CUDA heavy installation.
- Untuk hasil georeferensi yang akurat, pastikan GeoJSON SLS berisi atribut ID SLS yang sesuai dengan teks yang terdeteksi di gambar peta.

