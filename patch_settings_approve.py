#!/usr/bin/env python3
"""
Patch: templates/settings.html — dodaj can_approve_vehicle_log u 3 JS konstante
       + fix dvostrukog migration unosa u app.py
"""
import shutil
from pathlib import Path

errors = []

# ════════════════════════════════════════════════════════
# 1. settings.html — 3 mjesta
# ════════════════════════════════════════════════════════
TSET = Path('templates/settings.html')
if not TSET.exists():
    print('ERROR: templates/settings.html nije pronađen!'); exit(1)

shutil.copy(TSET, TSET.with_suffix('.html.bak'))
sc = TSET.read_text(encoding='utf-8')

# PERM_LABELS (JS) — linija ~1135
old = "  can_view_vehicle_log: 'Službeni automobil — pregled', can_view_pool_vehicles: 'Evidencija pool automobila',"
new = "  can_view_vehicle_log: 'Službeni automobil — pregled', can_approve_vehicle_log: 'Službeni automobil — odobravanje', can_view_pool_vehicles: 'Evidencija pool automobila',"
if old in sc: sc = sc.replace(old, new); print('✅ PERM_LABELS (JS)')
else: errors.append('PERM_LABELS (JS)')

# PERM_GROUPS — linija ~1196
old = "  { label: 'Službeni automobil', perms: ['can_view_vehicle_log','can_view_pool_vehicles'] },"
new = "  { label: 'Službeni automobil', perms: ['can_view_vehicle_log','can_approve_vehicle_log','can_view_pool_vehicles'] },"
if old in sc: sc = sc.replace(old, new); print('✅ PERM_GROUPS')
else: errors.append('PERM_GROUPS')

# PERM_SHORT — linija ~1205
old = "  can_view_vehicle_log: 'Pregled', can_view_pool_vehicles: 'Evidencija pool auta',"
new = "  can_view_vehicle_log: 'Pregled', can_approve_vehicle_log: 'Odobravanje', can_view_pool_vehicles: 'Evidencija pool auta',"
if old in sc: sc = sc.replace(old, new); print('✅ PERM_SHORT')
else: errors.append('PERM_SHORT')

TSET.write_text(sc, encoding='utf-8')

# ════════════════════════════════════════════════════════
# 2. app.py — ukloni dvostruki migration unos
# ════════════════════════════════════════════════════════
APP = Path('app.py')
if APP.exists():
    shutil.copy(APP, APP.with_suffix('.py.bak'))
    ac = APP.read_text(encoding='utf-8')

    old = """    try:
        c.execute("ALTER TABLE profiles ADD COLUMN can_approve_vehicle_log INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE profiles ADD COLUMN can_approve_vehicle_log INTEGER DEFAULT 0")
    except: pass"""
    new = """    try:
        c.execute("ALTER TABLE profiles ADD COLUMN can_approve_vehicle_log INTEGER DEFAULT 0")
    except: pass"""
    if old in ac: ac = ac.replace(old, new); print('✅ app.py dvostruki migration uklonjen')
    else: print('ℹ️  app.py dvostruki migration — nije pronađen (možda već ok)')

    APP.write_text(ac, encoding='utf-8')

print()
if errors:
    print('⚠️  NISU primijenjeni:')
    for e in errors: print(f'   ❌ {e}')
else:
    print('✅ Svi patchi primijenjeni!')
    print('\nRestartaj Flask, otvori Postavke → Profili → uredi "Voditelj"')
    print('→ pod "Službeni automobil" treba se pojaviti checkbox "Odobravanje"')
