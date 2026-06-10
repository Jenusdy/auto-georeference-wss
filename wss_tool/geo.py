from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import numpy as np

from wss_tool._io import find_images


def detect_feature_points(image_path: str | Path) -> list[list[int, int]] | None:
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

    eps_factors = [0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.07, 0.1]
    for c in sorted_contours:
        peri = cv2.arcLength(c, True)
        for eps in eps_factors:
            approx = cv2.approxPolyDP(c, eps * peri, True)
            if len(approx) == 4:
                return [p[0] for p in approx.tolist()]
    return None


def find_diagonal_points(points: list[list[int, int]]) -> dict[str, list[int, int]]:
    s = [p[0] + p[1] for p in points]
    d = [p[0] - p[1] for p in points]
    return {
        'top_left': points[min(range(4), key=lambda i: s[i])],
        'top_right': points[max(range(4), key=lambda i: d[i])],
        'bottom_left': points[min(range(4), key=lambda i: d[i])],
        'bottom_right': points[max(range(4), key=lambda i: s[i])],
    }


def calculate_rotation_angle(p1: list[int, int], p2: list[int, int]) -> float:
    angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
    return angle if angle >= 0 else angle + 360


def get_feature_dimensions(diag: dict[str, list[int, int]], margin: float) -> tuple[float, float]:
    w = math.hypot(
        diag['top_left'][0] - diag['top_right'][0],
        diag['top_left'][1] - diag['top_right'][1],
    )
    h = math.hypot(
        diag['top_left'][0] - diag['bottom_left'][0],
        diag['top_left'][1] - diag['bottom_left'][1],
    )
    return w / (1 + margin), h / (1 + margin)


def _lw(a: float, b: float) -> tuple[float, float]:
    return (a, b) if a >= b else (b, a)


def calculate_parameters(
    img_w: int,
    img_h: int,
    feature_points: list[list[int, int]],
    extent: dict[str, float],
    margin: float = 0.05,
    rotation: int = 0,
) -> tuple[float, float, float, float, float, float]:
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

    poly_len, poly_wid = _lw(delta_x, delta_y)
    feat_len, feat_wid = _lw(feat_w, feat_h)

    if (poly_len / poly_wid) >= (feat_len / feat_wid):
        scale = poly_len / feat_len
    else:
        scale = poly_wid / feat_wid

    rad = math.radians(angle)

    cx_img = sum(p[0] for p in feature_points) / 4
    cy_img = sum(p[1] for p in feature_points) / 4
    cx_geo = (extent['xmin'] + extent['xmax']) / 2
    cy_geo = (extent['ymin'] + extent['ymax']) / 2

    return (
        scale * math.cos(rad),
        scale * math.sin(rad),
        scale * math.sin(rad),
        -scale * math.cos(rad),
        cx_geo - scale * math.cos(rad) * cx_img - scale * math.sin(rad) * cy_img,
        cy_geo - scale * math.sin(rad) * cx_img + scale * math.cos(rad) * cy_img,
    )


def write_jgw(image_path: Path, a: float, d: float, b: float, e: float, c: float, f: float) -> bool:
    suffix = '.pgw' if image_path.suffix.lower() in ('.png',) else '.jgw'
    jgw_path = image_path.with_suffix(suffix)
    with open(jgw_path, 'w') as fh:
        fh.write(f'{a:.15f}\n{d:.15f}\n{b:.15f}\n{e:.15f}\n{c:.15f}\n{f:.15f}\n')
    return True


def build_index(geojson_path: str | Path) -> dict[str, dict]:
    with open(geojson_path) as f:
        data = json.load(f)

    index: dict[str, dict] = {}
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        idsubsls = props.get('idsubsls')
        if not idsubsls:
            continue

        coords: list[list[float]] = []
        geom = feature['geometry']
        if geom['type'] == 'MultiPolygon':
            for poly in geom['coordinates']:
                for ring in poly:
                    coords.extend(ring)
        elif geom['type'] == 'Polygon':
            for ring in geom['coordinates']:
                coords.extend(ring)

        if not coords:
            continue

        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        index[idsubsls] = {
            'xmin': min(xs),
            'xmax': max(xs),
            'ymin': min(ys),
            'ymax': max(ys),
            'nmdesa': props.get('nmdesa', ''),
            'nmkec': props.get('nmkec', ''),
        }
    return index


def process_one_image(
    img_file: Path,
    entry: dict,
) -> dict:
    points = detect_feature_points(img_file)
    if points is None:
        img = cv2.imread(str(img_file))
        if img is None:
            return {'status': 'fail', 'reason': 'GAGAL (baca gambar)'}
        h, w = img.shape[:2]
        x_res = (entry['xmax'] - entry['xmin']) / w
        y_res = -(entry['ymax'] - entry['ymin']) / h
        write_jgw(img_file, x_res, 0.0, 0.0, y_res, entry['xmin'], entry['ymax'])
        return {'status': 'ok_fallback', 'nmdesa': entry['nmdesa'], 'nmkec': entry['nmkec']}

    img = cv2.imread(str(img_file))
    if img is None:
        return {'status': 'fail', 'reason': 'GAGAL (baca gambar)'}
    h, w = img.shape[:2]
    params = calculate_parameters(w, h, points, entry)
    write_jgw(img_file, *params)
    return {
        'status': 'ok',
        'a': params[0],
        'e': params[3],
        'nmdesa': entry['nmdesa'],
        'nmkec': entry['nmkec'],
    }


def process_all(output_dir: str | Path, geojson_path: str | Path):
    index = build_index(geojson_path)
    if not index:
        return

    image_files = find_images(output_dir)
    if not image_files:
        return

    for img_path in sorted(image_files):
        img_file = Path(img_path)
        idsubsls = img_file.stem.replace('_WSS', '')
        entry = index.get(idsubsls)
        if entry is None:
            yield img_file, {'status': 'fail', 'reason': f'{idsubsls} tidak ada di GeoJSON'}
            continue

        result = process_one_image(img_file, entry)
        yield img_file, result
