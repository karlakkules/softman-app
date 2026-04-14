#!/usr/bin/env python3
"""Patch: app.py — dodaje podprojekte (subprojects) u modul Projekti."""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
shutil.copy2(APP, os.path.join(BACKUP_DIR, 'app.py.bak_subprojects'))
print('✅ Backup napravljen')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Migracija: tablica subprojects + stupac subproject_id u project_time_entries ──
MIG_ANCHOR = "# Migration: projekti"
MIG_NEW = (
    "# Migration: podprojekti\n"
    "    c.executescript('''\n"
    "        CREATE TABLE IF NOT EXISTS subprojects (\n"
    "            id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    "            project_id INTEGER NOT NULL,\n"
    "            name TEXT NOT NULL,\n"
    "            created_at TEXT,\n"
    "            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE\n"
    "        );\n"
    "    ''')\n"
    "    try:\n"
    "        c.execute('ALTER TABLE project_time_entries ADD COLUMN subproject_id INTEGER')\n"
    "    except: pass\n\n"
    "    # Migration: projekti"
)

if "CREATE TABLE IF NOT EXISTS subprojects" not in content and MIG_ANCHOR in content:
    content = content.replace(MIG_ANCHOR, MIG_NEW, 1)
    changes += 1
    print('✅ Migracija subprojects dodana')
else:
    print('⚠️  Migracija subprojects već postoji ili anchor nije pronađen')

# ── 2. Nadogradi api_project_time_save da prima subproject_id ─────────────────
OLD_SAVE = (
    "    conn.execute(\"DELETE FROM project_time_entries WHERE employee_id=? AND date=?\", (employee_id, date_str))\n"
    "    total = 0\n"
    "    for e in entries:\n"
    "        hours = float(e.get('hours') or 0)\n"
    "        if hours <= 0: continue\n"
    "        conn.execute(\"INSERT INTO project_time_entries (project_id, employee_id, date, hours, notes, created_at) VALUES (?,?,?,?,?,?)\",\n"
    "                     (int(e['project_id']), int(employee_id), date_str, hours, e.get('notes') or '', now))\n"
    "        total += hours"
)
NEW_SAVE = (
    "    conn.execute(\"DELETE FROM project_time_entries WHERE employee_id=? AND date=?\", (employee_id, date_str))\n"
    "    total = 0\n"
    "    for e in entries:\n"
    "        hours = float(e.get('hours') or 0)\n"
    "        if hours <= 0: continue\n"
    "        sub_id = e.get('subproject_id') or None\n"
    "        conn.execute(\"INSERT INTO project_time_entries (project_id, subproject_id, employee_id, date, hours, notes, created_at) VALUES (?,?,?,?,?,?,?)\",\n"
    "                     (int(e['project_id']), sub_id, int(employee_id), date_str, hours, e.get('notes') or '', now))\n"
    "        total += hours"
)

if OLD_SAVE in content:
    content = content.replace(OLD_SAVE, NEW_SAVE, 1)
    changes += 1
    print('✅ api_project_time_save nadograđen za subproject_id')
else:
    print('⚠️  api_project_time_save marker nije pronađen')

# ── 3. Nadogradi api_project_time_get da vraća subproject_id ──────────────────
OLD_GET = (
    "    sql = (\"SELECT pte.*, p.name as project_name, p.color FROM project_time_entries pte \"\n"
    "           \"JOIN projects p ON p.id = pte.project_id WHERE pte.employee_id=? AND pte.date=? ORDER BY pte.hours DESC\")\n"
    "    rows = conn.execute(sql, (employee_id, date_str)).fetchall()"
)
NEW_GET = (
    "    sql = (\"SELECT pte.*, p.name as project_name, p.color, s.name as subproject_name \"\n"
    "           \"FROM project_time_entries pte \"\n"
    "           \"JOIN projects p ON p.id = pte.project_id \"\n"
    "           \"LEFT JOIN subprojects s ON s.id = pte.subproject_id \"\n"
    "           \"WHERE pte.employee_id=? AND pte.date=? ORDER BY pte.hours DESC\")\n"
    "    rows = conn.execute(sql, (employee_id, date_str)).fetchall()"
)

if OLD_GET in content:
    content = content.replace(OLD_GET, NEW_GET, 1)
    changes += 1
    print('✅ api_project_time_get nadograđen')
else:
    print('⚠️  api_project_time_get marker nije pronađen')

# ── 4. Nove rute za podprojekte ───────────────────────────────────────────────
SUB_ROUTES = '''
@app.route('/api/projects/<int:project_id>/subprojects', methods=['GET'])
@login_required
def api_subprojects_get(project_id):
    conn = get_db()
    sql = ("SELECT s.*, "
           "COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE subproject_id=s.id),0) as total_hours "
           "FROM subprojects s WHERE s.project_id=? ORDER BY s.name")
    rows = conn.execute(sql, (project_id,)).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))

@app.route('/api/subprojects', methods=['POST'])
@login_required
def api_subproject_save():
    data = request.json
    name = (data.get('name') or '').strip()
    project_id = data.get('project_id')
    sub_id = data.get('id')
    if not name or not project_id:
        return jsonify({'error': 'Naziv i projekt su obavezni'}), 400
    conn = get_db()
    now = datetime.now().isoformat()
    if sub_id:
        conn.execute("UPDATE subprojects SET name=? WHERE id=?", (name, sub_id))
        conn.commit(); conn.close()
        return jsonify({'success': True, 'id': int(sub_id)})
    conn.execute("INSERT INTO subprojects (project_id, name, created_at) VALUES (?,?,?)",
                 (int(project_id), name, now))
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    audit('create', module='projekti', entity='subproject', entity_id=new_id, detail=name)
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/subprojects/<int:sub_id>', methods=['DELETE'])
@login_required
def api_subproject_delete(sub_id):
    conn = get_db()
    conn.execute("DELETE FROM subprojects WHERE id=?", (sub_id,))
    conn.commit(); conn.close()
    audit('delete', module='projekti', entity='subproject', entity_id=sub_id)
    return jsonify({'success': True})

'''

if '/api/subprojects' not in content:
    # Ubaci prije brisanja projekta
    anchor = "@app.route('/api/projects/<int:project_id>', methods=['DELETE'])"
    if anchor in content:
        content = content.replace(anchor, SUB_ROUTES + anchor, 1)
        changes += 1
        print('✅ Rute za subprojects dodane')
    else:
        # Fallback — ubaci pri kraju
        anchor2 = "def api_project_delete"
        if anchor2 in content:
            content = content.replace(anchor2, SUB_ROUTES.strip() + "\n\ndef api_project_delete", 1)
            changes += 1
            print('✅ Rute za subprojects dodane (fallback)')
        else:
            print('⚠️  Anchor za subproject rute nije pronađen')
else:
    print('⚠️  Subproject rute već postoje')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{"✅ Patch gotov" if changes else "❌ Bez promjena"} ({changes} izmjena)')
print('Pokreni: python3 app.py')
