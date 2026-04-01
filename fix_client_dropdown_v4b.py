#!/usr/bin/env python3
"""
fix_client_dropdown_v4b.py
Popravlja typo u filterFormClientDropdown u form.html:
  .includes(c)  →  .includes(q)

Pokretanje:
    cd ~/Projects/Softman_app
    python3 fix_client_dropdown_v4b.py
"""
import shutil, os

BASE = os.path.dirname(os.path.abspath(__file__))
FORM = os.path.join(BASE, 'templates', 'form.html')

with open(FORM, encoding='utf-8') as f:
    content = f.read()

OLD = "!q || c.name.toLowerCase().includes(c) ||"
NEW = "!q || c.name.toLowerCase().includes(q) ||"

if OLD not in content:
    print("GREŠKA: Typo nije pronađen — možda je već popravljeno?")
    print(f"Tražim: {OLD}")
else:
    shutil.copy2(FORM, FORM + '.bak_v4b')
    content = content.replace(OLD, NEW, 1)
    with open(FORM, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Typo popravljen: .includes(c) → .includes(q)")
    print("Restartaj Flask i testiraj.")
