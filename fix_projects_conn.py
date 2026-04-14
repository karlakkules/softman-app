#!/usr/bin/env python3
"""Popravak: Cannot operate on a closed database — projekti koriste svoju konekciju."""
import os, shutil, re

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
shutil.copy2(APP, os.path.join(BACKUP_DIR, 'app.py.bak_projects_connfix'))
print('✅ Backup napravljen')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

# Stari kod koji patch ubacio (koristi zatvoreni conn)
OLD = (
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

# Novi kod koji otvara svježu konekciju
NEW = (
    "    # Projekti danas — svježa konekcija\n"
    "    today_str = datetime.now().strftime('%Y-%m-%d')\n"
    "    user_obj = get_current_user()\n"
    "    _disp = (user_obj.get('display_name') or '').split(' ')[0]\n"
    "    _conn_proj = get_db()\n"
    "    emp_today = _conn_proj.execute(\n"
    "        'SELECT id FROM employees WHERE name LIKE ?', ('%' + _disp + '%',)\n"
    "    ).fetchone() if _disp else None\n"
    "    project_hours_today = []\n"
    "    if emp_today:\n"
    "        _sql = ('SELECT p.name, p.color, pte.hours '\n"
    "                'FROM project_time_entries pte '\n"
    "                'JOIN projects p ON p.id = pte.project_id '\n"
    "                'WHERE pte.employee_id=? AND pte.date=? ORDER BY pte.hours DESC')\n"
    "        project_hours_today = rows_to_dicts(_conn_proj.execute(_sql, (emp_today['id'], today_str)).fetchall())\n"
    "    try:\n"
    "        projects_active = _conn_proj.execute(\n"
    "            'SELECT COUNT(*) as cnt FROM projects WHERE status=?', ('active',)\n"
    "        ).fetchone()['cnt']\n"
    "    except Exception:\n"
    "        projects_active = 0\n"
    "    _conn_proj.close()\n"
    "    project_hours_today_total = round(sum(r['hours'] for r in project_hours_today), 2)\n\n"
)

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    print('✅ Konekcija popravljena — koristi se svježa _conn_proj')
else:
    print('❌ Stari blok nije pronađen — tražim po parcijalnom ključu...')
    # Pokušaj pronaći i prikazati kontekst
    idx = content.find("    # Projekti danas")
    if idx != -1:
        print(f'   Pronađen blok na liniji ~{content[:idx].count(chr(10))+1}:')
        print(repr(content[idx:idx+400]))
    else:
        print('   Blok "# Projekti danas" nije pronađen u app.py!')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print('\nPokreni: python3 app.py')
