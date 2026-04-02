#!/usr/bin/env python3
"""
patch_employee_manager.py
- Dodaje manager_id kolonu u employees tablicu (DB migracija u init_db)
- Dodaje dropdown "Voditelj" u employee modal settings.html
- Popravlja CSS grid za uloge u sustavu (poravnanje u stupce, ne cik-cak)
- Ažurira JS: openModal, editEmployee, saveEmployee da uključuju manager_id
- Ažurira tablicu zaposlenika da prikazuje voditelja
"""

import shutil
import os

BASE = os.path.expanduser('~/Projects/Softman_app')
APP_PY = os.path.join(BASE, 'app.py')
SETTINGS_HTML = os.path.join(BASE, 'templates', 'settings.html')

def backup(path):
    bak = path + '.bak'
    shutil.copy2(path, bak)
    print(f'  Backup: {bak}')

def patch_app_py():
    with open(APP_PY, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Dodaj migraciju za manager_id u init_db
    OLD = '    try:\n        c.execute("ALTER TABLE vehicles ADD COLUMN home_city TEXT DEFAULT NULL")\n    except: pass'
    NEW = '    try:\n        c.execute("ALTER TABLE vehicles ADD COLUMN home_city TEXT DEFAULT NULL")\n    except: pass\n    try:\n        c.execute("ALTER TABLE employees ADD COLUMN manager_id INTEGER DEFAULT NULL")\n    except: pass'

    if 'ALTER TABLE employees ADD COLUMN manager_id' in content:
        print('  [app.py] manager_id migracija vec postoji.')
    elif OLD in content:
        content = content.replace(OLD, NEW, 1)
        print('  [app.py] Dodan ALTER TABLE employees ADD COLUMN manager_id.')
    else:
        print('  [app.py] UPOZORENJE: Trazim fallback anchor...')
        # Fallback: dodaj prije zadnjeg conn.commit() + conn.close() u init_db
        OLD2 = '    conn.commit()\n    conn.close()\n\ndef audit('
        NEW2 = '    try:\n        c.execute("ALTER TABLE employees ADD COLUMN manager_id INTEGER DEFAULT NULL")\n    except: pass\n    conn.commit()\n    conn.close()\n\ndef audit('
        if OLD2 in content:
            content = content.replace(OLD2, NEW2, 1)
            print('  [app.py] Dodan manager_id fallback.')
        else:
            print('  [app.py] GREŠKA: nije moguce dodati migraciju!')

    # 2. Ažuriraj list_employees da vraća i manager_name
    OLD_LIST = '@app.route(\'/api/employees\', methods=[\'GET\'])\n@admin_required\ndef list_employees():\n    conn = get_db()\n    items = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()\n    conn.close()\n    return jsonify([dict(i) for i in items])'
    NEW_LIST = '@app.route(\'/api/employees\', methods=[\'GET\'])\n@admin_required\ndef list_employees():\n    conn = get_db()\n    items = conn.execute("""\n        SELECT e.*, m.name as manager_name\n        FROM employees e\n        LEFT JOIN employees m ON m.id = e.manager_id\n        ORDER BY e.name\n    """).fetchall()\n    conn.close()\n    return jsonify([dict(i) for i in items])'

    if 'manager_name' in content and 'list_employees' in content:
        print('  [app.py] list_employees vec vraca manager_name.')
    elif 'def list_employees' in content and 'SELECT * FROM employees ORDER BY name' in content:
        content = content.replace(
            '    items = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()',
            '    items = conn.execute("""\n        SELECT e.*, m.name as manager_name\n        FROM employees e\n        LEFT JOIN employees m ON m.id = e.manager_id\n        ORDER BY e.name\n    """).fetchall()',
            1
        )
        print('  [app.py] Azuriran list_employees da vraca manager_name.')
    else:
        print('  [app.py] UPOZORENJE: Nije pronaden list_employees!')

    with open(APP_PY, 'w', encoding='utf-8') as f:
        f.write(content)
    print('  [app.py] Zapisano.')


def patch_settings_html():
    with open(SETTINGS_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    # PATCH 1: Stupac Voditelj u headeru tablice
    OLD_TH = '            <th data-hr="Radno mjesto" data-en="Position">Radno mjesto</th>\n            <th data-hr="Potpis" data-en="Signature">Potpis</th>'
    NEW_TH = '            <th data-hr="Radno mjesto" data-en="Position">Radno mjesto</th>\n            <th data-hr="Voditelj" data-en="Manager">Voditelj</th>\n            <th data-hr="Potpis" data-en="Signature">Potpis</th>'

    if 'data-hr="Voditelj"' in content:
        print('  [settings.html] Stupac Voditelj vec postoji.')
    elif OLD_TH in content:
        content = content.replace(OLD_TH, NEW_TH, 1)
        print('  [settings.html] Dodan stupac Voditelj u tablicu.')
    else:
        print('  [settings.html] UPOZORENJE: Nije pronaden header tablice!')

    # PATCH 2: Prikaz voditelja u retku tablice
    OLD_TR_CELL = "            <td>{{ e.position or '—' }}</td>\n            <td>"
    NEW_TR_CELL = "            <td>{{ e.position or '—' }}</td>\n            <td>\n              {% set mgr = employees | selectattr('id', 'equalto', e.manager_id) | list %}\n              {% if mgr %}<span style=\"font-size:12px;\">{{ mgr[0].name }}</span>{% else %}<span style=\"color:var(--gray-300);\">—</span>{% endif %}\n            </td>\n            <td>"

    if 'selectattr' in content and 'mgr' in content:
        print('  [settings.html] Prikaz voditelja u retku vec postoji.')
    elif OLD_TR_CELL in content:
        content = content.replace(OLD_TR_CELL, NEW_TR_CELL, 1)
        print('  [settings.html] Dodan prikaz voditelja u retke tablice.')
    else:
        print('  [settings.html] UPOZORENJE: Nije pronaden anchor za prikaz voditelja!')

    # PATCH 3: Employee modal - zamijeni cijeli roles block s novim (dodaj voditelja + popravi grid)
    OLD_ROLES = '''      <div style="background:var(--gray-50);border-radius:8px;padding:14px;margin-bottom:12px;">
        <div style="font-size:11px;font-weight:700;color:var(--gray-600);text-transform:uppercase;margin-bottom:10px;" data-hr="Uloge u sustavu" data-en="System roles">Uloge u sustavu</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
          <label class="checkbox-wrap"><input type="checkbox" id="emp-direktor"> <span data-hr="Direktor (odobrava nalog)" data-en="Director (approves)">Direktor</span></label>
          <label class="checkbox-wrap"><input type="checkbox" id="emp-validator"> <span data-hr="Validator" data-en="Validator">Validator</span></label>
          <label class="checkbox-wrap"><input type="checkbox" id="emp-blagajnik"> <span data-hr="Blagajnik/likvidator" data-en="Cashier/liquidator">Blagajnik/likvidator</span></label>
          <label class="checkbox-wrap"><input type="checkbox" id="emp-knjizio"> <span data-hr="Knjižio" data-en="Posted by">Knjižio</span></label>
          <label class="checkbox-wrap"><input type="checkbox" id="emp-default"> <span data-hr="Zadani zaposlenik" data-en="Default employee">Zadani zaposlenik</span></label>
        </div>
      </div>'''

    NEW_ROLES = '''      <div class="form-group">
        <label class="form-label" style="font-size:11px;font-weight:700;color:var(--navy);text-transform:uppercase;letter-spacing:0.5px;" data-hr="Voditelj" data-en="Manager">Voditelj</label>
        <select class="form-control" id="emp-manager">
          <option value="">— bez voditelja —</option>
          {% for e in employees %}
          <option value="{{ e.id }}">{{ e.name }}</option>
          {% endfor %}
        </select>
      </div>
      <div style="background:var(--gray-50);border-radius:8px;padding:14px;margin-bottom:12px;">
        <div style="font-size:11px;font-weight:700;color:var(--gray-600);text-transform:uppercase;margin-bottom:10px;" data-hr="Uloge u sustavu" data-en="System roles">Uloge u sustavu</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;">
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:5px 0;min-width:0;">
            <input type="checkbox" id="emp-direktor" style="width:15px;height:15px;flex-shrink:0;margin:0;">
            <span style="font-size:13px;line-height:1.3;" data-hr="Direktor (odobrava nalog)" data-en="Director (approves)">Direktor (odobrava nalog)</span>
          </label>
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:5px 0;min-width:0;">
            <input type="checkbox" id="emp-validator" style="width:15px;height:15px;flex-shrink:0;margin:0;">
            <span style="font-size:13px;line-height:1.3;" data-hr="Validator" data-en="Validator">Validator</span>
          </label>
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:5px 0;min-width:0;">
            <input type="checkbox" id="emp-blagajnik" style="width:15px;height:15px;flex-shrink:0;margin:0;">
            <span style="font-size:13px;line-height:1.3;" data-hr="Blagajnik/likvidator" data-en="Cashier/liquidator">Blagajnik/likvidator</span>
          </label>
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:5px 0;min-width:0;">
            <input type="checkbox" id="emp-knjizio" style="width:15px;height:15px;flex-shrink:0;margin:0;">
            <span style="font-size:13px;line-height:1.3;" data-hr="Knjižio" data-en="Posted by">Knjižio</span>
          </label>
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:5px 0;min-width:0;">
            <input type="checkbox" id="emp-default" style="width:15px;height:15px;flex-shrink:0;margin:0;">
            <span style="font-size:13px;line-height:1.3;" data-hr="Zadani zaposlenik" data-en="Default employee">Zadani zaposlenik</span>
          </label>
        </div>
      </div>'''

    if 'emp-manager' in content:
        print('  [settings.html] Employee modal roles block vec ima voditelja.')
    elif OLD_ROLES in content:
        content = content.replace(OLD_ROLES, NEW_ROLES, 1)
        print('  [settings.html] Zamijenjen roles block (dodani voditelj + popravljen grid).')
    else:
        print('  [settings.html] UPOZORENJE: Nije pronaden OLD_ROLES block! Provjeri rucno.')

    # PATCH 4: openModal JS - resetiraj manager
    OLD_OPEN = "    ['direktor','validator','blagajnik','knjizio','default'].forEach(r => document.getElementById(`emp-${r}`).checked = false);"
    NEW_OPEN = "    ['direktor','validator','blagajnik','knjizio','default'].forEach(r => document.getElementById(`emp-${r}`).checked = false);\n    const mgrSel = document.getElementById('emp-manager'); if (mgrSel) mgrSel.value = '';"

    if 'mgrSel' in content:
        print('  [settings.html] openModal JS vec ima manager reset.')
    elif OLD_OPEN in content:
        content = content.replace(OLD_OPEN, NEW_OPEN, 1)
        print('  [settings.html] Azuriran openModal JS.')
    else:
        print('  [settings.html] UPOZORENJE: Nije pronaden openModal anchor!')

    # PATCH 5: editEmployee JS - postavi manager_id
    OLD_EDIT = "  document.getElementById('emp-default').checked = !!emp.is_default;\n  document.getElementById('emp-modal-title').textContent = emp.name;"
    NEW_EDIT = "  document.getElementById('emp-default').checked = !!emp.is_default;\n  const mgrDropdown = document.getElementById('emp-manager');\n  if (mgrDropdown) mgrDropdown.value = emp.manager_id || '';\n  document.getElementById('emp-modal-title').textContent = emp.name;"

    if 'mgrDropdown' in content:
        print('  [settings.html] editEmployee JS vec ima manager postavljanje.')
    elif OLD_EDIT in content:
        content = content.replace(OLD_EDIT, NEW_EDIT, 1)
        print('  [settings.html] Azuriran editEmployee JS.')
    else:
        print('  [settings.html] UPOZORENJE: Nije pronaden editEmployee anchor!')

    # PATCH 6: saveEmployee JS - pošalji manager_id
    OLD_SAVE = "    is_default: document.getElementById('emp-default').checked ? 1 : 0,\n  };"
    NEW_SAVE = "    is_default: document.getElementById('emp-default').checked ? 1 : 0,\n    manager_id: (() => { const v = document.getElementById('emp-manager')?.value; return v ? parseInt(v) : null; })(),\n  };"

    if 'manager_id' in content and 'saveEmployee' in content:
        print('  [settings.html] saveEmployee JS vec salje manager_id.')
    elif OLD_SAVE in content:
        content = content.replace(OLD_SAVE, NEW_SAVE, 1)
        print('  [settings.html] Azuriran saveEmployee JS.')
    else:
        print('  [settings.html] UPOZORENJE: Nije pronaden saveEmployee anchor!')

    with open(SETTINGS_HTML, 'w', encoding='utf-8') as f:
        f.write(content)
    print('  [settings.html] Zapisano.')


if __name__ == '__main__':
    print('=== PATCH: Employee Manager & Roles UI Fix ===\n')
    print('1. Backup datoteka...')
    backup(APP_PY)
    backup(SETTINGS_HTML)
    print('\n2. Patching app.py...')
    patch_app_py()
    print('\n3. Patching settings.html...')
    patch_settings_html()
    print('\n=== GOTOVO! ===')
    print('Na kraju: cd ~/Projects/Softman_app && git add . && git commit -m "feat: voditelj zaposlenika, popravljen grid uloga" && git push origin main')
