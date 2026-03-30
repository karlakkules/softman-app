#!/usr/bin/env python3
"""
Patch: invoice_list.html
- Fixa z-index na supplier modalima da se prikazuju iznad upload review forme (z-index:1001)
- suppliers-mgmt-modal   → z-index: 1100
- inv-supplier-edit-modal → z-index: 1100
"""
import shutil, os, sys

TEMPLATE = os.path.join(os.path.dirname(__file__), 'templates', 'invoice_list.html')

if not os.path.exists(TEMPLATE):
    print(f"❌ Nije pronađen: {TEMPLATE}")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE + '.bak')
print("✅ Backup kreiran: invoice_list.html.bak")

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    src = f.read()

# --- Patch 1: suppliers-mgmt-modal - dodaj z-index:1100 ---
OLD1 = '<div class="modal-overlay" id="suppliers-mgmt-modal">'
NEW1 = '<div class="modal-overlay" id="suppliers-mgmt-modal" style="z-index:1100;">'

# --- Patch 2: inv-supplier-edit-modal - dodaj z-index:1100 ---
OLD2 = '<div class="modal-overlay" id="inv-supplier-edit-modal">'
NEW2 = '<div class="modal-overlay" id="inv-supplier-edit-modal" style="z-index:1100;">'

patches = [
    ("suppliers-mgmt-modal z-index",     OLD1, NEW1),
    ("inv-supplier-edit-modal z-index",  OLD2, NEW2),
]

ok = True
for label, old, new in patches:
    if old not in src:
        print(f"⚠️  PATCH PRESKOČEN — pattern nije pronađen: {label}")
        print(f"   Tražim: {repr(old[:80])}")
        ok = False
    else:
        src = src.replace(old, new, 1)
        print(f"✅ Patch primijenjen: {label}")

if ok:
    with open(TEMPLATE, 'w', encoding='utf-8') as f:
        f.write(src)
    print("\n🎉 invoice_list.html uspješno ažuriran!")
    print("   Reload stranice i testiraj gumb ➕ za novog dobavljača unutar forme za učitavanje računa.")
else:
    print("\n❌ Neki patchi nisu primijenjeni.")
    print("   Pokreni dijagnostiku da vidiš stvarni sadržaj fajla:")
    print("   python -c \"open('templates/invoice_list.html').read()\" | grep 'suppliers-mgmt'")
