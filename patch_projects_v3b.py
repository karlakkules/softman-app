#!/usr/bin/env python3
"""
Patch v3b: 
1. Fix duplog projekta — dodaj UNIQUE constraint check u api_project_save
2. Nova ruta /api/projects/my-employee-id za prijavljenog korisnika
3. missing-hours ruta ne treba project_id — popravi URL
"""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
shutil.copy2(APP, os.path.join(BACKUP_DIR, 'app.py.bak_projects_v3b'))
print('✅ Backup napravljen')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Fix duplog projekta — problem je što _get_next_project_id može dati isti ID
#       ako se brzo klikne 2 puta. Dodamo try/except i retry.
OLD_PROJ_INSERT = (
    "    auto_id = _get_next_project_id()\n"
    "    conn.execute(\"INSERT INTO projects (auto_id, name, client_id, color, status, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)\",\n"
    "                 (auto_id, name, client_id, color, status, notes, now, now))\n"
    "    conn.commit()\n"
    "    new_id = conn.execute(\"SELECT last_insert_rowid()\").fetchone()[0]\n"
    "    conn.close()\n"
    "    audit('create', module='projekti', entity='project', entity_id=new_id, detail=name)\n"
    "    return jsonify({'success': True, 'id': new_id, 'auto_id': auto_id})"
)
NEW_PROJ_INSERT = (
    "    # Retry loop za slučaj race condition na auto_id\n"
    "    for _attempt in range(3):\n"
    "        auto_id = _get_next_project_id()\n"
    "        try:\n"
    "            conn.execute(\"INSERT INTO projects (auto_id, name, client_id, color, status, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)\",\n"
    "                         (auto_id, name, client_id, color, status, notes, now, now))\n"
    "            conn.commit()\n"
    "            break\n"
    "        except Exception as _e:\n"
    "            if 'UNIQUE' in str(_e) and _attempt < 2:\n"
    "                continue\n"
    "            conn.close()\n"
    "            return jsonify({'error': f'Greška pri kreiranju projekta: {_e}'}), 500\n"
    "    new_id = conn.execute(\"SELECT last_insert_rowid()\").fetchone()[0]\n"
    "    conn.close()\n"
    "    audit('create', module='projekti', entity='project', entity_id=new_id, detail=name)\n"
    "    return jsonify({'success': True, 'id': new_id, 'auto_id': auto_id})"
)

if OLD_PROJ_INSERT in content:
    content = content.replace(OLD_PROJ_INSERT, NEW_PROJ_INSERT, 1)
    changes += 1
    print('✅ Fix duplog projekta primijenjen')
else:
    print('⚠️  Projekt insert marker nije pronađen')

# ── 2. Nova ruta /api/projects/my-employee-id ─────────────────────────────────
MY_EMP_ROUTE = '''
@app.route('/api/projects/my-employee-id')
@login_required
def api_my_employee_id():
    """Vrati employee_id za prijavljenog korisnika."""
    user = get_current_user()
    disp = (user.get('display_name') or '').strip()
    conn = get_db()
    emp = None
    if disp:
        emp = conn.execute(
            'SELECT id FROM employees WHERE name=? OR name LIKE ?', (disp, f'%{disp}%')
        ).fetchone()
    conn.close()
    return jsonify({'employee_id': emp['id'] if emp else None})

'''

# ── 3. missing-hours — makni project_id iz URL-a (nije potreban) ──────────────
OLD_MISSING = "@app.route('/api/projects/<int:project_id>/missing-hours')"
NEW_MISSING = "@app.route('/api/projects/missing-hours')"

if OLD_MISSING in content:
    content = content.replace(OLD_MISSING, NEW_MISSING, 1)
    # Popravi i funkciju — makni project_id parametar
    content = content.replace(
        "def api_project_missing_hours(project_id):",
        "def api_project_missing_hours():"
    )
    changes += 1
    print('✅ missing-hours URL popravljen (maknuti project_id)')
else:
    print('⚠️  missing-hours ruta nije pronađena ili je već ispravna')

# Ubaci my-employee-id rutu
if '/api/projects/my-employee-id' not in content:
    anchor = "@app.route('/api/projects/missing-hours')"
    if anchor in content:
        content = content.replace(anchor, MY_EMP_ROUTE + anchor, 1)
        changes += 1
        print('✅ /api/projects/my-employee-id ruta dodana')
    else:
        print('⚠️  Anchor za my-employee-id nije pronađen')
else:
    print('⚠️  my-employee-id već postoji')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{"✅ Patch v3b gotov" if changes else "❌ Bez promjena"} ({changes} izmjena)')
