#!/usr/bin/env python3
"""Dijagnostika: provjeri stanje invoice_list.html"""
import os

PATH = os.path.join('templates', 'invoice_list.html')
with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Veličina: {len(content)} znakova")
print()

# Provjeri edit modal HTML
checks = [
    ('edit-supplier-search (HTML input)', 'id="edit-supplier-search"'),
    ('edit-supplier-dropdown (HTML div)', 'id="edit-supplier-dropdown"'),
    ('edit-supplier-match (HTML badge)', 'id="edit-supplier-match"'),
    ('filterEditSupplierDropdown (JS)', 'function filterEditSupplierDropdown'),
    ('showEditSupplierDropdown (JS)', 'function showEditSupplierDropdown'),
    ('quickAddEditSupplier (JS)', 'function quickAddEditSupplier'),
    ('_origOpenEditModal (JS patch)', '_origOpenEditModal'),
]

for label, marker in checks:
    found = marker in content
    status = '✅' if found else '❌'
    print(f"  {status} {label}")

# Pokaži edit modal dio
idx = content.find('id="edit-modal"')
if idx >= 0:
    # Nađi od <!-- EDIT MODAL --> do modal-footer
    start = max(0, idx - 200)
    end_marker = content.find('</div>\n</div>\n\n', idx)
    if end_marker < 0:
        end_marker = idx + 2000
    snippet = content[start:min(end_marker + 50, len(content))]
    print(f"\n── Edit modal snippet (od pozicije {start}) ──")
    print(snippet[:3000])
