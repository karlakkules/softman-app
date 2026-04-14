#!/usr/bin/env python3
"""Patch: subprojects sort_order + reorder ruta."""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
shutil.copy2(APP, os.path.join(BACKUP_DIR, 'app.py.bak_subproject_order'))
print('✅ Backup napravljen')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Migracija: dodaj sort_order u subprojects
MIG_ANCHOR = "# Migration: project_employees i can_manage_projects"
MIG_NEW = (
    "# Migration: subproject sort_order\n"
    "    try:\n"
    "        c.execute('ALTER TABLE subprojects ADD COLUMN sort_order INTEGER DEFAULT 0')\n"
    "    except: pass\n\n"
    "    # Migration: project_employees i can_manage_projects"
)
if "subproject sort_order" not in content and MIG_ANCHOR in content:
    content = content.replace(MIG_ANCHOR, MIG_NEW, 1)
    changes += 1
    print('✅ Migracija sort_order dodana')
else:
    print('⚠️  sort_order migracija već postoji')

# 2. Uredi api_subprojects_get da sortira po sort_order
OLD_SUB_SQL = (
    "    sql = (\"SELECT s.*, \"\n"
    "           \"COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE subproject_id=s.id),0) as total_hours \"\n"
    "           \"FROM subprojects s WHERE s.project_id=? ORDER BY s.name\")"
)
NEW_SUB_SQL = (
    "    sql = (\"SELECT s.*, \"\n"
    "           \"COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE subproject_id=s.id),0) as total_hours \"\n"
    "           \"FROM subprojects s WHERE s.project_id=? ORDER BY s.sort_order ASC, s.name ASC\")"
)
if OLD_SUB_SQL in content:
    content = content.replace(OLD_SUB_SQL, NEW_SUB_SQL, 1)
    changes += 1
    print('✅ Subproject sort po sort_order')
else:
    print('⚠️  Subproject SQL marker nije pronađen')

# 3. Nova ruta za reorder
REORDER_ROUTE = '''
@app.route('/api/projects/<int:project_id>/subprojects/reorder', methods=['POST'])
@login_required
def api_subproject_reorder(project_id):
    """Spremi novi redoslijed podprojekata."""
    data = request.json
    ids = data.get('ids', [])
    conn = get_db()
    for i, sub_id in enumerate(ids):
        conn.execute("UPDATE subprojects SET sort_order=? WHERE id=? AND project_id=?",
                     (i, sub_id, project_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

'''

if '/subprojects/reorder' not in content:
    anchor = "@app.route('/api/subprojects', methods=['POST'])"
    if anchor in content:
        content = content.replace(anchor, REORDER_ROUTE + anchor, 1)
        changes += 1
        print('✅ Reorder ruta dodana')
    else:
        anchor2 = "def api_subproject_save"
        if anchor2 in content:
            content = content.replace(anchor2, REORDER_ROUTE.strip() + "\n\ndef api_subproject_save", 1)
            changes += 1
            print('✅ Reorder ruta dodana (fallback)')
        else:
            print('⚠️  Anchor za reorder rutu nije pronađen')
else:
    print('⚠️  Reorder ruta već postoji')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{"✅ Patch gotov" if changes else "❌ Bez promjena"} ({changes} izmjena)')
