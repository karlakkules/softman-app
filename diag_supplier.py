#!/usr/bin/env python3
"""Dijagnostika: ispiši stvarni sadržaj supplier ruta iz app.py"""
import os, re

APP = os.path.join(os.path.dirname(__file__), 'app.py')

with open(APP, 'r', encoding='utf-8') as f:
    src = f.read()

# Pronađi sve redove koji sadrže 'supplier'
lines = src.splitlines()
print("=== Redovi koji sadrže 'supplier' ===")
for i, line in enumerate(lines, 1):
    if 'supplier' in line.lower():
        print(f"{i:5d}: {line}")

print("\n=== Blok oko /api/suppliers POST/PUT/DELETE ===")
# Ispiši 8 redova oko svake relevantne rute
for i, line in enumerate(lines, 1):
    if '/api/suppliers' in line or 'supplier_create' in line or 'supplier_update' in line or 'supplier_delete' in line:
        start = max(0, i-3)
        end = min(len(lines), i+8)
        print(f"\n--- oko linije {i} ---")
        for j in range(start, end):
            print(f"{j+1:5d}: {repr(lines[j])}")
