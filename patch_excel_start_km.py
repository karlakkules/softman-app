#!/usr/bin/env python3
"""
Patch: app.py — Excel export prikazuje krivu početnu km u dnevnoj tablici.

Bug: stupac 'početno' piše cur_km (koji je end_km prethodnog dana),
     ali trebalo bi pisati start_km_d (početnu km tog konkretnog dana iz baze).
     
     Za 2026-03-01: baza ima start_km=51904, ali korisnik je upisao 51890
     kao početnu km evidencije. Excel treba pokazivati vrijednost iz baze (start_km_d),
     jer je to stvarna početna km za taj dan prema GPS podacima.
     
     Dodatno: u else grani (dan nije u bazi) nedostaje start_km_d varijabla.
"""

import shutil
from pathlib import Path

APP = Path('app.py')

if not APP.exists():
    print('ERROR: app.py nije pronađen!')
    exit(1)

shutil.copy(APP, APP.with_suffix('.py.bak'))
print('✅ Backup kreiran: app.py.bak')

content = APP.read_text(encoding='utf-8')

# ─── Fix 1: else grana — dodaj start_km_d varijablu ─────────────────────────
OLD_ELSE = """        else:
            official   = pn_official.get(date_str, 0) if is_pn else 0
            private    = 0 if is_pn else private_per_day
            total_day  = round(official + private, 2)
            end_km_day = round(cur_km + total_day, 2)
            pn_label   = pn_by_day[date_str]['label'] if is_pn else ''
            comment    = pn_label if is_pn else ('privatno' if private > 0 else '')
            cur_km     = end_km_day"""

NEW_ELSE = """        else:
            start_km_d = cur_km
            official   = pn_official.get(date_str, 0) if is_pn else 0
            private    = 0 if is_pn else private_per_day
            total_day  = round(official + private, 2)
            end_km_day = round(cur_km + total_day, 2)
            pn_label   = pn_by_day[date_str]['label'] if is_pn else ''
            comment    = pn_label if is_pn else ('privatno' if private > 0 else '')
            cur_km     = end_km_day"""

if OLD_ELSE in content:
    content = content.replace(OLD_ELSE, NEW_ELSE)
    print('✅ Fix 1: start_km_d dodan u else granu')
else:
    print('❌ Fix 1: pattern nije pronađen')
    exit(1)

# ─── Fix 2: stupac "početno" — piši start_km_d umjesto cur_km ────────────────
OLD_COLS = """        sc2(r, 2, date_str, font=th(9), align=al('center'), border=full_brd, fill=fill2)
        sc2(r, 3, round(cur_km, 0), font=th(9), align=al('center'), border=full_brd, fill=fill2, nfmt='#,##0')
        sc2(r, 4, end_km_day, font=th(9), align=al('center'), border=full_brd, fill=fill2, nfmt='#,##0')"""

NEW_COLS = """        sc2(r, 2, date_str, font=th(9), align=al('center'), border=full_brd, fill=fill2)
        sc2(r, 3, round(start_km_d, 0), font=th(9), align=al('center'), border=full_brd, fill=fill2, nfmt='#,##0')
        sc2(r, 4, end_km_day, font=th(9), align=al('center'), border=full_brd, fill=fill2, nfmt='#,##0')"""

if OLD_COLS in content:
    content = content.replace(OLD_COLS, NEW_COLS)
    print('✅ Fix 2: stupac "početno" sada piše start_km_d')
else:
    print('❌ Fix 2: pattern nije pronađen')
    exit(1)

APP.write_text(content, encoding='utf-8')
print('\n✅ Patch uspješno primijenjen!')
print('Testiraj: generiraj Excel za ožujak — stupac "početno" za 2026-03-01 treba biti 51904 (iz GPS baze), a ne 51890.')
