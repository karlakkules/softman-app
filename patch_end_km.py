#!/usr/bin/env python3
"""
Patch: vehicle_log_form.html — automatsko popunjavanje end_km iz CSV-a
Problem: parseCSV() popunjava total_km, official_km, private_km, ali ne i end_km.
Fix 1: Nakon što se postavi total_km, ako start_km postoji — postavi end_km = start + total.
Fix 2: calcTotal() ide samo end-start=total; dodaj i obrnuto izračunavanje kad se total ručno unese.
"""

import re
import shutil
from pathlib import Path

TEMPLATE = Path('templates/vehicle_log_form.html')

if not TEMPLATE.exists():
    print(f'ERROR: {TEMPLATE} ne postoji!')
    exit(1)

shutil.copy(TEMPLATE, TEMPLATE.with_suffix('.html.bak'))
print('✅ Backup kreiran')

content = TEMPLATE.read_text(encoding='utf-8')

# --- FIX 1: U parseCSV(), odmah nakon postavljanja total_km, dodaj izračun end_km ---
OLD = """  document.getElementById('total_km').value = data.total_km;
  document.getElementById('official_km').value = data.official_km;
  document.getElementById('private_km').value = data.private_km;"""

NEW = """  document.getElementById('total_km').value = data.total_km;
  document.getElementById('official_km').value = data.official_km;
  document.getElementById('private_km').value = data.private_km;
  // Automatski izračunaj end_km = start_km + total_km
  const _startKm = parseFloat(document.getElementById('start_km').value || 0);
  if (_startKm > 0 && data.total_km > 0) {
    const _endKm = Math.round((_startKm + data.total_km) * 100) / 100;
    document.getElementById('end_km').value = _endKm;
    document.getElementById('end_km').style.background = '#f0faf4';
    setTimeout(() => document.getElementById('end_km').style.background = '', 2000);
  }"""

if OLD in content:
    content = content.replace(OLD, NEW)
    print('✅ Fix 1: end_km automatski popunjen iz CSV-a')
else:
    print('⚠️  Fix 1: pattern nije pronađen — provjeri ručno')

# --- FIX 2: Poboljšaj calcTotal() da radi i obrnuto (start + total = end) ---
OLD2 = """function calcTotal() {
  const start = parseFloat(document.getElementById('start_km').value||0);
  const end = parseFloat(document.getElementById('end_km').value||0);
  const total = end - start;
  document.getElementById('total_km').value = total > 0 ? total.toFixed(2) : '';
}"""

NEW2 = """function calcTotal(changed) {
  const start = parseFloat(document.getElementById('start_km').value||0);
  const end = parseFloat(document.getElementById('end_km').value||0);
  const total = parseFloat(document.getElementById('total_km').value||0);
  if (changed === 'total' && start > 0 && total > 0) {
    // Korisnik je promijenio total → izračunaj end
    document.getElementById('end_km').value = Math.round((start + total) * 100) / 100;
  } else {
    // Default: end - start = total
    const t = end - start;
    document.getElementById('total_km').value = t > 0 ? t.toFixed(2) : '';
  }
}"""

if OLD2 in content:
    content = content.replace(OLD2, NEW2)
    print('✅ Fix 2: calcTotal() poboljšan (bidirekcionaln)')
else:
    print('⚠️  Fix 2: pattern nije pronađen — provjeri ručno')

# Ažuriraj oninput na total_km polju da prosljeđuje 'total'
OLD3 = 'id="total_km" step="0.01" value="{{ log.total_km if log else \'\' }}" readonly style="background:var(--gray-50);">'
NEW3 = 'id="total_km" step="0.01" value="{{ log.total_km if log else \'\' }}" readonly style="background:var(--gray-50);" oninput="calcTotal(\'total\')">'

if OLD3 in content:
    content = content.replace(OLD3, NEW3)
    print('✅ Fix 3: oninput dodan na total_km polje')
else:
    print('ℹ️  Fix 3: total_km je readonly — oninput nije potreban, preskačem')

# Ažuriraj start_km oninput da ne utječe na end kad je end već popunjen
OLD4 = 'oninput="calcTotal()" style="border-color:#f5c6a0;"'
# (ovo je private_km, preskačemo)

TEMPLATE.write_text(content, encoding='utf-8')
print(f'\n✅ Patch primijenjen na {TEMPLATE}')
print('\nTestiraj: učitaj CSV → provjeri je li end_km automatski popunjen.')
