#!/usr/bin/env python3
"""Ispisuje /invoices route iz app.py"""
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Pronađi invoice_list ili /invoices route
for i, line in enumerate(lines):
    if ("'/invoices'" in line or '"/invoices"' in line) and 'route' in line.lower():
        print(f"Pronađen na liniji {i+1}")
        for j, l in enumerate(lines[i:i+60], i+1):
            print(f"{j:4}: {l}", end='')
        break
