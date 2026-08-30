from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _preload_onnxruntime():
    """Pre-load onnxruntime before PyQt5 to avoid DLL initialization conflict on Windows."""
    if hasattr(sys, '_MEIPASS'):
        _ort_capi = Path(sys._MEIPASS) / 'onnxruntime' / 'capi'
        if _ort_capi.is_dir() and hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(str(_ort_capi))
            except Exception:
                pass
    else:
        try:
            import onnxruntime
            _ort_capi = Path(onnxruntime.__file__).parent / 'capi'
            if _ort_capi.is_dir() and hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(str(_ort_capi))
        except Exception:
            pass
    try:
        import onnxruntime  # noqa: F401
    except Exception:
        pass


_preload_onnxruntime()


from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from wss_tool._io import find_images
from wss_tool.geo import process_all as process_geo


class Worker(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_dir: Path, output_dir: Path, geojson_path: Path) -> None:
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.geojson_path = geojson_path

    def run(self) -> None:
        try:
            self.log.emit('=== RENAME (OCR) ===')
            rename_ok = 0
            rename_fail = 0
            rename_total = 0
            try:
                from wss_tool.ocr import process_all as process_ocr
                for source, result in process_ocr(self.input_dir, self.output_dir):
                    rename_total += 1
                    if result['status'] == 'ok':
                        rename_ok += 1
                        self.log.emit(f'[OK] {source.name} -> {result["idsubsls"]}_WSS{source.suffix}')
                    else:
                        rename_fail += 1
                        self.log.emit(f'[FAIL] {source.name} -> {result.get("reason", "")}')
                    self.progress.emit(rename_total, rename_total)
            except OSError:
                rename_fail = 1
                self.log.emit('[SKIP] OCR dilewati karena gagal memuat PyTorch/torch.')
                self.log.emit('       Install Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe')
            self.log.emit(f'Rename: {rename_ok} berhasil, {rename_fail} gagal')
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()
            return

        try:
            self.log.emit('')
            self.log.emit('=== GEOREFERENSI ===')
            ok = 0
            fail = 0
            fallback = 0
            total = 0
            for img_file, result in process_geo(self.output_dir, self.geojson_path):
                total += 1
                if result['status'] == 'ok':
                    ok += 1
                    self.log.emit(
                        f'[OK] {img_file.name} -> {result["a"]:.6f} {result["e"]:.6f} '
                        f'| {result["nmdesa"]}, {result["nmkec"]}'
                    )
                elif result['status'] == 'ok_fallback':
                    fallback += 1
                    ok += 1
                    self.log.emit(
                        f'[OK] {img_file.name} -> (sederhana, tanpa deteksi) '
                        f'| {result["nmdesa"]}, {result["nmkec"]}'
                    )
                else:
                    fail += 1
                    self.log.emit(f'[FAIL] {img_file.name} -> {result.get("reason", "")}')
                self.progress.emit(total, total)

            self.log.emit('')
            self.log.emit(f'Selesai. {ok} JGW berhasil ({fallback} fallback sederhana), {fail} gagal.')
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Rename dan Georeferensi Otomatis')
        self.setMinimumSize(720, 520)
        self._setup_ui()
        self._thread: QThread | None = None
        self._worker: Worker | None = None

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        header = QLabel('Rename dan Georeferensi Otomatis')
        header.setStyleSheet('font-size: 16px; font-weight: bold; padding: 4px 0;')
        layout.addWidget(header)

        row_geo = QHBoxLayout()
        row_geo.addWidget(QLabel('Peta Digital (GeoJSON):'))
        self.geojson_path = QLineEdit()
        self.geojson_path.setPlaceholderText('Pilih file GeoJSON...')
        row_geo.addWidget(self.geojson_path)
        btn_geo = QPushButton('Browse...')
        btn_geo.clicked.connect(lambda: self._browse_file(self.geojson_path, 'GeoJSON (*.geojson *.json);;Semua file (*.*)'))
        row_geo.addWidget(btn_geo)
        layout.addLayout(row_geo)

        row_in = QHBoxLayout()
        row_in.addWidget(QLabel('Folder Input Peta WSS:'))
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText('Pilih folder gambar peta WSS...')
        row_in.addWidget(self.input_path)
        btn_in = QPushButton('Browse...')
        btn_in.clicked.connect(lambda: self._browse_dir(self.input_path))
        row_in.addWidget(btn_in)
        layout.addLayout(row_in)

        row_out = QHBoxLayout()
        row_out.addWidget(QLabel('Folder Output:'))
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText('Pilih folder output...')
        row_out.addWidget(self.output_path)
        btn_out = QPushButton('Browse...')
        btn_out.clicked.connect(lambda: self._browse_dir(self.output_path))
        row_out.addWidget(btn_out)
        layout.addLayout(row_out)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton('Mulai')
        self.btn_start.setMinimumHeight(36)
        self.btn_start.setStyleSheet('font-size: 14px; font-weight: bold;')
        self.btn_start.clicked.connect(self._start)
        btn_layout.addWidget(self.btn_start)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        btn_layout.addWidget(self.progress_bar)
        layout.addLayout(btn_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet('font-family: Consolas, Courier New, monospace; font-size: 12px;')
        layout.addWidget(self.log_output, stretch=1)

        self.statusBar().showMessage('Siap')

    def _browse_file(self, field: QLineEdit, filter_str: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, 'Pilih File', '', filter_str)
        if path:
            field.setText(path)

    def _browse_dir(self, field: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(self, 'Pilih Folder')
        if path:
            field.setText(path)

    def _start(self) -> None:
        geojson = Path(self.geojson_path.text().strip())
        input_dir = Path(self.input_path.text().strip())
        output_dir = Path(self.output_path.text().strip())

        if not self.geojson_path.text().strip():
            QMessageBox.warning(self, 'Error', 'Pilih file GeoJSON terlebih dahulu.')
            return
        if not self.input_path.text().strip():
            QMessageBox.warning(self, 'Error', 'Pilih folder input peta WSS terlebih dahulu.')
            return
        if not self.output_path.text().strip():
            QMessageBox.warning(self, 'Error', 'Pilih folder output terlebih dahulu.')
            return
        if not geojson.exists():
            QMessageBox.warning(self, 'Error', f'File GeoJSON tidak ditemukan:\n{geojson}')
            return

        try:
            with open(geojson) as f:
                raw = json.load(f)
            features = raw.get('features', [])
            has_idsubsls = any(
                feat.get('properties', {}).get('idsubsls')
                for feat in features
            )
            if not has_idsubsls:
                QMessageBox.warning(
                    self, 'Error',
                    f'GeoJSON tidak memiliki fitur dengan kolom "idsubsls".\n'
                    f'Pastikan file GeoJSON valid ({len(features)} fitur ditemukan).'
                )
                return
        except json.JSONDecodeError:
            QMessageBox.warning(self, 'Error', f'File GeoJSON tidak valid (bukan format JSON):\n{geojson}')
            return

        if not input_dir.exists():
            QMessageBox.warning(self, 'Error', f'Folder input tidak ditemukan:\n{input_dir}')
            return

        if not find_images(input_dir):
            QMessageBox.warning(self, 'Error', f'Tidak ditemukan file gambar (jpg/jpeg/png) di folder input:\n{input_dir}')
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        self.btn_start.setEnabled(False)
        self.btn_start.setText('Memproses...')
        self.log_output.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(0)
        self.statusBar().showMessage('Memulai...')

        self._thread = QThread()
        self._worker = Worker(input_dir, output_dir, geojson)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._on_finished)
        self._worker.log.connect(self._on_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.error.connect(self._on_error)

        self._thread.start()

    def _on_log(self, msg: str) -> None:
        self.log_output.append(msg)

    def _on_progress(self, current: int, total: int) -> None:
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f'{current} / {total}')

    def _on_error(self, msg: str) -> None:
        QMessageBox.critical(self, 'Error', msg)

    def _on_finished(self) -> None:
        self.btn_start.setEnabled(True)
        self.btn_start.setText('Mulai')
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.statusBar().showMessage('Selesai')
        self.log_output.append('')


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
