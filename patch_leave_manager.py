#!/usr/bin/env python3
"""
patch_leave_manager.py
Popravlja tko vidi zahtjeve za godišnji odmor:
  - Admin: vidi sve
  - can_approve_leave profil: vidi sve
  - Voditelj (employee.manager_id == current_emp_id): vidi zahtjeve svojih podređenih I svoje vlastite
  - Zaposlenik: vidi samo svoje

Također popravlja is_approver logiku u leave_list ruti.
Pokretanje: cd ~/Projects/Softman_app && python patch_leave_manager.py
"""
import shutil, os

BASE   = os.path.expanduser('~/Projects/Softman_app')
APP_PY = os.path.join(BASE, 'app.py')

def backup(p):
    shutil.copy2(p, p + '.bak3')
    print(f'  Backup: {p}.bak3')

OLD_LEAVE_LIST = '''@app.route('/leave')
@login_required
def leave_list():
    user = get_current_user()
    conn = get_db()
    current_year = datetime.now().year

    years_raw = conn.execute(
        "SELECT DISTINCT substr(date_from,1,4) as yr FROM leave_requests ORDER BY yr DESC"
    ).fetchall()
    years = [r['yr'] for r in years_raw] or [str(current_year)]
    if str(current_year) not in years:
        years.insert(0, str(current_year))

    employees = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()

    if user.get('is_admin') or user.get('can_approve_leave'):
        requests = conn.execute("""
            SELECT lr.*, e.name as employee_name,
                   approver.name as approved_by_name
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            LEFT JOIN employees approver ON approver.id = lr.approved_by_id
            ORDER BY lr.date_from DESC
        """).fetchall()
    else:
        urow = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
        emp_id = urow['employee_id'] if urow and urow['employee_id'] else 0
        requests = conn.execute("""
            SELECT lr.*, e.name as employee_name,
                   approver.name as approved_by_name
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            LEFT JOIN employees approver ON approver.id = lr.approved_by_id
            WHERE lr.employee_id = ?
            ORDER BY lr.date_from DESC
        """, (emp_id,)).fetchall()

    employee_quotas = []
    if user.get('is_admin') or user.get('can_approve_leave'):
        for e in employees:
            if not e['annual_leave_days']:
                continue
            used = conn.execute("""
                SELECT COALESCE(SUM(days),0) as s FROM leave_requests
                WHERE employee_id=? AND status IN ('approved','used')
                AND substr(date_from,1,4)=?
            """, (e['id'], str(current_year))).fetchone()['s']
            employee_quotas.append({
                'id': e['id'], 'name': e['name'], 'position': e['position'],
                'total_days': e['annual_leave_days'],
                'used': int(used),
                'remaining': max(0, e['annual_leave_days'] - int(used))
            })

    my_quota = None
    current_employee_id = None
    if not (user.get('is_admin') or user.get('can_approve_leave')):
        urow = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
        if urow and urow['employee_id']:
            current_employee_id = urow['employee_id']
            erow = conn.execute("SELECT * FROM employees WHERE id=?", (current_employee_id,)).fetchone()
            if erow and erow['annual_leave_days']:
                used = conn.execute("""
                    SELECT COALESCE(SUM(days),0) as s FROM leave_requests
                    WHERE employee_id=? AND status IN ('approved','used')
                    AND substr(date_from,1,4)=?
                """, (current_employee_id, str(current_year))).fetchone()['s']
                my_quota = {
                    'total_days': erow['annual_leave_days'],
                    'used': int(used),
                    'remaining': max(0, erow['annual_leave_days'] - int(used))
                }

    all_holidays = ALL_HOLIDAYS
    conn.close()
    return render_template('leave_list.html',
        active='leave', user=user,
        requests=rows_to_dicts(requests),
        employees=rows_to_dicts(employees),
        employee_quotas=employee_quotas,
        my_quota=my_quota,
        current_employee_id=current_employee_id,
        years=years,
        current_year=current_year,
        holidays_json=all_holidays,
    )'''

NEW_LEAVE_LIST = '''@app.route('/leave')
@login_required
def leave_list():
    user = get_current_user()
    conn = get_db()
    current_year = datetime.now().year

    years_raw = conn.execute(
        "SELECT DISTINCT substr(date_from,1,4) as yr FROM leave_requests ORDER BY yr DESC"
    ).fetchall()
    years = [r['yr'] for r in years_raw] or [str(current_year)]
    if str(current_year) not in years:
        years.insert(0, str(current_year))

    employees = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()

    # Dohvati current_employee_id za sve korisnike
    urow = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
    current_employee_id = urow['employee_id'] if urow and urow['employee_id'] else None

    # Provjeri je li korisnik voditelj nekome (manager_id == current_employee_id)
    is_manager = False
    managed_employee_ids = []
    if current_employee_id:
        managed = conn.execute(
            "SELECT id FROM employees WHERE manager_id=?", (current_employee_id,)
        ).fetchall()
        managed_employee_ids = [r['id'] for r in managed]
        # Voditelj je i sam sebi voditelj, ili ima podređene
        is_manager = len(managed_employee_ids) > 0

    # Tko smije odobravati: admin, can_approve_leave profil, ili voditelj
    is_approver = user.get('is_admin') or user.get('can_approve_leave') or is_manager

    if user.get('is_admin') or user.get('can_approve_leave'):
        # Admin i profile approver vide SVE
        requests = conn.execute("""
            SELECT lr.*, e.name as employee_name,
                   approver.name as approved_by_name
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            LEFT JOIN employees approver ON approver.id = lr.approved_by_id
            ORDER BY lr.date_from DESC
        """).fetchall()
    elif is_manager:
        # Voditelj vidi svoje i zahtjeve svojih podređenih
        visible_ids = list(set(managed_employee_ids + ([current_employee_id] if current_employee_id else [])))
        placeholders = ','.join('?' for _ in visible_ids)
        requests = conn.execute(f"""
            SELECT lr.*, e.name as employee_name,
                   approver.name as approved_by_name
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            LEFT JOIN employees approver ON approver.id = lr.approved_by_id
            WHERE lr.employee_id IN ({placeholders})
            ORDER BY lr.date_from DESC
        """, visible_ids).fetchall()
    else:
        # Obični zaposlenik — samo svoje
        emp_id = current_employee_id or 0
        requests = conn.execute("""
            SELECT lr.*, e.name as employee_name,
                   approver.name as approved_by_name
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            LEFT JOIN employees approver ON approver.id = lr.approved_by_id
            WHERE lr.employee_id = ?
            ORDER BY lr.date_from DESC
        """, (emp_id,)).fetchall()

    # Kvote — za approvere prikaži sve zaposlenike s definiranim godišnjim
    employee_quotas = []
    if is_approver:
        quota_employees = employees if (user.get('is_admin') or user.get('can_approve_leave')) else \
            [e for e in employees if e['id'] in (managed_employee_ids + ([current_employee_id] if current_employee_id else []))]
        for e in quota_employees:
            if not e['annual_leave_days']:
                continue
            used = conn.execute("""
                SELECT COALESCE(SUM(days),0) as s FROM leave_requests
                WHERE employee_id=? AND status IN ('approved','used')
                AND substr(date_from,1,4)=?
            """, (e['id'], str(current_year))).fetchone()['s']
            employee_quotas.append({
                'id': e['id'], 'name': e['name'], 'position': e['position'],
                'total_days': e['annual_leave_days'],
                'used': int(used),
                'remaining': max(0, e['annual_leave_days'] - int(used))
            })

    # Moja kvota (uvijek prikaži i zaposleniku)
    my_quota = None
    if current_employee_id:
        erow = conn.execute("SELECT * FROM employees WHERE id=?", (current_employee_id,)).fetchone()
        if erow and erow['annual_leave_days']:
            used = conn.execute("""
                SELECT COALESCE(SUM(days),0) as s FROM leave_requests
                WHERE employee_id=? AND status IN ('approved','used')
                AND substr(date_from,1,4)=?
            """, (current_employee_id, str(current_year))).fetchone()['s']
            my_quota = {
                'total_days': erow['annual_leave_days'],
                'used': int(used),
                'remaining': max(0, erow['annual_leave_days'] - int(used))
            }

    all_holidays = ALL_HOLIDAYS
    conn.close()
    return render_template('leave_list.html',
        active='leave', user=user,
        requests=rows_to_dicts(requests),
        employees=rows_to_dicts(employees),
        employee_quotas=employee_quotas,
        my_quota=my_quota,
        current_employee_id=current_employee_id,
        is_approver=is_approver,
        is_manager=is_manager,
        years=years,
        current_year=current_year,
        holidays_json=all_holidays,
    )'''

def patch():
    with open(APP_PY, 'r', encoding='utf-8') as f:
        c = f.read()

    if OLD_LEAVE_LIST in c:
        c = c.replace(OLD_LEAVE_LIST, NEW_LEAVE_LIST, 1)
        print('✅ leave_list ruta ažurirana')
    else:
        print('❌ Nije pronađen stari leave_list — provjeri je li patch_leave_module.py već pokrenut.')
        return False

    # Također popravi leave_status rutu da voditelj može odobravati
    OLD_STATUS_CHECK = '''    if new_status in ('approved', 'rejected'):
        if not (user.get('is_admin') or user.get('can_approve_leave')):
            conn.close()
            return jsonify({'error': 'Nemate pravo odobravanja'}), 403'''

    NEW_STATUS_CHECK = '''    if new_status in ('approved', 'rejected'):
        # Provjeri je li voditelj podređenog zaposlenika
        urow2 = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
        cur_emp_id = urow2['employee_id'] if urow2 else None
        is_mgr = cur_emp_id and conn.execute(
            "SELECT id FROM employees WHERE id=? AND manager_id=?",
            (req['employee_id'], cur_emp_id)
        ).fetchone() is not None
        # Voditelj je i sam sebi voditelj
        is_self_mgr = cur_emp_id and conn.execute(
            "SELECT id FROM employees WHERE id=? AND manager_id=?",
            (cur_emp_id, cur_emp_id)
        ).fetchone() is not None
        if not (user.get('is_admin') or user.get('can_approve_leave') or is_mgr or is_self_mgr):
            conn.close()
            return jsonify({'error': 'Nemate pravo odobravanja'}), 403'''

    if OLD_STATUS_CHECK in c:
        c = c.replace(OLD_STATUS_CHECK, NEW_STATUS_CHECK, 1)
        print('✅ leave_status provjera ažurirana (voditelj može odobravati)')
    else:
        print('⚠️  leave_status anchor nije pronađen — možda već patchiran')

    with open(APP_PY, 'w', encoding='utf-8') as f:
        f.write(c)
    return True

if __name__ == '__main__':
    print('=== PATCH: Leave manager odobrava ===\n')
    backup(APP_PY)
    ok = patch()
    if ok:
        print('\n✅ Gotovo! Restart: python app.py')
    else:
        print('\n❌ Patch nije uspio.')
