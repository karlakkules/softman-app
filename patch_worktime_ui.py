#!/usr/bin/env python3
"""
patch_worktime_ui.py
Popravlja 5 UI problema u worktime modulu:
  worktime_form.html:
    1. Napomena kućica — proporcionalniji grid (2fr 1fr 1fr 1.5fr)
    2. Default zaposlenik = ulogirani korisnik
    3. Legenda boja Radni dan — bijela s borderom (ne tamno plava)
    4. R.br. — text-align:center
  worktime_list.html:
    5. Search input — ista veličina kao ostali filteri (width:140px)
Pokretanje: cd ~/Projects/Softman_app && python patch_worktime_ui.py
"""
import shutil, os

BASE    = os.path.expanduser('~/Projects/Softman_app')
WT_FORM = os.path.join(BASE, 'templates', 'worktime_form.html')
WT_LIST = os.path.join(BASE, 'templates', 'worktime_list.html')

def backup(p):
    shutil.copy2(p, p + '.bak6')
    print(f'  Backup: {p}.bak6')

def patch_form():
    with open(WT_FORM, 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. Form grid layout — napomena proporcionalna
    OLD = '<div class="form-row form-row-4">'
    NEW = '<div class="form-row" style="grid-template-columns:2fr 1fr 1fr 1.5fr;gap:16px;">'
    if OLD in c:
        c = c.replace(OLD, NEW, 1)
        print('  [form] ✅ Form grid layout')
    elif 'grid-template-columns:2fr' in c:
        print('  [form] Form grid već patchiran.')
    else:
        print('  [form] ❌ Form grid anchor nije pronađen!')

    # 2. Default zaposlenik
    OLD_OPT = """          {% for e in employees %}
          <option value="{{ e.id }}"
            {% if report and report.employee_id == e.id %}selected
            {% elif copy_from and copy_from.employee_id == e.id %}selected
            {% endif %}>{{ e.name }}</option>
          {% endfor %}"""
    NEW_OPT = """          {% for e in employees %}
          <option value="{{ e.id }}"
            {% if report and report.employee_id == e.id %}selected
            {% elif copy_from and copy_from.employee_id == e.id %}selected
            {% elif not report and not copy_from and my_emp_id is defined and e.id == my_emp_id %}selected
            {% endif %}>{{ e.name }}</option>
          {% endfor %}"""
    if OLD_OPT in c:
        c = c.replace(OLD_OPT, NEW_OPT, 1)
        print('  [form] ✅ Default zaposlenik')
    elif 'my_emp_id is defined' in c:
        print('  [form] Default zaposlenik već patchiran.')
    else:
        print('  [form] ❌ Default zaposlenik anchor nije pronađen!')

    # 3. Legenda boja Radni dan
    OLD_LEG = '<span style="display:flex;align-items:center;gap:4px;"><span style="width:12px;height:12px;background:#1A3A5C;border-radius:2px;display:inline-block;"></span> Radni dan</span>'
    NEW_LEG = '<span style="display:flex;align-items:center;gap:4px;"><span style="width:12px;height:12px;background:#ffffff;border:1.5px solid #1A3A5C;border-radius:2px;display:inline-block;"></span> Radni dan</span>'
    if OLD_LEG in c:
        c = c.replace(OLD_LEG, NEW_LEG, 1)
        print('  [form] ✅ Legenda Radni dan')
    elif 'border:1.5px solid #1A3A5C' in c:
        print('  [form] Legenda već patchirana.')
    else:
        print('  [form] ❌ Legenda anchor nije pronađen!')

    # 4. R.br. centriran
    OLD_RBR = '<th style="min-width:30px;background:#1A3A5C;color:white;padding:4px;">R.br.</th>'
    NEW_RBR = '<th style="min-width:30px;background:#1A3A5C;color:white;padding:4px;text-align:center;">R.br.</th>'
    if OLD_RBR in c:
        c = c.replace(OLD_RBR, NEW_RBR, 1)
        print('  [form] ✅ R.br. centriran')
    elif 'text-align:center;">R.br.' in c:
        print('  [form] R.br. već centriran.')
    else:
        print('  [form] ❌ R.br. anchor nije pronađen!')

    with open(WT_FORM, 'w', encoding='utf-8') as f:
        f.write(c)

def patch_list():
    with open(WT_LIST, 'r', encoding='utf-8') as f:
        c = f.read()

    # 5. Search input ista veličina kao ostali filteri
    OLD_SEARCH = '<input type="text" id="wt-search" class="form-control" placeholder="Pretraži..." style="width:200px;" oninput="filterWT()">'
    NEW_SEARCH = '<input type="text" id="wt-search" class="form-control" placeholder="Pretraži..." style="width:140px;" oninput="filterWT()">'
    if OLD_SEARCH in c:
        c = c.replace(OLD_SEARCH, NEW_SEARCH, 1)
        print('  [list] ✅ Search input veličina')
    elif 'width:140px' in c:
        print('  [list] Search input već patchiran.')
    else:
        print('  [list] ❌ Search input anchor nije pronađen!')

    with open(WT_LIST, 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    print('=== PATCH: Worktime UI popravci ===\n')
    backup(WT_FORM)
    backup(WT_LIST)

    print('\n1. worktime_form.html...')
    patch_form()

    print('\n2. worktime_list.html...')
    patch_list()

    print('\n=== ✅ GOTOVO! ===')
    print('Restart nije potreban — samo osvježi stranicu.')
    print('Git: cd ~/Projects/Softman_app && git add . && git commit -m "fix: worktime UI popravci" && git push origin main')
