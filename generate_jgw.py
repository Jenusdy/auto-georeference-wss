import json
import argparse
from pathlib import Path
from glob import glob

import cv2


def build_index(geojson_path):
    with open(geojson_path) as f:
        data = json.load(f)

    index = {}
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        idsubsls = props.get('idsubsls')
        if not idsubsls:
            continue

        coords = []
        geom = feature['geometry']
        if geom['type'] == 'MultiPolygon':
            for poly in geom['coordinates']:
                for ring in poly:
                    for c in ring:
                        coords.append(c)
        elif geom['type'] == 'Polygon':
            for ring in geom['coordinates']:
                for c in ring:
                    coords.append(c)

        if not coords:
            continue

        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        index[idsubsls] = {
            'xmin': min(xs), 'xmax': max(xs),
            'ymin': min(ys), 'ymax': max(ys),
            'nmdesa': props.get('nmdesa', ''),
            'nmkec': props.get('nmkec', ''),
        }
    return index


def write_jgw(image_path, bounds):
    img = cv2.imread(str(image_path))
    if img is None:
        return False

    height, width = img.shape[:2]
    x_res = (bounds['xmax'] - bounds['xmin']) / width
    y_res = -(bounds['ymax'] - bounds['ymin']) / height

    jgw_path = image_path.with_suffix('.jgw')
    with open(jgw_path, 'w') as f:
        f.write(f'{x_res:.15f}\n0.0\n0.0\n{y_res:.15f}\n{bounds["xmin"]:.15f}\n{bounds["ymax"]:.15f}\n')
    return True


def main():
    parser = argparse.ArgumentParser(description='Generate JGW dari gambar hasil rename dan GeoJSON')
    parser.add_argument('--output', '-o', default='output', help='Folder hasil rename')
    parser.add_argument('--geojson', '-g',
                        default='input/02_Peta Digital/Final_SLS_202513674.geojson',
                        help='Path file GeoJSON')
    args = parser.parse_args()

    output_dir = Path(args.output)
    geojson_path = Path(args.geojson)

    if not geojson_path.exists():
        print(f'GeoJSON tidak ditemukan: {geojson_path}')
        return

    print('Memuat GeoJSON...')
    index = build_index(str(geojson_path))
    if not index:
        print('Tidak ada data dalam GeoJSON')
        return
    print(f'{len(index)} fitur dimuat')

    patterns = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    seen = set()
    image_files = []
    for pattern in patterns:
        for f in glob(str(output_dir / '**' / pattern), recursive=True):
            f_lower = f.lower()
            if f_lower not in seen:
                seen.add(f_lower)
                image_files.append(f)

    if not image_files:
        print(f'Tidak ada gambar di folder {output_dir}')
        return

    print(f'Memproses {len(image_files)} gambar...')
    ok = 0
    fail = 0

    for img_path in sorted(image_files):
        img_file = Path(img_path)
        idsubsls = img_file.stem.replace('_WSS', '')
        entry = index.get(idsubsls)
        if entry is None:
            print(f'[FAIL] {img_file.name} -> {idsubsls} tidak ada di GeoJSON')
            fail += 1
            continue

        if write_jgw(img_file, entry):
            print(f'[OK] {img_file.name} -> {idsubsls}.jgw | {entry["nmdesa"]}, {entry["nmkec"]}')
            ok += 1
        else:
            print(f'[FAIL] {img_file.name} -> GAGAL (baca gambar)')
            fail += 1

    print(f'\nSelesai. {ok} JGW berhasil, {fail} gagal.')


if __name__ == '__main__':
    main()
