#!/usr/bin/env python3
"""Ispisuje app.py od linije 6904 do 7020"""
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print("=" * 70)
for i, line in enumerate(lines[6903:7020], 6904):
    print(f"{i:4}: {line}", end='')
print("\n" + "=" * 70)
