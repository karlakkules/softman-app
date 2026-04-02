#!/usr/bin/env python3
"""
patch_leave_calcdays.py
Popravlja računanje dana godišnjeg odmora:
- Backend sam računa radne dane (isključuje vikende i blagdane)
- Ne oslanja se na `days` koji dolazi s klijenta
- Frontend calcDays() ostaje isti (već isključuje vikende i blagdane)
Pokretanje: cd ~/Projects/Softman_app && python patch_leave_calcdays.py
"""
import shutil, os

BASE   = os.path.expanduser('~/Projects/Softman_app')
APP_PY = os.path.join(BASE, 'app.py')

def backup(p):
    shutil.copy2(p, p + '.bak2')
    print(f'  Backup: {p}.bak2')

def patch():
    with open(APP_PY, 'r', encoding='utf-8') as f:
        c = f.read()

    # ── 1. Dodaj helper funkciju calc_working_days prije leave_save ──────────
    HELPER = '''
def calc_working_days(date_from_str, date_to_str):
    """Broj radnih dana između dva datuma (uključivo), isključuje vikende i blagdane."""
    from datetime import date, timedelta
    try:
        d1 = date.fromisoformat(date_from_str)
        d2 = date.fromisoformat(date_to_str)
    except Exception:
        return 0
    if d1 > d2:
        return 0
    count = 0
    cur = d1
    while cur <= d2:
        ds = cur.isoformat()
        wd = cur.weekday()  # 0=Mon, 6=Sun
        if wd < 5 and ds not in ALL_HOLIDAYS:
            count += 1
        cur += timedelta(days=1)
    return count

'''

    ANCHOR_LEAVE_SAVE = "@app.route('/api/leave', methods=['POST'])\n@login_required\ndef leave_save():"
    if 'def calc_working_days' in c:
        print('✅ calc_working_days već postoji.')
    elif ANCHOR_LEAVE_SAVE in c:
        c = c.replace(ANCHOR_LEAVE_SAVE, HELPER + ANCHOR_LEAVE_SAVE, 1)
        print('✅ calc_working_days helper dodan')
    else:
        print('❌ Nije pronađen anchor za helper! Provjeri je li patch_leave_module.py već pokrenut.')
        return False

    # ── 2. U leave_save zamijeni 'days': data.get('days', 0) s izračunom ────
    OLD_DAYS = "        'days': data.get('days', 0),"
    NEW_DAYS = "        'days': calc_working_days(data.get('date_from',''), data.get('date_to','')),"

    if NEW_DAYS in c:
        print('✅ days izračun već postoji.')
    elif OLD_DAYS in c:
        c = c.replace(OLD_DAYS, NEW_DAYS, 1)
        print('✅ days se sada računa na backendu')
    else:
        print('❌ Nije pronađen OLD_DAYS anchor u leave_save!')
        return False

    with open(APP_PY, 'w', encoding='utf-8') as f:
        f.write(c)
    return True

if __name__ == '__main__':
    print('=== PATCH: Leave calcDays backend ===\n')
    backup(APP_PY)
    ok = patch()
    if ok:
        print('\n✅ Gotovo! Restart: python app.py')
    else:
        print('\n❌ Patch nije uspio — provjeri greške gore.')
