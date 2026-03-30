#!/usr/bin/env python3
"""
Dijagnostika: ispisuje /api/pn-expenses POST endpoint iz app.py
Pokreni: python3 diagnose_pn_expenses.py
"""
import os

TARGET = 'app.py'
with open(TARGET, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Pronađi početak pn-expenses POST routea
start_line = None
for i, line in enumerate(lines):
    if 'pn-expenses' in line and ('POST' in line or 'route' in line.lower()):
        start_line = i
        break

if start_line is None:
    # Pokušaj pronaći funkciju
    for i, line in enumerate(lines):
        if 'pn_expenses' in line and 'def ' in line:
            start_line = i
            break

if start_line is None:
    print("❌ Nije pronađen endpoint!")
else:
    print(f"✅ Pronađen na liniji {start_line + 1}")
    print("=" * 70)
    # Ispiši 80 linija od tog mjesta
    for i, line in enumerate(lines[start_line:start_line+80], start_line+1):
        print(f"{i:4}: {line}", end='')
    print("\n" + "=" * 70)
    print("\nPošalji ovaj output Claudeu!")
