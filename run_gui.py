import sys

try:
    from wss_tool.gui import main
    main()
except OSError as e:
    if '1114' in str(e) or 'c10.dll' in str(e):
        print('=' * 60)
        print('ERROR: Gagal memuat PyTorch/torch (dependency EasyOCR).')
        print('Solusi: https://aka.ms/vs/17/release/vc_redist.x64.exe')
        print('Atau jalankan hanya georef: python -m wss_tool.cli georef ...')
        print('=' * 60)
    else:
        raise
