#!/usr/bin/env python3
"""
Patch: fix saveOrder() crash zbog nedostajućeg #cost_center_id elementa u form.html
Bug: JavaScript poziva document.getElementById('cost_center_id').value
     ali element ne postoji → TypeError → saveOrder() puca tiho → ništa se ne sprema

Pokreni iz korijenskog direktorija projekta:
    python3 patch_form_cost_center.py
"""

import shutil, os, re

TARGET = os.path.join('templates', 'form.html')
BACKUP = TARGET + '.bak'

if not os.path.exists(TARGET):
    print(f"❌ Nije pronađen: {TARGET}")
    print("   Pokreni skriptu iz korijena projekta (tamo gdje je app.py).")
    exit(1)

shutil.copy2(TARGET, BACKUP)
print(f"✅ Backup: {BACKUP}")

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# ── FIX 1: Dodaj hidden input za cost_center_id u prazno polje ─────────────
# Pronađi prazno "Centar troškova" polje i dodaj hidden input
OLD_COST_CENTER = '''      <div class="form-group">
        <label class="form-label" data-hr="Centar troškova" data-en="Cost center">Centar troškova</label>
        
      </div>'''

NEW_COST_CENTER = '''      <div class="form-group">
        <label class="form-label" data-hr="Centar troškova" data-en="Cost center">Centar troškova</label>
        <input type="hidden" id="cost_center_id" value="{{ order.cost_center_id if order and order.cost_center_id else '' }}">
        <input type="text" class="form-control" value="—" disabled style="background:#f7f9fc;color:var(--gray-400);cursor:not-allowed;" placeholder="Nije konfigurirano">
      </div>'''

if OLD_COST_CENTER in content:
    content = content.replace(OLD_COST_CENTER, NEW_COST_CENTER)
    print("✅ FIX 1: Dodan hidden input #cost_center_id")
else:
    # Fallback: traži samo label i dodaj hidden input
    fallback_old = '        <label class="form-label" data-hr="Centar troškova" data-en="Cost center">Centar troškova</label>\n        \n      </div>'
    fallback_new = '        <label class="form-label" data-hr="Centar troškova" data-en="Cost center">Centar troškova</label>\n        <input type="hidden" id="cost_center_id" value="{{ order.cost_center_id if order and order.cost_center_id else \'\' }}">\n      </div>'
    if fallback_old in content:
        content = content.replace(fallback_old, fallback_new)
        print("✅ FIX 1 (fallback): Dodan hidden input #cost_center_id")
    else:
        print("⚠️  FIX 1: Nije pronađen pattern za Centar troškova — dodaj ručno hidden input #cost_center_id")

# ── FIX 2: Zaštiti saveOrder() od null elementa (defensive programming) ────
OLD_COST_CENTER_JS = "    cost_center_id: document.getElementById('cost_center_id').value || null,"
NEW_COST_CENTER_JS = "    cost_center_id: (document.getElementById('cost_center_id') || {value: null}).value || null,"

if OLD_COST_CENTER_JS in content:
    content = content.replace(OLD_COST_CENTER_JS, NEW_COST_CENTER_JS)
    print("✅ FIX 2: Zaštićen JavaScript od null elementa")
else:
    print("⚠️  FIX 2: JS pattern nije pronađen — provjeri ručno")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 Patch primijenjen!")
print("   Restartaj Flask i probaj 'Spremi nacrt' na PN 2026-13.")
print("\n   Git commit:")
print("   cd ~/Projects/Softman_app && git add templates/form.html && git commit -m 'fix: saveOrder crash zbog nedostajuceg cost_center_id elementa' && git push origin main")
