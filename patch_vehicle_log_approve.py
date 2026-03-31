#!/usr/bin/env python3
"""
Patch: app.py — više promjena za vehicle log:
1. Novo pravo can_approve_vehicle_log u MINIMAL_PERMS, PERM_LABELS, migration, approve endpoint
2. vehicle_log_new — prev_end_km iz najnovije ODOBRENE evidencije (is_approved=1)
3. vehicle_log_edit — prosljeđuje can_approve flag u template
"""

import shutil
from pathlib import Path

APP = Path('app.py')
if not APP.exists():
    print('ERROR: app.py nije pronađen!')
    exit(1)

shutil.copy(APP, APP.with_suffix('.py.bak'))
print('✅ Backup kreiran: app.py.bak')

content = APP.read_text(encoding='utf-8')

errors = []

# ─── Fix 1: MINIMAL_PERMS — dodaj can_approve_vehicle_log ────────────────────
OLD_PERMS = "    'can_view_reports': 0, 'can_view_vehicle_log': 0,\n    'can_view_pool_vehicles': 0,"
NEW_PERMS = "    'can_view_reports': 0, 'can_view_vehicle_log': 0, 'can_approve_vehicle_log': 0,\n    'can_view_pool_vehicles': 0,"

if OLD_PERMS in content:
    content = content.replace(OLD_PERMS, NEW_PERMS)
    print('✅ Fix 1a: can_approve_vehicle_log dodan u MINIMAL_PERMS')
else:
    errors.append('Fix 1a: MINIMAL_PERMS pattern nije pronađen')

# ─── Fix 2: PERM_LABELS — dodaj label ────────────────────────────────────────
OLD_LABELS = "    'can_view_vehicle_log': 'Službeni automobil — pregled',\n    'can_view_pool_vehicles': 'Evidencija pool automobila',"
NEW_LABELS = "    'can_view_vehicle_log': 'Službeni automobil — pregled',\n    'can_approve_vehicle_log': 'Službeni automobil — odobravanje',\n    'can_view_pool_vehicles': 'Evidencija pool automobila',"

if OLD_LABELS in content:
    content = content.replace(OLD_LABELS, NEW_LABELS)
    print('✅ Fix 2: can_approve_vehicle_log dodan u PERM_LABELS')
else:
    errors.append('Fix 2: PERM_LABELS pattern nije pronađen')

# ─── Fix 3: DB migration — ALTER TABLE profiles ───────────────────────────────
OLD_MIGRATION = "    try:\n        c.execute(\"ALTER TABLE profiles ADD COLUMN can_view_pool_vehicles INTEGER DEFAULT 0\")\n    except: pass"
NEW_MIGRATION = "    try:\n        c.execute(\"ALTER TABLE profiles ADD COLUMN can_approve_vehicle_log INTEGER DEFAULT 0\")\n    except: pass\n    try:\n        c.execute(\"ALTER TABLE profiles ADD COLUMN can_view_pool_vehicles INTEGER DEFAULT 0\")\n    except: pass"

if OLD_MIGRATION in content:
    content = content.replace(OLD_MIGRATION, NEW_MIGRATION)
    print('✅ Fix 3: ALTER TABLE migration dodan')
else:
    errors.append('Fix 3: migration pattern nije pronađen')

# ─── Fix 4: approve_vehicle_log endpoint — provjera prava ────────────────────
OLD_APPROVE = """def approve_vehicle_log(log_id):
    \"\"\"Dodaj potpis direktora kao odobrenje.\"\"\"
    conn = get_db()
    user = get_current_user()
    if not user_can_edit_vehicle_log(user, conn, log_id):
        conn.close()
        return jsonify({'error': 'Nemate pravo odobravanja evidencije'}), 403"""

NEW_APPROVE = """def approve_vehicle_log(log_id):
    \"\"\"Dodaj potpis direktora kao odobrenje.\"\"\"
    conn = get_db()
    user = get_current_user()
    if not (user and (user.get('is_admin') or user.get('can_approve_vehicle_log'))):
        conn.close()
        return jsonify({'error': 'Nemate pravo odobravanja evidencije'}), 403"""

if OLD_APPROVE in content:
    content = content.replace(OLD_APPROVE, NEW_APPROVE)
    print('✅ Fix 4: approve endpoint koristi can_approve_vehicle_log')
else:
    errors.append('Fix 4: approve endpoint pattern nije pronađen')

# ─── Fix 5: vehicle_log_edit — prosljeđuje can_approve u template ─────────────
OLD_EDIT_RENDER = """    return render_template('vehicle_log_form.html',
                          vehicles=vehicles,
                          log=log_dict, preview=None, pn_list=pn_list,
                          month_names=MONTH_NAMES, active='vehicle-log',
                          now_month=datetime.now().month,
                          director_sig=dir_sig,
                          can_edit=can_edit)"""

NEW_EDIT_RENDER = """    can_approve = bool(user and (user.get('is_admin') or user.get('can_approve_vehicle_log')))
    return render_template('vehicle_log_form.html',
                          vehicles=vehicles,
                          log=log_dict, preview=None, pn_list=pn_list,
                          month_names=MONTH_NAMES, active='vehicle-log',
                          now_month=datetime.now().month,
                          director_sig=dir_sig,
                          can_edit=can_edit,
                          can_approve=can_approve)"""

if OLD_EDIT_RENDER in content:
    content = content.replace(OLD_EDIT_RENDER, NEW_EDIT_RENDER)
    print('✅ Fix 5: can_approve prosljeđen u vehicle_log_form template')
else:
    errors.append('Fix 5: edit render pattern nije pronađen')

# ─── Fix 6: vehicle_log_new — prev_end_km iz najnovije ODOBRENE evidencije ───
OLD_PREV = """    prev_log = conn.execute(
        "SELECT end_km FROM vehicle_log WHERE year=? AND month=? ORDER BY id DESC LIMIT 1",
        (prev_year, prev_month)
    ).fetchone()
    prev_end_km = prev_log['end_km'] if prev_log and prev_log['end_km'] else None"""

NEW_PREV = """    # Traži završnu km iz najnovije ODOBRENE evidencije za odabrano vozilo
    # Prvo pokušaj odobrenu evidenciju prethodnog mjeseca, pa bilo koji prethodni odobreni
    default_vehicle = get_default_vehicle_for_user(conn, user)
    vehicle_filter = "AND vl.vehicle_id=?" if default_vehicle else ""
    vehicle_params_prev = [prev_year, prev_month] + ([default_vehicle['id']] if default_vehicle else [])
    vehicle_params_any  = ([default_vehicle['id']] if default_vehicle else [])
    prev_log = conn.execute(
        f"SELECT end_km FROM vehicle_log vl WHERE year=? AND month=? AND is_approved=1 {vehicle_filter} ORDER BY id DESC LIMIT 1",
        vehicle_params_prev
    ).fetchone()
    if not prev_log:
        # Fallback: najnovija odobrena evidencija bez obzira na mjesec
        if default_vehicle:
            prev_log = conn.execute(
                "SELECT end_km FROM vehicle_log WHERE is_approved=1 AND vehicle_id=? ORDER BY year DESC, month DESC, id DESC LIMIT 1",
                (default_vehicle['id'],)
            ).fetchone()
        else:
            prev_log = conn.execute(
                "SELECT end_km FROM vehicle_log WHERE is_approved=1 ORDER BY year DESC, month DESC, id DESC LIMIT 1"
            ).fetchone()
    prev_end_km = prev_log['end_km'] if prev_log and prev_log['end_km'] else None"""

if OLD_PREV in content:
    content = content.replace(OLD_PREV, NEW_PREV)
    print('✅ Fix 6: prev_end_km iz najnovije odobrene evidencije')
else:
    errors.append('Fix 6: prev_end_km pattern nije pronađen')

APP.write_text(content, encoding='utf-8')

if errors:
    print('\n⚠️  Sljedeći patchi NISU primijenjeni:')
    for e in errors:
        print(f'   ❌ {e}')
else:
    print('\n✅ Svi patchi uspješno primijenjeni na app.py!')

print('\nSljedeći korak: pokreni patch_vehicle_log_ui.py za template promjene.')
