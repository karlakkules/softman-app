#!/usr/bin/env python3
"""
patch_leave_module.py
Dodaje modul Godišnji odmori:
  1. app.py       — DB migracije, Flask rute, API
  2. base.html    — nav stavka
  3. settings.html — annual_leave_days, can_approve_leave u profilima
  4. worktime_form.html — banner o godišnjem u tom mjesecu
  5. Kopira leave_list.html u templates/
Pokretanje: cd ~/Projects/Softman_app && python patch_leave_module.py
"""
import shutil, os, sys

BASE       = os.path.expanduser('~/Projects/Softman_app')
APP_PY     = os.path.join(BASE, 'app.py')
BASE_HTML  = os.path.join(BASE, 'templates', 'base.html')
SETTINGS   = os.path.join(BASE, 'templates', 'settings.html')
WT_FORM    = os.path.join(BASE, 'templates', 'worktime_form.html')
LEAVE_HTML = os.path.join(BASE, 'templates', 'leave_list.html')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def backup(p):
    shutil.copy2(p, p + '.bak')
    print(f'  Backup: {p}.bak')

# ════════════════════════════════════════════════════════════════
# 1. KOPIRAJ TEMPLATE
# ════════════════════════════════════════════════════════════════
def copy_template():
    src = os.path.join(SCRIPT_DIR, 'leave_list.html')
    if not os.path.exists(src):
        print('❌ leave_list.html nije pronađen pored skripte!')
        return False
    shutil.copy2(src, LEAVE_HTML)
    print('✅ leave_list.html kopiran u templates/')
    return True

# ════════════════════════════════════════════════════════════════
# 2. APP.PY
# ════════════════════════════════════════════════════════════════
LEAVE_ROUTES = '''
# ─── GODIŠNJI ODMORI ─────────────────────────────────────────────────────────

@app.route('/leave')
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

    all_holidays = getattr(sys.modules[__name__], 'ALL_HOLIDAYS', {})
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
    )


@app.route('/api/leave', methods=['POST'])
@login_required
def leave_save():
    data = request.json
    user = get_current_user()
    conn = get_db()
    emp_id = data.get('employee_id')
    if not (user.get('is_admin') or user.get('can_approve_leave')):
        urow = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
        if not urow or urow['employee_id'] != emp_id:
            conn.close()
            return jsonify({'error': 'Nemate pravo predati zahtjev za drugog zaposlenika'}), 403
    req_id = data.get('id')
    fields = {
        'employee_id': emp_id,
        'date_from': data.get('date_from'),
        'date_to': data.get('date_to'),
        'days': data.get('days', 0),
        'notes': data.get('notes') or None,
        'status': data.get('status', 'submitted'),
        'updated_at': datetime.now().isoformat(),
    }
    if req_id:
        sets = ', '.join(f"{k}=?" for k in fields)
        conn.execute(f"UPDATE leave_requests SET {sets} WHERE id=?", list(fields.values()) + [req_id])
    else:
        fields['created_at'] = datetime.now().isoformat()
        fields['created_by'] = user.get('user_id')
        cols = ', '.join(fields.keys())
        placeholders = ', '.join('?' for _ in fields)
        conn.execute(f"INSERT INTO leave_requests ({cols}) VALUES ({placeholders})", list(fields.values()))
    conn.commit()
    conn.close()
    audit('save', module='leave', detail=f"Zahtjev {req_id or 'novi'} status={fields['status']}")
    return jsonify({'success': True})


@app.route('/api/leave/<int:req_id>/status', methods=['POST'])
@login_required
def leave_status(req_id):
    data = request.json
    new_status = data.get('status')
    user = get_current_user()
    conn = get_db()
    req = conn.execute("SELECT * FROM leave_requests WHERE id=?", (req_id,)).fetchone()
    if not req:
        conn.close()
        return jsonify({'error': 'Nije pronađeno'}), 404
    if new_status in ('approved', 'rejected'):
        if not (user.get('is_admin') or user.get('can_approve_leave')):
            conn.close()
            return jsonify({'error': 'Nemate pravo odobravanja'}), 403
        urow = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
        approver_emp_id = urow['employee_id'] if urow else None
        conn.execute(
            "UPDATE leave_requests SET status=?, approved_by_id=?, updated_at=? WHERE id=?",
            (new_status, approver_emp_id, datetime.now().isoformat(), req_id)
        )
    elif new_status == 'used':
        urow = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
        is_own = urow and urow['employee_id'] == req['employee_id']
        if not (user.get('is_admin') or is_own):
            conn.close()
            return jsonify({'error': 'Nemate pravo potvrde iskorištenja'}), 403
        conn.execute(
            "UPDATE leave_requests SET status='used', updated_at=? WHERE id=?",
            (datetime.now().isoformat(), req_id)
        )
    else:
        conn.close()
        return jsonify({'error': 'Nevažeći status'}), 400
    conn.commit()
    conn.close()
    audit('status_change', module='leave', entity_id=req_id, detail=f'Status -> {new_status}')
    return jsonify({'success': True})


@app.route('/api/leave/<int:req_id>', methods=['DELETE'])
@login_required
def leave_delete(req_id):
    user = get_current_user()
    conn = get_db()
    req = conn.execute("SELECT * FROM leave_requests WHERE id=?", (req_id,)).fetchone()
    if not req:
        conn.close()
        return jsonify({'error': 'Nije pronađeno'}), 404
    if req['status'] != 'draft':
        conn.close()
        return jsonify({'error': 'Može se brisati samo nacrt'}), 400
    urow = conn.execute("SELECT employee_id FROM users WHERE id=?", (user['user_id'],)).fetchone()
    is_own = urow and urow['employee_id'] == req['employee_id']
    if not (user.get('is_admin') or is_own):
        conn.close()
        return jsonify({'error': 'Nemate pravo brisanja'}), 403
    conn.execute("DELETE FROM leave_requests WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/leave/by-employee/<int:emp_id>')
@login_required
def leave_by_employee(emp_id):
    """Godišnji odmori za zaposleni u određenom mjesecu — za worktime formu"""
    year  = request.args.get('year',  type=int)
    month = request.args.get('month', type=int)
    conn  = get_db()
    if year and month:
        month_start = f"{year:04d}-{month:02d}-01"
        month_end   = f"{year:04d}-{month:02d}-31"
        reqs = conn.execute("""
            SELECT date_from, date_to, days, status FROM leave_requests
            WHERE employee_id=? AND status IN ('approved','used')
              AND date_from <= ? AND date_to >= ?
            ORDER BY date_from
        """, (emp_id, month_end, month_start)).fetchall()
    else:
        reqs = []
    conn.close()
    return jsonify([dict(r) for r in reqs])

'''

def patch_app():
    with open(APP_PY, 'r', encoding='utf-8') as f:
        c = f.read()

    # A. DB migracije
    DB_MIG = """    # Godisnji odmori
    try:
        c.execute("ALTER TABLE employees ADD COLUMN annual_leave_days INTEGER DEFAULT 0")
    except: pass
    try:
        c.executescript(\"\"\"
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date_from TEXT NOT NULL,
                date_to TEXT NOT NULL,
                days INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                status TEXT DEFAULT 'submitted',
                approved_by_id INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
        \"\"\")
    except: pass
    try:
        c.execute("ALTER TABLE profiles ADD COLUMN can_approve_leave INTEGER DEFAULT 0")
    except: pass
"""
    MANCOR = '    conn.commit()\n    conn.close()\n\ndef audit('
    if 'leave_requests' in c:
        print('  [app.py] DB migracije vec postoje.')
    elif MANCOR in c:
        c = c.replace(MANCOR, DB_MIG + MANCOR, 1)
        print('  [app.py] ✅ DB migracije dodane')
    else:
        print('  [app.py] ❌ Nije pronađen anchor za DB migracije!')

    # B. can_approve_leave u MINIMAL_PERMS
    OLD_P = "    'can_view_loans': 0, 'can_edit_loans': 0, 'can_lock_loans': 0,"
    NEW_P = "    'can_view_loans': 0, 'can_edit_loans': 0, 'can_lock_loans': 0,\n    'can_approve_leave': 0,"
    if 'can_approve_leave' in c:
        print('  [app.py] can_approve_leave vec postoji.')
    elif OLD_P in c:
        c = c.replace(OLD_P, NEW_P, 1)
        print('  [app.py] ✅ can_approve_leave dodan u MINIMAL_PERMS')
    else:
        print('  [app.py] ❌ Nije pronađen MINIMAL_PERMS anchor!')

    # C. Leave rute
    if '/api/leave' in c:
        print('  [app.py] Leave rute vec postoje.')
    else:
        ANCHOR_MAIN = "if __name__ == '__main__':"
        if ANCHOR_MAIN in c:
            c = c.replace(ANCHOR_MAIN, LEAVE_ROUTES + ANCHOR_MAIN, 1)
        else:
            c += LEAVE_ROUTES
        print('  [app.py] ✅ Leave rute dodane')

    with open(APP_PY, 'w', encoding='utf-8') as f:
        f.write(c)

# ════════════════════════════════════════════════════════════════
# 3. BASE.HTML
# ════════════════════════════════════════════════════════════════
def patch_base():
    with open(BASE_HTML, 'r', encoding='utf-8') as f:
        c = f.read()
    if '/leave' in c:
        print('  [base.html] Nav stavka vec postoji.')
        return
    NAV_NEW = '\n        <a href="/leave" class="nav-item {% if active == \'leave\' %}active{% endif %}">\n          <span class="icon">🏖️</span> Godišnji odmori\n        </a>'
    # Pokušaj iza worktime
    OLD1 = '<a href="/worktime" class="nav-item {% if active == \'worktime\' %}active{% endif %}">\n          <span class="icon">⏱️</span> Radno vrijeme\n        </a>'
    if OLD1 in c:
        c = c.replace(OLD1, OLD1 + NAV_NEW, 1)
        print('  [base.html] ✅ Nav stavka dodana iza worktime')
    else:
        # Fallback: iza loans
        OLD2 = "href=\"/loans\""
        idx = c.rfind(OLD2)
        if idx > 0:
            end = c.find('</a>', idx) + 4
            c = c[:end] + NAV_NEW + c[end:]
            print('  [base.html] ✅ Nav stavka dodana iza loans (fallback)')
        else:
            print('  [base.html] ❌ Nije pronađen anchor za navigaciju!')
    with open(BASE_HTML, 'w', encoding='utf-8') as f:
        f.write(c)

# ════════════════════════════════════════════════════════════════
# 4. SETTINGS.HTML
# ════════════════════════════════════════════════════════════════
def patch_settings():
    with open(SETTINGS, 'r', encoding='utf-8') as f:
        c = f.read()

    # A. annual_leave_days polje u employee modalu
    if 'annual_leave_days' in c:
        print('  [settings.html] annual_leave_days vec postoji.')
    else:
        OLD = '        <div class="form-group">\n          <label class="form-label">Ugovor o radu vrijedi do</label>'
        NEW = '''        <div class="form-group">
          <label class="form-label">Godišnji odmor (dana/god)</label>
          <input type="number" class="form-control" id="emp-annual-leave" min="0" max="60" placeholder="npr. 22" style="width:130px;">
          <div style="font-size:11px;color:var(--gray-400);margin-top:3px;">Dogovoreni broj dana godišnjeg odmora u godini</div>
        </div>
        <div class="form-group">
          <label class="form-label">Ugovor o radu vrijedi do</label>'''
        if OLD in c:
            c = c.replace(OLD, NEW, 1)
            print('  [settings.html] ✅ annual_leave_days polje dodano')
        else:
            print('  [settings.html] ❌ Nije pronađen anchor za annual_leave_days!')

    # B. can_approve_leave u PERM_LABELS (jednolinijski format)
    OLD_LABELS = "can_lock_loans: 'Pozajmice \u2014 zaklju\u010davanje plana otplate',\n};"
    NEW_LABELS = "can_lock_loans: 'Pozajmice \u2014 zaklju\u010davanje plana otplate',\n  can_approve_leave: 'Godi\u0161nji odmori \u2014 odobravanje',\n};"
    if 'can_approve_leave' in c:
        print('  [settings.html] can_approve_leave vec postoji u PERM_LABELS.')
    elif OLD_LABELS in c:
        c = c.replace(OLD_LABELS, NEW_LABELS, 1)
        print('  [settings.html] ✅ can_approve_leave dodan u PERM_LABELS')
    else:
        # Fallback s ASCII crticom
        OLD_LABELS2 = "can_lock_loans: 'Pozajmice"
        idx = c.find(OLD_LABELS2)
        if idx > 0:
            end = c.find('\n};', idx) + 3
            insert = "  can_approve_leave: 'Godišnji odmori — odobravanje',\n"
            c = c[:end-3] + '\n' + insert + c[end-3:]
            print('  [settings.html] ✅ can_approve_leave dodan (fallback)')
        else:
            print('  [settings.html] ❌ Nije pronađen PERM_LABELS anchor!')

    # C. can_approve_leave u PERM_GROUPS
    OLD_GROUP = "{ label: 'Pozajmice', perms: ['can_view_loans','can_edit_loans','can_lock_loans'] },"
    NEW_GROUP = "{ label: 'Pozajmice', perms: ['can_view_loans','can_edit_loans','can_lock_loans'] },\n  { label: 'Godišnji odmori', perms: ['can_approve_leave'] },"
    if 'can_approve_leave' in c and 'Godišnji odmori' in c:
        print('  [settings.html] PERM_GROUPS vec ima godisnji.')
    elif OLD_GROUP in c:
        c = c.replace(OLD_GROUP, NEW_GROUP, 1)
        print('  [settings.html] ✅ PERM_GROUPS ažuriran')
    else:
        print('  [settings.html] ❌ Nije pronađen PERM_GROUPS anchor!')

    # D. can_approve_leave u PERM_SHORT
    OLD_SHORT = "can_lock_loans: 'Zaključavanje',\n};"
    NEW_SHORT = "can_lock_loans: 'Zaklju\u010davanje',\n  can_approve_leave: 'Odobravanje godi\u0161njih',\n};"
    if 'Odobravanje godišnjih' in c:
        print('  [settings.html] PERM_SHORT vec ima godisnji.')
    elif OLD_SHORT in c:
        c = c.replace(OLD_SHORT, NEW_SHORT, 1)
        print('  [settings.html] ✅ PERM_SHORT ažuriran')
    else:
        print('  [settings.html] ⚠️  PERM_SHORT anchor nije pronađen — nije kritično')

    # E. openModal JS reset — dodaj emp-annual-leave
    OLD_RST = "['emp-phone','emp-email','emp-street','emp-city','emp-country','emp-oib','emp-contract-until'].forEach"
    NEW_RST = "['emp-phone','emp-email','emp-street','emp-city','emp-country','emp-oib','emp-contract-until','emp-annual-leave'].forEach"
    if 'emp-annual-leave' in c:
        print('  [settings.html] emp-annual-leave reset vec postoji.')
    elif OLD_RST in c:
        c = c.replace(OLD_RST, NEW_RST, 1)
        print('  [settings.html] ✅ openModal reset ažuriran')
    else:
        print('  [settings.html] ❌ Nije pronađen openModal reset anchor!')

    # F. editEmployee JS — popuni annual_leave_days
    OLD_SET = "  setVal('emp-contract-until', emp.contract_until);"
    NEW_SET = "  setVal('emp-contract-until', emp.contract_until);\n  setVal('emp-annual-leave', emp.annual_leave_days);"
    if 'emp-annual-leave' in c and 'setVal' in c:
        print('  [settings.html] editEmployee annual_leave vec postoji.')
    elif OLD_SET in c:
        c = c.replace(OLD_SET, NEW_SET, 1)
        print('  [settings.html] ✅ editEmployee ažuriran')
    else:
        print('  [settings.html] ❌ Nije pronađen editEmployee anchor!')

    # G. saveEmployee JS — pošalji annual_leave_days
    OLD_SAV = "    contract_indefinite: document.getElementById('emp-contract-indefinite')?.checked ? 1 : 0,"
    NEW_SAV = "    contract_indefinite: document.getElementById('emp-contract-indefinite')?.checked ? 1 : 0,\n    annual_leave_days: (() => { const v = document.getElementById('emp-annual-leave')?.value; return v ? parseInt(v) : 0; })(),"
    if 'annual_leave_days' in c and 'saveEmployee' in c:
        print('  [settings.html] saveEmployee annual_leave_days vec postoji.')
    elif OLD_SAV in c:
        c = c.replace(OLD_SAV, NEW_SAV, 1)
        print('  [settings.html] ✅ saveEmployee ažuriran')
    else:
        print('  [settings.html] ❌ Nije pronađen saveEmployee anchor!')

    with open(SETTINGS, 'w', encoding='utf-8') as f:
        f.write(c)

# ════════════════════════════════════════════════════════════════
# 5. WORKTIME_FORM.HTML
# ════════════════════════════════════════════════════════════════
LEAVE_JS = """
// ── Godišnji odmori u ovom mjesecu ────────────────────────────────────────────
async function loadLeaveForMonth() {
  const empId = document.getElementById('wt-employee')?.value;
  const year  = document.getElementById('wt-year')?.value;
  const month = document.getElementById('wt-month')?.value;
  const banner  = document.getElementById('leave-banner');
  const content = document.getElementById('leave-banner-content');
  if (!empId || !year || !month || !banner || !content) return;
  try {
    const res = await fetch(`/api/leave/by-employee/${empId}?year=${year}&month=${month}`);
    const leaves = await res.json();
    if (!leaves.length) { banner.style.display = 'none'; return; }
    const fmtDate = d => d ? d.split('-').reverse().join('.') + '.' : '';
    content.innerHTML = leaves.map(l =>
      `<span style="display:inline-block;background:white;border:1px solid #a8d5b5;border-radius:20px;padding:2px 12px;margin:2px 0;font-size:12px;">
        ${fmtDate(l.date_from)} – ${fmtDate(l.date_to)}
        <strong>(${l.days} ${l.days === 1 ? 'dan' : 'dana'})</strong>
        <span style="font-size:10px;color:#27ae60;margin-left:4px;">${l.status === 'used' ? '✅ iskorišteno' : '✓ odobreno'}</span>
      </span>`
    ).join('');
    banner.style.display = 'block';
  } catch(e) { console.warn('Leave banner error:', e); }
}

"""

LEAVE_BANNER_HTML = """<!-- Godišnji odmori u ovom mjesecu -->
<div id="leave-banner" style="display:none;background:#e6f5ef;border:1px solid #a8d5b5;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
  <div style="font-weight:600;color:#1a8a5a;font-size:13px;margin-bottom:6px;">🏖️ Godišnji odmor u ovom mjesecu:</div>
  <div id="leave-banner-content" style="line-height:1.8;"></div>
</div>

"""

def patch_worktime():
    with open(WT_FORM, 'r', encoding='utf-8') as f:
        c = f.read()

    if 'leave-banner' in c:
        print('  [worktime_form.html] Leave banner vec postoji.')
        return

    # Dodaj HTML banner ispred <!-- Grid -->
    if '<!-- Grid -->' in c:
        c = c.replace('<!-- Grid -->', LEAVE_BANNER_HTML + '<!-- Grid -->', 1)
        print('  [worktime_form.html] ✅ Leave banner HTML dodan')
    else:
        print('  [worktime_form.html] ❌ Nije pronađen <!-- Grid --> anchor!')

    # Dodaj JS + poziv u DOMContentLoaded
    OLD_DOM = "document.addEventListener('DOMContentLoaded', () => {\n  buildGrid();\n  if (IS_NEW) autoFillGrid();\n});"
    NEW_DOM = LEAVE_JS + "document.addEventListener('DOMContentLoaded', () => {\n  buildGrid();\n  if (IS_NEW) autoFillGrid();\n  loadLeaveForMonth();\n});"
    if OLD_DOM in c:
        c = c.replace(OLD_DOM, NEW_DOM, 1)
        print('  [worktime_form.html] ✅ JS dodan')
    else:
        print('  [worktime_form.html] ❌ Nije pronađen DOMContentLoaded anchor!')

    # Dodaj loadLeaveForMonth() u reloadGrid
    OLD_RLD = 'function reloadGrid() {\n  if (IS_NEW) grid = {};\n  buildGrid();\n  if (IS_NEW) autoFillGrid();\n}'
    NEW_RLD = 'function reloadGrid() {\n  if (IS_NEW) grid = {};\n  buildGrid();\n  if (IS_NEW) autoFillGrid();\n  loadLeaveForMonth();\n}'
    if OLD_RLD in c:
        c = c.replace(OLD_RLD, NEW_RLD, 1)
        print('  [worktime_form.html] ✅ reloadGrid ažuriran')
    else:
        print('  [worktime_form.html] ⚠️  reloadGrid anchor nije točan — nije kritično')

    # Trigger na promjenu zaposlenika
    OLD_EMP = '<select class="form-control" id="wt-employee" {% if locked %}disabled{% endif %}>'
    NEW_EMP = '<select class="form-control" id="wt-employee" {% if locked %}disabled{% endif %} onchange="loadLeaveForMonth()">'
    if OLD_EMP in c:
        c = c.replace(OLD_EMP, NEW_EMP, 1)
        print('  [worktime_form.html] ✅ onchange dodan na wt-employee')
    else:
        print('  [worktime_form.html] ⚠️  wt-employee select anchor nije pronađen')

    with open(WT_FORM, 'w', encoding='utf-8') as f:
        f.write(c)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('=== PATCH: Modul Godišnji odmori ===\n')

    # Provjeri da smo u pravom direktoriju
    if not os.path.exists(APP_PY):
        print(f'❌ Nije pronađen app.py na: {APP_PY}')
        print('Pokreni skriptu iz ~/Projects/Softman_app direktorija ili provjeri putanju.')
        sys.exit(1)

    print('1. Backupi...')
    for p in [APP_PY, BASE_HTML, SETTINGS, WT_FORM]:
        if os.path.exists(p):
            backup(p)

    print('\n2. Kopiraj leave_list.html template...')
    if not copy_template():
        sys.exit(1)

    print('\n3. Patch app.py (DB + rute)...')
    patch_app()

    print('\n4. Patch base.html (navigacija)...')
    patch_base()

    print('\n5. Patch settings.html (annual_leave_days + profili)...')
    patch_settings()

    print('\n6. Patch worktime_form.html (leave banner)...')
    patch_worktime()

    print('\n=== ✅ GOTOVO! ===')
    print('\nPokreni aplikaciju: python app.py')
    print('\nNa kraju sesije:')
    print('cd ~/Projects/Softman_app && git add . && git commit -m "feat: modul Godisnji odmori" && git push origin main')
