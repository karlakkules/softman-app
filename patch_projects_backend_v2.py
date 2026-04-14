#!/usr/bin/env python3
"""Patch: app.py — novi modul Projekti (v2 - fixed)"""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

bak = os.path.join(BACKUP_DIR, 'app.py.bak_projects_v2')
shutil.copy2(APP, bak)
print(f'✅ Backup: {bak}')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. DB Migracija
MIG_ANCHOR = "# Migration: narudzbenica_path u quotes"
MIG_NEW = (
    "# Migration: projekti\n"
    "    c.executescript('''\n"
    "        CREATE TABLE IF NOT EXISTS projects (\n"
    "            id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    "            auto_id TEXT UNIQUE NOT NULL,\n"
    "            name TEXT NOT NULL,\n"
    "            client_id INTEGER,\n"
    "            status TEXT DEFAULT ''active'',\n"
    "            color TEXT DEFAULT ''#2d5986'',\n"
    "            notes TEXT,\n"
    "            created_at TEXT,\n"
    "            updated_at TEXT\n"
    "        );\n"
    "        CREATE TABLE IF NOT EXISTS project_time_entries (\n"
    "            id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    "            project_id INTEGER NOT NULL,\n"
    "            employee_id INTEGER NOT NULL,\n"
    "            date TEXT NOT NULL,\n"
    "            hours REAL NOT NULL,\n"
    "            notes TEXT,\n"
    "            created_at TEXT,\n"
    "            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,\n"
    "            FOREIGN KEY (employee_id) REFERENCES employees(id)\n"
    "        );\n"
    "    ''')\n\n"
    "    # Migration: narudzbenica_path u quotes"
)

if "CREATE TABLE IF NOT EXISTS projects" not in content and MIG_ANCHOR in content:
    content = content.replace(MIG_ANCHOR, MIG_NEW, 1)
    changes += 1
    print('✅ Migracija projects/project_time_entries dodana')
else:
    print('⚠️  Migracija već postoji ili anchor nije pronađen')

# 2. Dashboard insert
DASH_INSERT = (
    "    # Projekti danas\n"
    "    today_str = datetime.now().strftime('%Y-%m-%d')\n"
    "    user_obj = get_current_user()\n"
    "    _disp = (user_obj.get('display_name') or '').split(' ')[0]\n"
    "    emp_today = conn.execute(\n"
    "        'SELECT id FROM employees WHERE name LIKE ?', ('%' + _disp + '%',)\n"
    "    ).fetchone() if _disp else None\n"
    "    project_hours_today = []\n"
    "    if emp_today:\n"
    "        _sql = ('SELECT p.name, p.color, pte.hours '\n"
    "                'FROM project_time_entries pte '\n"
    "                'JOIN projects p ON p.id = pte.project_id '\n"
    "                'WHERE pte.employee_id=? AND pte.date=? ORDER BY pte.hours DESC')\n"
    "        project_hours_today = rows_to_dicts(conn.execute(_sql, (emp_today['id'], today_str)).fetchall())\n"
    "    projects_active = conn.execute(\n"
    "        'SELECT COUNT(*) as cnt FROM projects WHERE status=?', ('active',)\n"
    "    ).fetchone()['cnt']\n"
    "    project_hours_today_total = round(sum(r['hours'] for r in project_hours_today), 2)\n\n"
)

if 'project_hours_today' not in content:
    idx = content.find("    return render_template('dashboard.html'")
    if idx != -1:
        content = content[:idx] + DASH_INSERT + content[idx:]
        # Dodaj varijable u render_template
        rt_idx = content.find("    return render_template('dashboard.html'")
        depth = 0
        end_idx = rt_idx
        for i, ch in enumerate(content[rt_idx:]):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    end_idx = rt_idx + i
                    break
        old_call = content[rt_idx:end_idx+1]
        extra = (
            ",\n                           project_hours_today=project_hours_today"
            ",\n                           project_hours_today_total=project_hours_today_total"
            ",\n                           projects_active=projects_active)"
        )
        new_call = old_call[:-1] + extra
        content = content.replace(old_call, new_call, 1)
        changes += 1
        print('✅ Dashboard varijable dodane')
    else:
        print('⚠️  dashboard.html render nije pronađen')
else:
    print('⚠️  Dashboard projekti već postoje')

# 3. Flask rute
ROUTES = '''

# \u2500\u2500\u2500 PROJEKTI \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _get_next_project_id():
    conn = get_db()
    year = datetime.now().year
    rows = conn.execute("SELECT auto_id FROM projects WHERE auto_id LIKE ?", (f"{year}-%",)).fetchall()
    conn.close()
    used = set()
    for r in rows:
        try: used.add(int(r['auto_id'].split('-')[1]))
        except: pass
    num = 1
    while num in used: num += 1
    return f"{year}-{num}"

@app.route('/projects')
@login_required
def projects_list():
    conn = get_db()
    sql = ("SELECT p.*, c.name as client_name, "
           "COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE project_id=p.id),0) as total_hours, "
           "COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE project_id=p.id AND date >= date('now','start of month')),0) as mtd_hours, "
           "COALESCE((SELECT MAX(date) FROM project_time_entries WHERE project_id=p.id),'') as last_entry_date "
           "FROM projects p LEFT JOIN clients c ON c.id=p.client_id ORDER BY p.status ASC, p.name ASC")
    projects = conn.execute(sql).fetchall()
    clients = conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    employees = conn.execute("SELECT id, name FROM employees ORDER BY name").fetchall()
    conn.close()
    return render_template('projects_list.html', projects=rows_to_dicts(projects),
                           clients=rows_to_dicts(clients), employees=rows_to_dicts(employees), active='projects')

@app.route('/api/projects', methods=['GET'])
@login_required
def api_projects_get():
    conn = get_db()
    rows = conn.execute("SELECT id, auto_id, name, color, status FROM projects WHERE status='active' ORDER BY name").fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))

@app.route('/api/projects', methods=['POST'])
@login_required
def api_project_save():
    data = request.json
    conn = get_db()
    now = datetime.now().isoformat()
    pid = data.get('id')
    name = (data.get('name') or '').strip()
    if not name:
        conn.close()
        return jsonify({'error': 'Naziv projekta je obavezan'}), 400
    client_id = data.get('client_id') or None
    color = data.get('color') or '#2d5986'
    status = data.get('status') or 'active'
    notes = data.get('notes') or ''
    if pid:
        conn.execute("UPDATE projects SET name=?, client_id=?, color=?, status=?, notes=?, updated_at=? WHERE id=?",
                     (name, client_id, color, status, notes, now, pid))
        conn.commit(); conn.close()
        audit('edit', module='projekti', entity='project', entity_id=int(pid), detail=name)
        return jsonify({'success': True, 'id': int(pid)})
    auto_id = _get_next_project_id()
    conn.execute("INSERT INTO projects (auto_id, name, client_id, color, status, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                 (auto_id, name, client_id, color, status, notes, now, now))
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    audit('create', module='projekti', entity='project', entity_id=new_id, detail=name)
    return jsonify({'success': True, 'id': new_id, 'auto_id': auto_id})

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
def api_project_delete(project_id):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit(); conn.close()
    audit('delete', module='projekti', entity='project', entity_id=project_id)
    return jsonify({'success': True})

@app.route('/api/projects/time', methods=['POST'])
@login_required
def api_project_time_save():
    data = request.json
    employee_id = data.get('employee_id')
    date_str = data.get('date')
    entries = data.get('entries', [])
    if not employee_id or not date_str:
        return jsonify({'error': 'employee_id i date su obavezni'}), 400
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("DELETE FROM project_time_entries WHERE employee_id=? AND date=?", (employee_id, date_str))
    total = 0
    for e in entries:
        hours = float(e.get('hours') or 0)
        if hours <= 0: continue
        conn.execute("INSERT INTO project_time_entries (project_id, employee_id, date, hours, notes, created_at) VALUES (?,?,?,?,?,?)",
                     (int(e['project_id']), int(employee_id), date_str, hours, e.get('notes') or '', now))
        total += hours
    conn.commit(); conn.close()
    audit('create', module='projekti', entity='project_time', detail=f'{date_str} - {total}h')
    return jsonify({'success': True, 'total_hours': total})

@app.route('/api/projects/time', methods=['GET'])
@login_required
def api_project_time_get():
    employee_id = request.args.get('employee_id')
    date_str = request.args.get('date')
    if not employee_id or not date_str: return jsonify([])
    conn = get_db()
    sql = ("SELECT pte.*, p.name as project_name, p.color FROM project_time_entries pte "
           "JOIN projects p ON p.id = pte.project_id WHERE pte.employee_id=? AND pte.date=? ORDER BY pte.hours DESC")
    rows = conn.execute(sql, (employee_id, date_str)).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))

@app.route('/api/projects/<int:project_id>/time-history')
@login_required
def api_project_time_history(project_id):
    conn = get_db()
    sql = ("SELECT pte.date, pte.hours, pte.notes, e.name as employee_name FROM project_time_entries pte "
           "JOIN employees e ON e.id = pte.employee_id WHERE pte.project_id=? ORDER BY pte.date DESC, pte.hours DESC")
    rows = conn.execute(sql, (project_id,)).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))

'''

if '/projects' not in content:
    for anchor in ['# \u2500\u2500\u2500 CAR LOGS', '# \u2500\u2500\u2500 SETTINGS API', "@app.route('/car-logs')","if __name__ == '__main__':"]:
        if anchor in content:
            content = content.replace(anchor, ROUTES + anchor, 1)
            changes += 1
            print('✅ Flask rute za projekte dodane')
            break
else:
    print('⚠️  Rute već postoje')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{"✅ Backend patch gotov" if changes else "❌ Bez promjena"} ({changes} izmjena)')
