import json
import argparse
import math
from pathlib import Path
from glob import glob

import cv2
import numpy as np


def detect_feature_points(image_path):
    """Detect 4 corner points of the map border within the scanned image.
    Ported from pypy.py (geomatis-desktop).
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return None

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([100, 50, 0])
    upper_blue = np.array([130, 255, 200])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    result = img.copy()
    result[mask_blue > 0] = [255, 255, 255]

    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
    container_approx = None

    eps_factors = [0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.07, 0.1]
    for c in sorted_contours:
        peri = cv2.arcLength(c, True)
        for eps in eps_factors:
            approx = cv2.approxPolyDP(c, eps * peri, True)
            if len(approx) == 4:
                container_approx = approx
                break
        if container_approx is not None:
            break

    if container_approx is None:
        return None

    return [p[0] for p in container_approx.tolist()]


def find_diagonal_points(points):
    """Order 4 points into top-left, top-right, bottom-right, bottom-left.
    Ported from util.FindDiagonalPoints (geomatis-desktop).
    """
    s = [p[0] + p[1] for p in points]
    d = [p[0] - p[1] for p in points]
    idx_min_s = min(range(4), key=lambda i: s[i])
    idx_max_s = max(range(4), key=lambda i: s[i])
    idx_min_d = min(range(4), key=lambda i: d[i])
    idx_max_d = max(range(4), key=lambda i: d[i])
    return {
        'top_left': points[idx_min_s],
        'top_right': points[idx_max_d],
        'bottom_left': points[idx_min_d],
        'bottom_right': points[idx_max_s],
    }


def calculate_rotation_angle(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.degrees(math.atan2(dy, dx))
    return angle if angle >= 0 else angle + 360


def get_feature_dimensions(diag, margin):
    w = math.hypot(
        diag['top_left'][0] - diag['top_right'][0],
        diag['top_left'][1] - diag['top_right'][1],
    )
    h = math.hypot(
        diag['top_left'][0] - diag['bottom_left'][0],
        diag['top_left'][1] - diag['bottom_left'][1],
    )
    return w / (1 + margin), h / (1 + margin)


def lw(a, b):
    return (a, b) if a >= b else (b, a)


def calculate_parameters(img_w, img_h, feature_points, extent, margin=0.05, rotation=0):
    """Calculate affine world file parameters (A, D, B, E, C, F).
    Ported from util.CalculateGeoreferenceParameters (geomatis-desktop).
    """
    delta_x = extent['xmax'] - extent['xmin']
    delta_y = extent['ymax'] - extent['ymin']

    diag = find_diagonal_points(feature_points)
    feat_w, feat_h = get_feature_dimensions(diag, margin)

    angle = calculate_rotation_angle(diag['top_left'], diag['top_right'])

    if delta_x > delta_y and img_w < img_h:
        angle += 90
    if delta_x < delta_y and img_w > img_h:
        angle -= 90
    if img_w < img_h and rotation == 90:
        angle += 180
    elif img_w > img_h and rotation == -90:
        angle += 180
    if rotation == 180:
        angle += 180

    poly_len, poly_wid = lw(delta_x, delta_y)
    feat_len, feat_wid = lw(feat_w, feat_h)

    if (poly_len / poly_wid) >= (feat_len / feat_wid):
        scale = poly_len / feat_len
    else:
        scale = poly_wid / feat_wid

    rad = math.radians(angle)

    cx_img = sum(p[0] for p in feature_points) / 4
    cy_img = sum(p[1] for p in feature_points) / 4
    cx_geo = (extent['xmin'] + extent['xmax']) / 2
    cy_geo = (extent['ymin'] + extent['ymax']) / 2

    a = scale * math.cos(rad)
    d = scale * math.sin(rad)
    b = scale * math.sin(rad)
    e = -scale * math.cos(rad)
    c = cx_geo - a * cx_img - b * cy_img
    f = cy_geo - d * cx_img - e * cy_img

    return a, d, b, e, c, f


def write_jgw(image_path, a, d, b, e, c, f):
    jgw_path = image_path.with_suffix(
        '.pgw' if image_path.suffix.lower() in ('.png',) else '.jgw'
    )
    with open(jgw_path, 'w') as fh:
        fh.write(f'{a:.15f}\n{d:.15f}\n{b:.15f}\n{e:.15f}\n{c:.15f}\n{f:.15f}\n')
    return True


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
    fallback = 0

    for img_path in sorted(image_files):
        img_file = Path(img_path)
        idsubsls = img_file.stem.replace('_WSS', '')
        entry = index.get(idsubsls)
        if entry is None:
            print(f'[FAIL] {img_file.name} -> {idsubsls} tidak ada di GeoJSON')
            fail += 1
            continue

        points = detect_feature_points(img_file)
        if points is not None:
            img = cv2.imread(str(img_file))
            h, w = img.shape[:2]
            params = calculate_parameters(w, h, points, entry)
            if write_jgw(img_file, *params):
                print(f'[OK] {img_file.name} -> {params[0]:.6f} {params[3]:.6f} | {entry["nmdesa"]}, {entry["nmkec"]}')
                ok += 1
            else:
                print(f'[FAIL] {img_file.name} -> GAGAL (baca gambar)')
                fail += 1
        else:
            img = cv2.imread(str(img_file))
            if img is None:
                print(f'[FAIL] {img_file.name} -> GAGAL (baca gambar)')
                fail += 1
                continue
            h, w = img.shape[:2]
            x_res = (entry['xmax'] - entry['xmin']) / w
            y_res = -(entry['ymax'] - entry['ymin']) / h
            if write_jgw(img_file, x_res, 0.0, 0.0, y_res, entry['xmin'], entry['ymax']):
                fallback += 1
                print(f'[OK] {img_file.name} -> (sederhana, tanpa deteksi) | {entry["nmdesa"]}, {entry["nmkec"]}')
                ok += 1
            else:
                print(f'[FAIL] {img_file.name} -> GAGAL (baca gambar)')
                fail += 1

    print(f'\nSelesai. {ok} JGW berhasil ({fallback} fallback sederhana), {fail} gagal.')


if __name__ == '__main__':
    main()
