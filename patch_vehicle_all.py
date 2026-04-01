#!/usr/bin/env python3
"""
Kombinirani patch — sve vehicle log promjene:
1. app.py: can_approve_vehicle_log pravo (MINIMAL_PERMS, PERM_LABELS, migration, approve endpoint, edit/new rute)
2. templates/vehicle_log.html: Status kolona, makni Službeno/Privatno km, CSS fix širine
3. templates/vehicle_log_form.html: approve gumb za can_approve umjesto is_admin
"""
import shutil
from pathlib import Path

errors = []

# ════════════════════════════════════════════════════════════
# app.py
# ════════════════════════════════════════════════════════════
APP = Path('app.py')
if not APP.exists():
    print('ERROR: app.py nije pronađen!'); exit(1)

shutil.copy(APP, APP.with_suffix('.py.bak'))
content = APP.read_text(encoding='utf-8')

# 1. MINIMAL_PERMS
old = "    'can_view_reports': 0, 'can_view_vehicle_log': 0,\n    'can_view_pool_vehicles': 0,"
new = "    'can_view_reports': 0, 'can_view_vehicle_log': 0, 'can_approve_vehicle_log': 0,\n    'can_view_pool_vehicles': 0,"
if old in content: content = content.replace(old, new); print('✅ MINIMAL_PERMS')
else: errors.append('MINIMAL_PERMS')

# 2. PERM_LABELS
old = "    'can_view_vehicle_log': 'Službeni automobil — pregled',\n    'can_view_pool_vehicles': 'Evidencija pool automobila',"
new = "    'can_view_vehicle_log': 'Službeni automobil — pregled',\n    'can_approve_vehicle_log': 'Službeni automobil — odobravanje',\n    'can_view_pool_vehicles': 'Evidencija pool automobila',"
if old in content: content = content.replace(old, new); print('✅ PERM_LABELS')
else: errors.append('PERM_LABELS')

# 3. DB migration
old = "    try:\n        c.execute(\"ALTER TABLE profiles ADD COLUMN can_view_pool_vehicles INTEGER DEFAULT 0\")\n    except: pass"
new = "    try:\n        c.execute(\"ALTER TABLE profiles ADD COLUMN can_approve_vehicle_log INTEGER DEFAULT 0\")\n    except: pass\n    try:\n        c.execute(\"ALTER TABLE profiles ADD COLUMN can_view_pool_vehicles INTEGER DEFAULT 0\")\n    except: pass"
if old in content: content = content.replace(old, new); print('✅ DB migration')
else: errors.append('DB migration')

# 4. approve endpoint — provjera prava
old = """    if not user_can_edit_vehicle_log(user, conn, log_id):
        conn.close()
        return jsonify({'error': 'Nemate pravo odobravanja evidencije'}), 403
    director = conn.execute("SELECT * FROM employees WHERE is_direktor=1 LIMIT 1").fetchone()"""
new = """    if not (user and (user.get('is_admin') or user.get('can_approve_vehicle_log'))):
        conn.close()
        return jsonify({'error': 'Nemate pravo odobravanja evidencije'}), 403
    director = conn.execute("SELECT * FROM employees WHERE is_direktor=1 LIMIT 1").fetchone()"""
if old in content: content = content.replace(old, new); print('✅ approve endpoint')
else: errors.append('approve endpoint')

# 5. vehicle_log_edit — can_approve u template
old = """    return render_template('vehicle_log_form.html',
                          vehicles=vehicles,
                          log=log_dict, preview=None, pn_list=pn_list,
                          month_names=MONTH_NAMES, active='vehicle-log',
                          now_month=datetime.now().month,
                          director_sig=dir_sig,
                          can_edit=can_edit)"""
new = """    can_approve = bool(user and (user.get('is_admin') or user.get('can_approve_vehicle_log')))
    return render_template('vehicle_log_form.html',
                          vehicles=vehicles,
                          log=log_dict, preview=None, pn_list=pn_list,
                          month_names=MONTH_NAMES, active='vehicle-log',
                          now_month=datetime.now().month,
                          director_sig=dir_sig,
                          can_edit=can_edit,
                          can_approve=can_approve)"""
if old in content: content = content.replace(old, new); print('✅ edit render + can_approve')
else: errors.append('edit render')

# 6. vehicle_log_new — prev_end_km iz najnovije ODOBRENE evidencije
old = """    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year = now.year if now.month > 1 else now.year - 1
    prev_log = conn.execute(
        "SELECT end_km FROM vehicle_log WHERE year=? AND month=? ORDER BY id DESC LIMIT 1",
        (prev_year, prev_month)
    ).fetchone()
    prev_end_km = prev_log['end_km'] if prev_log and prev_log['end_km'] else None"""
new = """    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year = now.year if now.month > 1 else now.year - 1
    # Uzmi završnu km iz najnovije ODOBRENE evidencije za to vozilo
    default_vehicle = get_default_vehicle_for_user(conn, user)
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
if old in content: content = content.replace(old, new); print('✅ prev_end_km iz odobrene evidencije')
else: errors.append('prev_end_km')

APP.write_text(content, encoding='utf-8')

# ════════════════════════════════════════════════════════════
# templates/vehicle_log.html
# ════════════════════════════════════════════════════════════
TLIST = Path('templates/vehicle_log.html')
if not TLIST.exists():
    errors.append('vehicle_log.html ne postoji'); 
else:
    shutil.copy(TLIST, TLIST.with_suffix('.html.bak'))
    lc = TLIST.read_text(encoding='utf-8')

    # thead — makni Službeno/Privatno km, dodaj Status
    old = """          <th class="sortable" onclick="sortLog(4)">Ukupno km <span class="sort-icon">↕</span></th>
          <th class="sortable" onclick="sortLog(5)">Službeno km <span class="sort-icon">↕</span></th>
          <th class="sortable" onclick="sortLog(6)">Privatno km <span class="sort-icon">↕</span></th>
          <th>PN nalozi</th>
          <th>Akcije</th>"""
    new = """          <th class="sortable" onclick="sortLog(4)">Ukupno km <span class="sort-icon">↕</span></th>
          <th style="width:110px;">Status</th>
          <th>PN nalozi</th>
          <th style="width:80px;">Akcije</th>"""
    if old in lc: lc = lc.replace(old, new); print('✅ thead vehicle_log.html')
    else: errors.append('thead vehicle_log.html')

    # tbody — makni official/private km td, dodaj Status td
    old = """          <td data-val="{{ log.total_km or 0 }}" style="font-weight:700;">{{ '%.2f'|format(log.total_km or 0) }} km</td>
          <td data-val="{{ log.official_km or 0 }}" style="color:#27ae60;">{{ '%.2f'|format(log.official_km or 0) }} km</td>
          <td data-val="{{ log.private_km or 0 }}" style="color:#e67e22;">{{ '%.2f'|format(log.private_km or 0) }} km</td>
          <td>
            <span class="pn-badges" data-log-id="{{ log.id }}" style="font-size:11px;color:var(--gray-400);">učitavam...</span>
          </td>"""
    new = """          <td data-val="{{ log.total_km or 0 }}" style="font-weight:700;">{{ '%.2f'|format(log.total_km or 0) }} km</td>
          <td style="white-space:nowrap;">
            {% if log.is_approved %}
              <span style="background:#e8f8f5;color:#27ae60;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;white-space:nowrap;">✅ Odobreno</span>
            {% else %}
              <span style="background:#fef9e7;color:#e67e22;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;white-space:nowrap;">📝 Nacrt</span>
            {% endif %}
          </td>
          <td>
            <span class="pn-badges" data-log-id="{{ log.id }}" style="font-size:11px;color:var(--gray-400);">učitavam...</span>
          </td>"""
    if old in lc: lc = lc.replace(old, new); print('✅ tbody vehicle_log.html')
    else: errors.append('tbody vehicle_log.html')

    # colspan prazno stanje
    if 'colspan="9"' in lc:
        lc = lc.replace('colspan="9"', 'colspan="7"')
        print('✅ colspan ažuriran')

    TLIST.write_text(lc, encoding='utf-8')

# ════════════════════════════════════════════════════════════
# templates/vehicle_log_form.html
# ════════════════════════════════════════════════════════════
TFORM = Path('templates/vehicle_log_form.html')
if not TFORM.exists():
    errors.append('vehicle_log_form.html ne postoji')
else:
    shutil.copy(TFORM, TFORM.with_suffix('.html.bak'))
    fc = TFORM.read_text(encoding='utf-8')

    old = "{% if can_edit and current_user.get('is_admin') %}"
    new = "{% if can_approve %}"
    if old in fc: fc = fc.replace(old, new); print('✅ approve gumb vehicle_log_form.html')
    else: errors.append('approve gumb vehicle_log_form.html')

    TFORM.write_text(fc, encoding='utf-8')

# ════════════════════════════════════════════════════════════
print()
if errors:
    print('⚠️  NISU primijenjeni:')
    for e in errors: print(f'   ❌ {e}')
else:
    print('✅ Svi patchi uspješno primijenjeni!')
    print('\nRestartaj Flask i testiraj:')
    print('  1. Postavke → Profili → Voditelj → Službeni automobil — odobravanje (checkbox)')
    print('  2. Nova evidencija → Početna km treba biti 57564 (kraj ožujka)')
