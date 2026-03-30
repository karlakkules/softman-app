#!/usr/bin/env python3
"""
fix_save_draft_bug.py
Ispravlja bug gdje gumb 'Spremi nacrt' ne radi jer
document.getElementById('cost_center_id') vraća null
(HTML element ne postoji u formi).

Pokreni iz korijena projekta:
    python fix_save_draft_bug.py
"""

import shutil
from pathlib import Path

TEMPLATE_PATH = Path("templates/form.html")

if not TEMPLATE_PATH.exists():
    print(f"❌ Datoteka nije pronađena: {TEMPLATE_PATH}")
    exit(1)

# Backup
backup = TEMPLATE_PATH.with_suffix(".html.bak")
shutil.copy2(TEMPLATE_PATH, backup)
print(f"✅ Backup: {backup}")

content = TEMPLATE_PATH.read_text(encoding="utf-8")

# ── FIX 1: Zaštiti JavaScript liniju koja čita cost_center_id ──────────────
OLD_JS = "    cost_center_id: document.getElementById('cost_center_id').value || null,"
NEW_JS = "    cost_center_id: document.getElementById('cost_center_id')?.value || null,"

if OLD_JS in content:
    content = content.replace(OLD_JS, NEW_JS)
    print("✅ Fix 1: JavaScript cost_center_id zaštićen s optional chaining (?.).")
else:
    print("⚠️  Fix 1: Obrazac već ispravljen ili nije pronađen — provjeri ručno.")

# ── FIX 2: Dodaj skriveni input u prazni form-group Centra troškova ────────
OLD_HTML = """      <div class="form-group">
        <label class="form-label" data-hr="Centar troškova" data-en="Cost center">Centar troškova</label>
        
      </div>"""

NEW_HTML = """      <div class="form-group">
        <label class="form-label" data-hr="Centar troškova" data-en="Cost center">Centar troškova</label>
        <input type="hidden" id="cost_center_id" value="">
      </div>"""

if OLD_HTML in content:
    content = content.replace(OLD_HTML, NEW_HTML)
    print("✅ Fix 2: Dodan skriveni input #cost_center_id u sekciju Centar troškova.")
elif 'id="cost_center_id"' in content:
    print("ℹ️  Fix 2: Element cost_center_id već postoji u HTML-u.")
else:
    # Alternativni pattern (whitespace može varirati)
    import re
    pattern = r'(<div class="form-group">\s*<label[^>]*>Centar tro[^<]*</label>\s*\n\s*\n\s*</div>)'
    replacement = '''<div class="form-group">
        <label class="form-label" data-hr="Centar troškova" data-en="Cost center">Centar troškova</label>
        <input type="hidden" id="cost_center_id" value="">
      </div>'''
    new_content, count = re.subn(pattern, replacement, content)
    if count:
        content = new_content
        print(f"✅ Fix 2 (regex): Dodan skriveni input #cost_center_id ({count} zamjena).")
    else:
        print("⚠️  Fix 2: Nije pronađen prazni form-group za Centar troškova.")
        print("    Ručno dodaj u form.html: <input type='hidden' id='cost_center_id' value=''>")

TEMPLATE_PATH.write_text(content, encoding="utf-8")
print(f"\n✅ Gotovo! Datoteka ažurirana: {TEMPLATE_PATH}")
print("\nPokreni aplikaciju i provjeri gumb 'Spremi nacrt'.")
