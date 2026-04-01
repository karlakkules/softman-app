#!/usr/bin/env python3
"""Provjeri što točno piše u PDF funkciji za početno km"""
from pathlib import Path

APP = Path('app.py')
c = APP.read_text(encoding='utf-8')

# Nađi liniju s daily_data.append u PDF sekciji
lines = c.splitlines()
for i, line in enumerate(lines):
    if 'daily_data.append' in line:
        print(f"\n=== daily_data.append na liniji {i+1} ===")
        for j in range(i-2, i+10):
            print(f"{j+1:5d}: {lines[j]}")
