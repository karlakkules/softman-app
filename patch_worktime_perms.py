#!/usr/bin/env python3
"""
patch_worktime_perms.py
1. worktime_list  — filtrira reports po korisniku/voditelju/adminu
2. worktime_new   — filtrira employees po korisniku/voditelju/adminu
                  — šalje existing_months da frontend sakrije zauzete
3. worktime_edit  — filtrira employees isto
4. save_worktime  — provjera smije li user snimati za tog zaposlenika
5. worktime_form.html — sakrij zauzete mjesece u dropdownu
6. worktime_list.html — prikaži samo vidljive redove
"""
import shutil, os

BASE      = os.path.expanduser('~/Projects/Softman_app')
APP_PY    = os.path.join(BASE, 'app.py')
WT_LIST   = os.path.join(BASE, 'templates', 'worktime_list.html')
WT_FORM   = os.path.join(BASE, 'templates', 'worktime_form.html')

def backup(p):
    if os.path.exists(p):
        shutil.copy2(p, p + '.bak5')
        print(f'  Backup: {p}.bak5')

# ── Helper koji se dodaje u app.py ──────────────────────────────────────────
HELPER_FUNC = '''
def get_worktime_allowed_employees(conn, user):
    """Vraća (employee_ids_list, is_manager) za worktime modul."""
    urow = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
    my_emp_id = urow['employee_id'] if urow and urow['employee_id'] else None

    if user.get('is_admin'):
        all_emps = [r['id'] for r in conn.execute("SELECT id FROM employees").fetchall()]
        return all_emps, True, my_emp_id

    # Provjeri je li voditelj
    managed = []
    if my_emp_id:
        managed = [r['id'] for r in conn.execute(
            "SELECT id FROM employees WHERE manager_id=?", (my_emp_id,)
        ).fetchall()]

    is_manager = len(managed) > 0
    # Uvijek uključi sebe
    allowed = list(set(([my_emp_id] if my_emp_id else []) + managed))
    return allowed, is_manager, my_emp_id

'''

# ── NOVA worktime_list ruta ──────────────────────────────────────────────────
OLD_WT_LIST = '''@app.route('/worktime')
@require_perm('can_view_worktime')
def worktime_list():
    audit('view', module='radno_vrijeme', entity='list')
    current_user = get_current_user() or {}
    conn = get_db()
    reports = conn.execute(\'\'\'
        SELECT wr.*, e.name as employee_name
        FROM worktime_reports wr
        LEFT JOIN employees e ON wr.employee_id = e.id
        ORDER BY wr.year DESC, wr.month DESC, e.name
    \'\'\').fetchall()
    employees = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()
    settings = {r[\'key\']: r[\'value\'] for r in conn.execute("SELECT * FROM settings").fetchall()}
    conn.close()
    import json as _json
    holidays_by_year = get_holidays_by_year()
    available_years = sorted(holidays_by_year.keys())
    conn2 = get_db()
    fund_years = [r[\'year\'] for r in conn2.execute("SELECT DISTINCT year FROM work_fund ORDER BY year").fetchall()]
    conn2.close()
    all_years = sorted(set(available_years) | set(fund_years))
    return render_template(\'worktime_list.html\',
                           reports=rows_to_dicts(reports),
                           employees=rows_to_dicts(employees),
                           months=MONTHS_HR,
                           active=\'worktime\',
                           settings=settings,
                           holidays_json=_json.dumps(holidays_by_year),
                           available_years=all_years,
                           is_admin=current_user.get(\'is_admin\', False))'''

NEW_WT_LIST = '''@app.route('/worktime')
@require_perm('can_view_worktime')
def worktime_list():
    audit('view', module='radno_vrijeme', entity='list')
    current_user = get_current_user() or {}
    conn = get_db()

    allowed_ids, is_manager, my_emp_id = get_worktime_allowed_employees(conn, current_user)

    if current_user.get('is_admin'):
        reports = conn.execute(\'\'\'
            SELECT wr.*, e.name as employee_name
            FROM worktime_reports wr
            LEFT JOIN employees e ON wr.employee_id = e.id
            ORDER BY wr.year DESC, wr.month DESC, e.name
        \'\'\').fetchall()
    elif allowed_ids:
        placeholders = \',\'.join(\'?\' for _ in allowed_ids)
        reports = conn.execute(f\'\'\'
            SELECT wr.*, e.name as employee_name
            FROM worktime_reports wr
            LEFT JOIN employees e ON wr.employee_id = e.id
            WHERE wr.employee_id IN ({placeholders})
            ORDER BY wr.year DESC, wr.month DESC, e.name
        \'\'\', allowed_ids).fetchall()
    else:
        reports = []

    employees = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()
    settings = {r[\'key\']: r[\'value\'] for r in conn.execute("SELECT * FROM settings").fetchall()}
    conn.close()
    import json as _json
    holidays_by_year = get_holidays_by_year()
    available_years = sorted(holidays_by_year.keys())
    conn2 = get_db()
    fund_years = [r[\'year\'] for r in conn2.execute("SELECT DISTINCT year FROM work_fund ORDER BY year").fetchall()]
    conn2.close()
    all_years = sorted(set(available_years) | set(fund_years))
    return render_template(\'worktime_list.html\',
                           reports=rows_to_dicts(reports),
                           employees=rows_to_dicts(employees),
                           months=MONTHS_HR,
                           active=\'worktime\',
                           settings=settings,
                           holidays_json=_json.dumps(holidays_by_year),
                           available_years=all_years,
                           is_admin=current_user.get(\'is_admin\', False),
                           is_manager=is_manager)'''

# ── NOVA worktime_new ruta ───────────────────────────────────────────────────
OLD_WT_NEW = '''@app.route('/worktime/new')
@require_perm('can_edit_worktime')
def worktime_new():
    conn = get_db()
    employees = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()
    settings = {r[\'key\']: r[\'value\'] for r in conn.execute("SELECT * FROM settings").fetchall()}
    conn.close()
    return render_template(\'worktime_form.html\',
                           report=None, entries={}, employees=rows_to_dicts(employees),
                           rows=WORKTIME_ROWS, months=MONTHS_HR,
                           holidays=ALL_HOLIDAYS,
                           holidays_by_year={2026: HOLIDAYS_2026, 2027: HOLIDAYS_2027, 2028: HOLIDAYS_2028},
                           work_fund=WORK_FUND_2026,
                           active=\'worktime\', settings=settings)'''

NEW_WT_NEW = '''@app.route('/worktime/new')
@require_perm('can_edit_worktime')
def worktime_new():
    user = get_current_user() or {}
    conn = get_db()
    allowed_ids, is_manager, my_emp_id = get_worktime_allowed_employees(conn, user)

    if user.get('is_admin'):
        employees = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()
    elif allowed_ids:
        placeholders = \',\'.join(\'?\' for _ in allowed_ids)
        employees = conn.execute(
            f"SELECT * FROM employees WHERE id IN ({placeholders}) ORDER BY name",
            allowed_ids
        ).fetchall()
    else:
        employees = []

    # Dohvati postojeće kombinacije (employee_id, year, month) za JS
    existing_months = rows_to_dicts(conn.execute(
        "SELECT employee_id, year, month FROM worktime_reports"
    ).fetchall())

    settings = {r[\'key\']: r[\'value\'] for r in conn.execute("SELECT * FROM settings").fetchall()}
    conn.close()
    return render_template(\'worktime_form.html\',
                           report=None, entries={}, employees=rows_to_dicts(employees),
                           rows=WORKTIME_ROWS, months=MONTHS_HR,
                           holidays=ALL_HOLIDAYS,
                           holidays_by_year={2026: HOLIDAYS_2026, 2027: HOLIDAYS_2027, 2028: HOLIDAYS_2028},
                           work_fund=WORK_FUND_2026,
                           active=\'worktime\', settings=settings,
                           existing_months=existing_months,
                           my_emp_id=my_emp_id)'''

# ── NOVA worktime_edit ruta (dodaj existing_months) ─────────────────────────
OLD_WT_EDIT_RET = '''    return render_template(\'worktime_form.html\',
                           report=row_to_dict(report), entries=entries,
                           employees=rows_to_dicts(employees),
                           rows=WORKTIME_ROWS, months=MONTHS_HR,
                           holidays=ALL_HOLIDAYS, work_fund=WORK_FUND_2026,
                           active=\'worktime\', settings=settings)'''

NEW_WT_EDIT_RET = '''    user = get_current_user() or {}
    allowed_ids, is_manager, my_emp_id = get_worktime_allowed_employees(conn2, user)
    existing_months = rows_to_dicts(conn2.execute(
        "SELECT employee_id, year, month FROM worktime_reports WHERE id != ?", (report_id,)
    ).fetchall())
    conn2.close()
    return render_template(\'worktime_form.html\',
                           report=row_to_dict(report), entries=entries,
                           employees=rows_to_dicts(employees),
                           rows=WORKTIME_ROWS, months=MONTHS_HR,
                           holidays=ALL_HOLIDAYS, work_fund=WORK_FUND_2026,
                           active=\'worktime\', settings=settings,
                           existing_months=existing_months,
                           my_emp_id=my_emp_id)'''

OLD_WT_EDIT_CONN = '''    settings = {r[\'key\']: r[\'value\'] for r in conn.execute("SELECT * FROM settings").fetchall()}
    conn.close()
    # Build entries dict: {row_num: {day: hours}}'''

NEW_WT_EDIT_CONN = '''    settings = {r[\'key\']: r[\'value\'] for r in conn.execute("SELECT * FROM settings").fetchall()}
    conn2 = conn
    # Build entries dict: {row_num: {day: hours}}'''

# ── save_worktime — provjeri smije li user snimati za tog zaposlenika ────────
OLD_SAVE_CHECK = '''    # Check confirm permission
    if status == \'confirmed\':
        user = get_current_user()
        if not user.get(\'is_admin\') and not user.get(\'can_confirm_worktime\'):
            return jsonify({\'error\': \'Nemate pravo potvrđivanja izvješća o radnom vremenu\'}), 403'''

NEW_SAVE_CHECK = '''    user = get_current_user()
    # Provjeri smije li user uopće snimati za tog zaposlenika
    if not user.get('is_admin'):
        _conn_chk = get_db()
        _allowed, _, _my_id = get_worktime_allowed_employees(_conn_chk, user)
        _conn_chk.close()
        if employee_id and int(employee_id) not in _allowed:
            return jsonify({'error': 'Nemate pravo kreirati evidenciju za ovog zaposlenika'}), 403
    # Check confirm permission
    if status == \'confirmed\':
        if not user.get(\'is_admin\') and not user.get(\'can_confirm_worktime\'):
            return jsonify({\'error\': \'Nemate pravo potvrđivanja izvješća o radnom vremenu\'}), 403'''

# Remove duplicate user = get_current_user() later in save_worktime
OLD_DUPLICATE_USER = '''    # Check confirm permission
    if status == \'confirmed\':
        user = get_current_user()'''
NEW_DUPLICATE_USER = '''    # Check confirm permission
    if status == \'confirmed\':'''


def patch_app():
    with open(APP_PY, 'r', encoding='utf-8') as f:
        c = f.read()

    # A. Helper funkcija
    if 'def get_worktime_allowed_employees' in c:
        print('  [app.py] Helper već postoji.')
    else:
        anchor = '@app.route(\'/worktime\')\n@require_perm(\'can_view_worktime\')\ndef worktime_list():'
        if anchor in c:
            c = c.replace(anchor, HELPER_FUNC + anchor, 1)
            print('  [app.py] ✅ Helper dodan')
        else:
            print('  [app.py] ❌ Anchor za helper nije pronađen!')

    # B. worktime_list
    if OLD_WT_LIST in c:
        c = c.replace(OLD_WT_LIST, NEW_WT_LIST, 1)
        print('  [app.py] ✅ worktime_list ažuriran')
    else:
        print('  [app.py] ❌ worktime_list anchor nije pronađen!')

    # C. worktime_new
    if OLD_WT_NEW in c:
        c = c.replace(OLD_WT_NEW, NEW_WT_NEW, 1)
        print('  [app.py] ✅ worktime_new ažuriran')
    else:
        print('  [app.py] ❌ worktime_new anchor nije pronađen!')

    # D. worktime_edit — najprije zamijeni conn.close() s conn2 = conn
    if 'conn2 = conn' in c:
        print('  [app.py] worktime_edit conn2 već postoji.')
    elif OLD_WT_EDIT_CONN in c:
        c = c.replace(OLD_WT_EDIT_CONN, NEW_WT_EDIT_CONN, 1)
        print('  [app.py] ✅ worktime_edit conn2 dodan')
    else:
        print('  [app.py] ❌ worktime_edit conn anchor nije pronađen!')

    # E. worktime_edit — zamijeni return render_template
    if 'existing_months' in c and 'worktime_edit' in c:
        print('  [app.py] worktime_edit existing_months već postoji.')
    elif OLD_WT_EDIT_RET in c:
        c = c.replace(OLD_WT_EDIT_RET, NEW_WT_EDIT_RET, 1)
        print('  [app.py] ✅ worktime_edit return ažuriran')
    else:
        print('  [app.py] ❌ worktime_edit return anchor nije pronađen!')

    # F. save_worktime — provjera prava
    if 'get_worktime_allowed_employees' in c and 'Nemate pravo kreirati evidenciju' in c:
        print('  [app.py] save_worktime provjera već postoji.')
    elif OLD_SAVE_CHECK in c:
        c = c.replace(OLD_SAVE_CHECK, NEW_SAVE_CHECK, 1)
        # Ukloni duplikat user = get_current_user()
        c = c.replace(
            "    if status == 'confirmed':\n        user = get_current_user()\n        if not user",
            "    if status == 'confirmed':\n        if not user",
            1
        )
        print('  [app.py] ✅ save_worktime provjera prava dodana')
    else:
        print('  [app.py] ❌ save_worktime anchor nije pronađen!')

    with open(APP_PY, 'w', encoding='utf-8') as f:
        f.write(c)


def patch_worktime_form():
    with open(WT_FORM, 'r', encoding='utf-8') as f:
        c = f.read()

    if 'existing_months' in c and 'filterMonths' in c:
        print('  [worktime_form.html] filterMonths već postoji.')
        return

    # Dodaj JS logiku za sakrivanje zauzetih mjeseci
    FILTER_MONTHS_JS = """
// ── Sakrij zauzete mjesece ────────────────────────────────────────────────────
const EXISTING_MONTHS = {{ existing_months | tojson if existing_months is defined else '[]' }};
const MY_EMP_ID = {{ my_emp_id | tojson if my_emp_id is defined else 'null' }};

function filterMonths() {
  const empId = parseInt(document.getElementById('wt-employee')?.value) || null;
  const yearEl = document.getElementById('wt-year');
  const monthEl = document.getElementById('wt-month');
  if (!empId || !yearEl || !monthEl) return;
  const year = parseInt(yearEl.value);
  // Skupi zauzete mjesece za tog zaposlenika i godinu
  const taken = new Set(
    EXISTING_MONTHS
      .filter(m => m.employee_id === empId && m.year === year)
      .map(m => m.month)
  );
  Array.from(monthEl.options).forEach(opt => {
    const v = parseInt(opt.value);
    if (!v) return; // skip placeholder
    opt.disabled = taken.has(v);
    opt.style.color = taken.has(v) ? '#bbb' : '';
    opt.textContent = opt.textContent.replace(' ✓', '') + (taken.has(v) ? ' ✓' : '');
  });
  // Ako trenutno odabrani mjesec je zauzet, resetiraj
  if (taken.has(parseInt(monthEl.value))) {
    monthEl.value = '';
  }
}

"""

    # Ubaci JS prije DOMContentLoaded
    OLD_DOM = "// Build on load\ndocument.addEventListener('DOMContentLoaded', () => {"
    if OLD_DOM in c:
        c = c.replace(OLD_DOM, FILTER_MONTHS_JS + OLD_DOM, 1)
        print('  [worktime_form.html] ✅ filterMonths JS dodan')
    else:
        # Fallback
        OLD_DOM2 = "document.addEventListener('DOMContentLoaded', () => {"
        idx = c.rfind(OLD_DOM2)
        if idx > 0:
            c = c[:idx] + FILTER_MONTHS_JS + c[idx:]
            print('  [worktime_form.html] ✅ filterMonths JS dodan (fallback)')
        else:
            print('  [worktime_form.html] ❌ DOMContentLoaded anchor nije pronađen!')

    # Dodaj onchange="filterMonths()" na employee i year select
    OLD_EMP = 'id="wt-employee" {% if locked %}disabled{% endif %} onchange="loadLeaveForMonth()"'
    NEW_EMP = 'id="wt-employee" {% if locked %}disabled{% endif %} onchange="loadLeaveForMonth(); filterMonths()"'
    if 'filterMonths' not in c or OLD_EMP in c:
        c = c.replace(OLD_EMP, NEW_EMP, 1)

    OLD_YEAR = 'id="wt-year" {% if locked %}disabled{% endif %} onchange="reloadGrid()"'
    NEW_YEAR = 'id="wt-year" {% if locked %}disabled{% endif %} onchange="reloadGrid(); filterMonths()"'
    if OLD_YEAR in c:
        c = c.replace(OLD_YEAR, NEW_YEAR, 1)

    # Pozovi filterMonths u DOMContentLoaded
    OLD_DOM_CALL = "  buildGrid();\n  if (IS_NEW) autoFillGrid();\n  loadLeaveForMonth();\n});"
    NEW_DOM_CALL = "  buildGrid();\n  if (IS_NEW) autoFillGrid();\n  loadLeaveForMonth();\n  if (IS_NEW) filterMonths();\n});"
    if OLD_DOM_CALL in c:
        c = c.replace(OLD_DOM_CALL, NEW_DOM_CALL, 1)
        print('  [worktime_form.html] ✅ filterMonths poziv u DOMContentLoaded')

    with open(WT_FORM, 'w', encoding='utf-8') as f:
        f.write(c)


def patch_worktime_list():
    with open(WT_LIST, 'r', encoding='utf-8') as f:
        c = f.read()

    if 'filterWT' in c and 'is_manager' in c:
        print('  [worktime_list.html] is_manager već postoji.')
        return

    # Dodaj is_manager provjeru za brisanje — voditelj ne smije brisati tuđe
    OLD_DELETE_BTN = '''              {% if current_user.get('is_admin') or current_user.get('can_copy_worktime') %}
              <a href="/worktime/{{ r.id }}/copy"'''
    NEW_DELETE_BTN = '''              {% if current_user.get('is_admin') or current_user.get('can_copy_worktime') or is_manager %}
              <a href="/worktime/{{ r.id }}/copy"'''
    if OLD_DELETE_BTN in c:
        c = c.replace(OLD_DELETE_BTN, NEW_DELETE_BTN, 1)
        print('  [worktime_list.html] ✅ is_manager dodan za copy/delete gumb')

    # Dodaj JS varijablu is_manager
    OLD_IS_ADMIN = 'const IS_ADMIN = {{ \'true\' if is_admin else \'false\' }};'
    NEW_IS_ADMIN = 'const IS_ADMIN = {{ \'true\' if is_admin else \'false\' }};\nconst IS_MANAGER = {{ \'true\' if is_manager is defined and is_manager else \'false\' }};'
    if 'IS_MANAGER' not in c and OLD_IS_ADMIN in c:
        c = c.replace(OLD_IS_ADMIN, NEW_IS_ADMIN, 1)
        print('  [worktime_list.html] ✅ IS_MANAGER JS varijabla dodana')

    with open(WT_LIST, 'w', encoding='utf-8') as f:
        f.write(c)


if __name__ == '__main__':
    print('=== PATCH: Worktime permissions ===\n')
    for p in [APP_PY, WT_LIST, WT_FORM]:
        backup(p)

    print('\n1. Patch app.py...')
    patch_app()

    print('\n2. Patch worktime_form.html...')
    patch_worktime_form()

    print('\n3. Patch worktime_list.html...')
    patch_worktime_list()

    print('\n=== ✅ GOTOVO! ===')
    print('Restart: python app.py')
    print('Git: cd ~/Projects/Softman_app && git add . && git commit -m "feat: worktime prava pristupa po voditelju" && git push origin main')
