#!/usr/bin/env python3
"""
fix_sidebar_width.py
Suzi plavi sidebar s 220px na 185px.

Pokreni iz korijena projekta:
    python fix_sidebar_width.py
"""

import shutil
from pathlib import Path

BASE_PATH = Path("templates/base.html")

if not BASE_PATH.exists():
    print(f"❌ Nije pronađeno: {BASE_PATH}")
    exit(1)

shutil.copy2(BASE_PATH, BASE_PATH.with_suffix(".html.bak_sidebar"))
print("✅ Backup kreiran")

content = BASE_PATH.read_text(encoding="utf-8")

OLD = '--sidebar-w: 220px;'
NEW = '--sidebar-w: 185px;'

if OLD in content:
    content = content.replace(OLD, NEW)
    BASE_PATH.write_text(content, encoding="utf-8")
    print("✅ Sidebar sužen: 220px → 185px")
    print("   Refresh stranice — bez restarta app.py")
else:
    print("⚠️  Nije pronađeno '--sidebar-w: 220px;'")
    # Pokaži što je u datoteci
    import re
    m = re.search(r'--sidebar-w:[^;]+;', content)
    if m:
        print(f"   Trenutna vrijednost: {m.group()}")
        val = input("Unesi novu širinu (npr. 185px): ").strip()
        content = content.replace(m.group(), f'--sidebar-w: {val};')
        BASE_PATH.write_text(content, encoding="utf-8")
        print(f"✅ Sidebar sužen na {val}")
