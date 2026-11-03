#!/usr/bin/env python3
"""Compatibility command: create 00_inicio_y_datasets, not the archived curator."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.crear_notebooks_vision import start, write_notebook


def main():
    root = Path(__file__).resolve().parents[1]
    write_notebook(root / 'notebooks/00_inicio_y_datasets.ipynb', start())


if __name__ == '__main__':
    main()
