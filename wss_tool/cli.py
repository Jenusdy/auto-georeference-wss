from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from wss_tool.geo import process_all as process_geo
from wss_tool.ocr import process_all as process_ocr


def _cmd_rename(args: argparse.Namespace) -> None:
    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.exists():
        print(f'Folder input tidak ditemukan: {input_dir}')
        sys.exit(1)

    results: list[list[str]] = []
    count = 0
    for source, result in process_ocr(input_dir, output_dir):
        count += 1
        if result['status'] == 'ok':
            results.append([source.name, result['idsubsls'], 'Berhasil', 'Berhasil melakukan rename file!'])
            print(f'[OK] {source.name} -> {result["idsubsls"]}')
        else:
            results.append([source.name, '', 'Gagal', result.get('reason', '')])
            print(f'[FAIL] {source.name} -> GAGAL')

    df = pd.DataFrame(results, columns=['Nama File', 'Nama Hasil', 'Status', 'Info'])
    output_path = output_dir / 'Hasil.xlsx'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    print(f'\nSelesai. {count} file diproses. Laporan: {output_path}')


def _cmd_georef(args: argparse.Namespace) -> None:
    output_dir = Path(args.output)
    geojson_path = Path(args.geojson)

    if not geojson_path.exists():
        print(f'GeoJSON tidak ditemukan: {geojson_path}')
        sys.exit(1)

    print('Memuat GeoJSON...', file=sys.stderr)
    ok = 0
    fail = 0
    fallback = 0
    count = 0

    for img_file, result in process_geo(output_dir, geojson_path):
        count += 1
        if result['status'] == 'ok':
            print(f'[OK] {img_file.name} -> {result["a"]:.6f} {result["e"]:.6f} | {result["nmdesa"]}, {result["nmkec"]}')
            ok += 1
        elif result['status'] == 'ok_fallback':
            fallback += 1
            print(f'[OK] {img_file.name} -> (sederhana, tanpa deteksi) | {result["nmdesa"]}, {result["nmkec"]}')
            ok += 1
        else:
            print(f'[FAIL] {img_file.name} -> {result.get("reason", "")}')
            fail += 1

    print(f'\nSelesai. {ok} JGW berhasil ({fallback} fallback sederhana), {fail} gagal.')


def main() -> None:
    parser = argparse.ArgumentParser(description='WSS Tool — Rename dan georeferencing peta WSS')
    sub = parser.add_subparsers(dest='command', required=True)

    rename_p = sub.add_parser('rename', help='Rename file menggunakan OCR')
    rename_p.add_argument('--input', '-i', default='input', help='Folder input gambar')
    rename_p.add_argument('--output', '-o', default='output', help='Folder output hasil rename')
    rename_p.set_defaults(func=_cmd_rename)

    georef_p = sub.add_parser('georef', help='Generate JGW menggunakan deteksi fitur')
    georef_p.add_argument('--output', '-o', default='output', help='Folder hasil rename')
    georef_p.add_argument(
        '--geojson', '-g',
        default='input/02_Peta Digital/Final_SLS_202513674.geojson',
        help='Path file GeoJSON',
    )
    georef_p.set_defaults(func=_cmd_georef)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
