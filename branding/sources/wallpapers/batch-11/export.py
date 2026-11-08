#!/usr/bin/env python3
"""Export approved batch 11 masters through the shared 4K/ultrawide pipeline."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def main():
    specification = importlib.util.spec_from_file_location(
        'batch_export', ROOT / 'branding/sources/wallpapers/batch-09/export.py')
    exporter = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(exporter)
    exporter.main('11')


if __name__ == '__main__':
    main()
