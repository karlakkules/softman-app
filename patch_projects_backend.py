#!/usr/bin/env python3
"""
Patch: app.py — novi modul Projekti
  1. Migracija: tablice projects i project_time_entries
  2. Rute: /projects, /projects/new, /projects/<id>/edit
  3. API: GET/POST /api/projects, POST /api/projects/<id>/time, DELETE, GET hours
  4. Dashboard: project_hours_today, projects_active u index ruti
"""
import os, shutil, re

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

bak = os.path.join(BACKUP_DIR, 'app.py.bak_projects')
shutil.copy2(APP, bak)
print(f'✅ Backup: {bak}')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. DB Migracija ───────────────────────────────────────────────────────────
MIG_ANCHOR = "# Migration: narudzbenica_path u quotes"
MIG_NEW = """# Migration: projekti
    c.executescript('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auto_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            client_id INTEGER,
            status TEXT DEFAULT 'active',
            color TEXT DEFAULT '#2d5986',
            notes TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS project_time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            hours REAL NOT NULL,
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
    ''')

    # Migration: narudzbenica_path u quotes"""

if "CREATE TABLE IF NOT EXISTS projects" not in content and MIG_ANCHOR in content:
    content = content.replace(MIG_ANCHOR, MIG_NEW, 1)
    changes += 1
    print('✅ Migracija projects/project_time_entries dodana')
else:
    print('⚠️  Migracija projekata već postoji ili anchor nije pronađen')

# ── 2. Dashboard — dodaj project_hours_today i projects_active u index() ─────
DASH_ANCHOR = "    return render_template('dashboard.html'"
DASH_INSERT = """    # Projekti — sati danas i aktivni projekti
    today_str = datetime.now().strftime('%Y-%m-%d')
    user_obj = get_current_user()
    emp_today = conn.execute(
        "SELECT id FROM employees WHERE name LIKE ?",
        (f"%{user_obj.get('display_name','').split()[0] if user_obj.get('display_name') else ''}%",)
    ).fetchone()
    project_hours_today = []
    if emp_today:
        rows_ph = conn.execute("""
            SELECT p.name, p.color, pte.hours, pte.notes
            FROM project_time_entries pte
            JOIN projects p ON p.id = pte.project_id
            WHERE pte.employee_id=? AND pte.date=?
            ORDER BY pte.hours DESC
        """, (emp_today['id'], today_str)).fetchall()
        project_hours_today = rows_to_dicts(rows_ph)
    projects_active = conn.execute(
        "SELECT COUNT(*) as cnt FROM projects WHERE status='active'"
    ).fetchone()['cnt']
    project_hours_today_total = round(sum(r['hours'] for r in project_hours_today), 2)

    """

DASH_RENDER_OLD = "    return render_template('dashboard.html'"
DASH_RENDER_NEW = """    return render_template('dashboard.html',
                           project_hours_today=project_hours_today,
                           project_hours_today_total=project_hours_today_total,
                           projects_active=projects_active,"""

# Provjeri je li već patchano
if 'project_hours_today' not in content:
    # Nađi zadnji conn.close() prije render_template u index ruti
    idx = content.find("    return render_template('dashboard.html'")
    if idx != -1:
        # Ubaci insert prije render_template
        content = content[:idx] + DASH_INSERT + content[idx:]
        # Dodaj nove varijable u render_template poziv
        old_rt = "    return render_template('dashboard.html'"
        # Nađi točan poziv (sad je već pomaknut)
        rt_idx = content.find(old_rt)
        if rt_idx != -1:
            # Nađi kraj tog poziva (matching zagrada)
            depth = 0
            end_idx = rt_idx
            for i, ch in enumerate(content[rt_idx:]):
                if ch == '(': depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        end_idx = rt_idx + i
                        break
            old_call = content[rt_idx:end_idx+1]
            # Dodaj varijable pred zadnju zagradu
            new_call = old_call[:-1] + ",\n                           project_hours_today=project_hours_today,\n                           project_hours_today_total=project_hours_today_total,\n                           projects_active=projects_active)"
            content = content.replace(old_call, new_call, 1)
            changes += 1
            print('✅ Dashboard varijable dodane u index()')
        else:
            print('⚠️  render_template poziv nije pronađen')
    else:
        print('⚠️  dashboard.html render nije pronađen')
else:
    print('⚠️  Dashboard projekti već postoje')

# ── 3. Flask rute ─────────────────────────────────────────────────────────────
NEW_ROUTES = '''

# ─── PROJEKTI ─────────────────────────────────────────────────────────────────

def _get_next_project_id():
    conn = get_db()
    year = datetime.now().year
    rows = conn.execute(
        "SELECT auto_id FROM projects WHERE auto_id LIKE ?", (f"{year}-%",)
    ).fetchall()
    conn.close()
    used = set()
    for r in rows:
        try: used.add(int(r['auto_id'].split('-')[1]))
        except: pass
    num = 1
    while num in used:
        num += 1
    return f"{year}-{num}"


@app.route('/projects')
@login_required
def projects_list():
    conn = get_db()
    projects = conn.execute("""
        SELECT p.*, c.name as client_name,
               COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE project_id=p.id),0) as total_hours,
               COALESCE((SELECT SUM(hours) FROM project_time_entries
                         WHERE project_id=p.id
                         AND date >= date('now','start of month')),0) as mtd_hours,
               COALESCE((SELECT MAX(date) FROM project_time_entries WHERE project_id=p.id),'') as last_entry_date
        FROM projects p
        LEFT JOIN clients c ON c.id=p.client_id
        ORDER BY p.status ASC, p.name ASC
    """).fetchall()
    clients = conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    employees = conn.execute("SELECT id, name FROM employees ORDER BY name").fetchall()
    conn.close()
    return render_template('projects_list.html',
                           projects=rows_to_dicts(projects),
                           clients=rows_to_dicts(clients),
                           employees=rows_to_dicts(employees),
                           active='projects')


@app.route('/api/projects', methods=['GET'])
@login_required
def api_projects_get():
    conn = get_db()
    projects = conn.execute(
        "SELECT id, auto_id, name, color, status FROM projects WHERE status='active' ORDER BY name"
    ).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(projects))


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
        conn.execute(
            "UPDATE projects SET name=?, client_id=?, color=?, status=?, notes=?, updated_at=? WHERE id=?",
            (name, client_id, color, status, notes, now, pid)
        )
        conn.commit()
        conn.close()
        audit('edit', module='projekti', entity='project', entity_id=int(pid), detail=name)
        return jsonify({'success': True, 'id': int(pid)})
    else:
        auto_id = _get_next_project_id()
        conn.execute(
            "INSERT INTO projects (auto_id, name, client_id, color, status, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (auto_id, name, client_id, color, status, notes, now, now)
        )
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
    conn.commit()
    conn.close()
    audit('delete', module='projekti', entity='project', entity_id=project_id)
    return jsonify({'success': True})


@app.route('/api/projects/time', methods=['POST'])
@login_required
def api_project_time_save():
    """Spremi dnevne sate po projektima — prima listu unosa za jedan dan."""
    data = request.json
    employee_id = data.get('employee_id')
    date_str = data.get('date')
    entries = data.get('entries', [])  # [{project_id, hours, notes}]

    if not employee_id or not date_str:
        return jsonify({'error': 'employee_id i date su obavezni'}), 400

    conn = get_db()
    now = datetime.now().isoformat()

    # Obriši postojeće unose za taj dan i zaposlenika
    conn.execute(
        "DELETE FROM project_time_entries WHERE employee_id=? AND date=?",
        (employee_id, date_str)
    )

    total = 0
    for e in entries:
        hours = float(e.get('hours') or 0)
        if hours <= 0:
            continue
        conn.execute(
            "INSERT INTO project_time_entries (project_id, employee_id, date, hours, notes, created_at) VALUES (?,?,?,?,?,?)",
            (int(e['project_id']), int(employee_id), date_str, hours, e.get('notes') or '', now)
        )
        total += hours

    conn.commit()
    conn.close()
    audit('create', module='projekti', entity='project_time', detail=f'{date_str} · {total}h')
    return jsonify({'success': True, 'total_hours': total})


@app.route('/api/projects/time', methods=['GET'])
@login_required
def api_project_time_get():
    """Dohvati sate za zaposlenika i datum."""
    employee_id = request.args.get('employee_id')
    date_str = request.args.get('date')
    if not employee_id or not date_str:
        return jsonify([])
    conn = get_db()
    rows = conn.execute("""
        SELECT pte.*, p.name as project_name, p.color
        FROM project_time_entries pte
        JOIN projects p ON p.id = pte.project_id
        WHERE pte.employee_id=? AND pte.date=?
        ORDER BY pte.hours DESC
    """, (employee_id, date_str)).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))


@app.route('/api/projects/<int:project_id>/time-history')
@login_required
def api_project_time_history(project_id):
    """Timeline unosa za projekt — grupirano po datumu."""
    conn = get_db()
    rows = conn.execute("""
        SELECT pte.date, pte.hours, pte.notes, e.name as employee_name
        FROM project_time_entries pte
        JOIN employees e ON e.id = pte.employee_id
        WHERE pte.project_id=?
        ORDER BY pte.date DESC, pte.hours DESC
    """, (project_id,)).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))

'''

if '/projects' not in content:
    # Ubaci prije # ─── CAR LOGS ili sličnog markera
    for anchor in ['# ─── CAR LOGS', '# ─── SETTINGS API', '@app.route(\'/car-logs\')']:
        if anchor in content:
            content = content.replace(anchor, NEW_ROUTES + anchor, 1)
            changes += 1
            print(f'✅ Flask rute za projekte dodane (anchor: {anchor})')
            break
    else:
        # Fallback — dodaj na kraj prije if __name__
        content = content.replace("if __name__ == '__main__':", NEW_ROUTES + "\nif __name__ == '__main__':")
        changes += 1
        print('✅ Flask rute za projekte dodane (fallback)')
else:
    print('⚠️  Rute za projekte već postoje')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{"✅ Backend patch gotov" if changes else "❌ Bez promjena"} ({changes} izmjena)')
print('\nSljedeći koraci:')
print('  1. Kopiraj projects_list.html u templates/')
print('  2. Dodaj nav link u base.html')
print('  3. Restart Flask')
