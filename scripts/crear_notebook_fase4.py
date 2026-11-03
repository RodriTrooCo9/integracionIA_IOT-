#!/usr/bin/env python3
"""Generate the measured YOLO26/YOLO11/YOLOv8 comparison (notebook 03)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.crear_notebooks_vision import comparison, write_notebook


def main():
    root = Path(__file__).resolve().parents[1]
    write_notebook(root / 'notebooks/03_comparar_detectores.ipynb', comparison())


if __name__ == '__main__':
    main()
