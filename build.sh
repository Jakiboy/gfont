#!/bin/bash
pip install pyinstaller
python -m PyInstaller --onefile --hidden-import=requests --hidden-import=fonttools --hidden-import=brotli download.py