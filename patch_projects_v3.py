#!/usr/bin/env python3
"""
Patch: Projekti — 5 ispravaka:
1. Fix duplog projekta (upsert logika)
2. Dodjela zaposlenika na projekte (nova tablica project_employees)
3. Filtriranje projekata prema dodjeli
4. Migracija za can_manage_projects pravo
5. Backend za "nedostaje ovaj mjesec" kalkulator
"""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
shutil.copy2(APP, os.path.join(BACKUP_DIR, 'app.py.bak_projects_v3'))
print('✅ Backup napravljen')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Migracija: project_employees + can_manage_projects ─────────────────────
MIG_ANCHOR = "# Migration: podprojekti"
MIG_NEW = (
    "# Migration: project_employees i can_manage_projects\n"
    "    c.executescript('''\n"
    "        CREATE TABLE IF NOT EXISTS project_employees (\n"
    "            id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    "            project_id INTEGER NOT NULL,\n"
    "            employee_id INTEGER NOT NULL,\n"
    "            created_at TEXT,\n"
    "            UNIQUE(project_id, employee_id),\n"
    "            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,\n"
    "            FOREIGN KEY (employee_id) REFERENCES employees(id)\n"
    "        );\n"
    "    ''')\n"
    "    try:\n"
    "        c.execute('ALTER TABLE profiles ADD COLUMN can_manage_projects INTEGER DEFAULT 0')\n"
    "    except: pass\n\n"
    "    # Migration: podprojekti"
)

if "CREATE TABLE IF NOT EXISTS project_employees" not in content and MIG_ANCHOR in content:
    content = content.replace(MIG_ANCHOR, MIG_NEW, 1)
    changes += 1
    print('✅ Migracija project_employees dodana')
else:
    print('⚠️  Migracija project_employees već postoji ili anchor nije pronađen')

# ── 2. Fix projects_list rute — filtriraj prema dodjeli + dodaj employees ──────
OLD_PROJ_LIST = (
    "    sql = (\"SELECT p.*, c.name as client_name, \"\n"
    "           \"COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE project_id=p.id),0) as total_hours, \"\n"
    "           \"COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE project_id=p.id AND date >= date('now','start of month')),0) as mtd_hours, \"\n"
    "           \"COALESCE((SELECT MAX(date) FROM project_time_entries WHERE project_id=p.id),'') as last_entry_date \"\n"
    "           \"FROM projects p LEFT JOIN clients c ON c.id=p.client_id ORDER BY p.status ASC, p.name ASC\")\n"
    "    projects = conn.execute(sql).fetchall()\n"
    "    clients = conn.execute(\"SELECT id, name FROM clients ORDER BY name\").fetchall()\n"
    "    employees = conn.execute(\"SELECT id, name FROM employees ORDER BY name\").fetchall()\n"
    "    conn.close()\n"
    "    return render_template('projects_list.html', projects=rows_to_dicts(projects),\n"
    "                           clients=rows_to_dicts(clients), employees=rows_to_dicts(employees), active='projects')"
)
NEW_PROJ_LIST = (
    "    user = get_current_user()\n"
    "    is_admin = user.get('is_admin') if user else False\n"
    "    can_manage = is_admin or bool(user.get('can_manage_projects') if user else False)\n"
    "    # Admin/manager vidi sve; zaposlenik vidi samo dodijeljene projekte\n"
    "    if can_manage:\n"
    "        sql = (\"SELECT p.*, c.name as client_name, \"\n"
    "               \"COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE project_id=p.id),0) as total_hours, \"\n"
    "               \"COALESCE((SELECT SUM(CASE WHEN date >= date('now','start of month') THEN hours ELSE 0 END) FROM project_time_entries WHERE project_id=p.id),0) as mtd_hours, \"\n"
    "               \"COALESCE((SELECT MAX(date) FROM project_time_entries WHERE project_id=p.id),'') as last_entry_date \"\n"
    "               \"FROM projects p LEFT JOIN clients c ON c.id=p.client_id ORDER BY p.status ASC, p.name ASC\")\n"
    "        projects = conn.execute(sql).fetchall()\n"
    "    else:\n"
    "        # Nađi employee_id za ovog korisnika\n"
    "        disp = (user.get('display_name') or '').strip()\n"
    "        emp = conn.execute('SELECT id FROM employees WHERE name=? OR name LIKE ?', (disp, f'%{disp}%')).fetchone()\n"
    "        if emp:\n"
    "            sql = (\"SELECT p.*, c.name as client_name, \"\n"
    "                   \"COALESCE((SELECT SUM(hours) FROM project_time_entries WHERE project_id=p.id AND employee_id=?),0) as total_hours, \"\n"
    "                   \"COALESCE((SELECT SUM(CASE WHEN date >= date('now','start of month') THEN hours ELSE 0 END) \"\n"
    "                   \"         FROM project_time_entries WHERE project_id=p.id AND employee_id=?),0) as mtd_hours, \"\n"
    "                   \"COALESCE((SELECT MAX(date) FROM project_time_entries WHERE project_id=p.id AND employee_id=?),'') as last_entry_date \"\n"
    "                   \"FROM projects p LEFT JOIN clients c ON c.id=p.client_id \"\n"
    "                   \"JOIN project_employees pe ON pe.project_id=p.id AND pe.employee_id=? \"\n"
    "                   \"WHERE p.status='active' ORDER BY p.name ASC\")\n"
    "            projects = conn.execute(sql, (emp['id'], emp['id'], emp['id'], emp['id'])).fetchall()\n"
    "        else:\n"
    "            projects = []\n"
    "    clients = conn.execute('SELECT id, name FROM clients ORDER BY name').fetchall()\n"
    "    employees = conn.execute('SELECT id, name FROM employees ORDER BY name').fetchall()\n"
    "    # Za svaki projekt dohvati dodijeljene zaposlenike\n"
    "    project_employees_map = {}\n"
    "    for pe_row in conn.execute('SELECT pe.project_id, e.id, e.name FROM project_employees pe JOIN employees e ON e.id=pe.employee_id').fetchall():\n"
    "        pid = pe_row['project_id']\n"
    "        if pid not in project_employees_map: project_employees_map[pid] = []\n"
    "        project_employees_map[pid].append({'id': pe_row['id'], 'name': pe_row['name']})\n"
    "    conn.close()\n"
    "    return render_template('projects_list.html', projects=rows_to_dicts(projects),\n"
    "                           clients=rows_to_dicts(clients), employees=rows_to_dicts(employees),\n"
    "                           project_employees_map=project_employees_map,\n"
    "                           can_manage=can_manage, active='projects')"
)

if OLD_PROJ_LIST in content:
    content = content.replace(OLD_PROJ_LIST, NEW_PROJ_LIST, 1)
    changes += 1
    print('✅ projects_list ruta nadograđena (dodjela zaposlenika)')
else:
    print('⚠️  projects_list ruta nije pronađena za modifikaciju')

# ── 3. Nova API ruta za dodjelu zaposlenika na projekt ───────────────────────
ASSIGN_ROUTES = '''
@app.route('/api/projects/<int:project_id>/employees', methods=['GET'])
@login_required
def api_project_employees_get(project_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT e.id, e.name FROM project_employees pe JOIN employees e ON e.id=pe.employee_id WHERE pe.project_id=? ORDER BY e.name",
        (project_id,)
    ).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))

@app.route('/api/projects/<int:project_id>/employees', methods=['POST'])
@login_required
def api_project_employees_save(project_id):
    """Postavi listu zaposlenika za projekt (zamijeni sve)."""
    data = request.json
    employee_ids = data.get('employee_ids', [])
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("DELETE FROM project_employees WHERE project_id=?", (project_id,))
    for emp_id in employee_ids:
        try:
            conn.execute("INSERT INTO project_employees (project_id, employee_id, created_at) VALUES (?,?,?)",
                         (project_id, int(emp_id), now))
        except: pass
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/projects/<int:project_id>/missing-hours')
@login_required
def api_project_missing_hours(project_id):
    """Izračun: fond sati ovog mjeseca - godišnji - evidentiran po projektima (max 8h/dan)."""
    from datetime import date as _date, timedelta as _td
    import calendar as _cal
    employee_id = request.args.get('employee_id')
    if not employee_id:
        return jsonify({'error': 'employee_id obavezan'}), 400
    now = datetime.now()
    year, month = now.year, now.month
    conn = get_db()
    # Fond sati za ovaj mjesec
    fund_row = conn.execute(
        "SELECT radni FROM work_fund WHERE year=? AND month=?", (year, month)
    ).fetchone()
    fond = fund_row['radni'] if fund_row else 0
    # Godišnji odmor iz worktime_entries (row 16 = Godišnji odmor)
    wt_report = conn.execute(
        "SELECT wr.id FROM worktime_reports wr WHERE wr.employee_id=? AND wr.year=? AND wr.month=?",
        (employee_id, year, month)
    ).fetchone()
    vacation_hours = 0
    if wt_report:
        vac = conn.execute(
            "SELECT SUM(hours) as h FROM worktime_entries WHERE report_id=? AND row_num=16",
            (wt_report['id'],)
        ).fetchone()
        vacation_hours = float(vac['h'] or 0) if vac else 0
    # Evidentirani sati po projektima ovaj mjesec (max 8h/dan)
    first_day = f"{year}-{month:02d}-01"
    last_day_num = _cal.monthrange(year, month)[1]
    last_day = f"{year}-{month:02d}-{last_day_num:02d}"
    daily_rows = conn.execute(
        "SELECT date, SUM(hours) as h FROM project_time_entries "
        "WHERE employee_id=? AND date>=? AND date<=? GROUP BY date",
        (employee_id, first_day, last_day)
    ).fetchall()
    conn.close()
    project_hours = sum(min(float(r['h']), 8.0) for r in daily_rows)
    missing = max(0, fond - vacation_hours - project_hours)
    return jsonify({
        'fond': fond,
        'vacation_hours': vacation_hours,
        'project_hours': round(project_hours, 1),
        'missing': round(missing, 1),
        'year': year,
        'month': month
    })

'''

if '/api/projects/<int:project_id>/employees' not in content:
    anchor = "@app.route('/api/projects/<int:project_id>/subprojects'"
    if anchor in content:
        content = content.replace(anchor, ASSIGN_ROUTES + anchor, 1)
        changes += 1
        print('✅ Rute za dodjelu zaposlenika dodane')
    else:
        anchor2 = "def api_subprojects_get"
        if anchor2 in content:
            content = content.replace(anchor2, ASSIGN_ROUTES.strip() + "\n\ndef api_subprojects_get", 1)
            changes += 1
            print('✅ Rute za dodjelu zaposlenika dodane (fallback)')
        else:
            print('⚠️  Anchor za employee rute nije pronađen')
else:
    print('⚠️  Employee rute već postoje')

# ── 4. Dodaj can_manage_projects u PERM_LABELS i PERM_GROUPS ─────────────────
OLD_PERM = "    'can_view_loans': 'Pozajmice — pregled',"
NEW_PERM = ("    'can_view_loans': 'Pozajmice — pregled',\n"
            "    'can_manage_projects': 'Projekti — upravljanje i dodjela',")

if "'can_manage_projects'" not in content and OLD_PERM in content:
    content = content.replace(OLD_PERM, NEW_PERM, 1)
    changes += 1
    print('✅ can_manage_projects dodan u PERM_LABELS')
else:
    print('⚠️  can_manage_projects već postoji ili PERM_LABELS anchor nije pronađen')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{"✅ Backend patch gotov" if changes else "❌ Bez promjena"} ({changes} izmjena)')
print('Pokreni: python3 app.py')
