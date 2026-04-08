#!/usr/bin/env python3
"""
Patch: form.html — polje Klijent / Partner postaje obavezno pri spremanju naloga.
"""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
TMPL = os.path.join(BASE, 'templates', 'form.html')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

bak = os.path.join(BACKUP_DIR, 'form.html.bak_client_required')
shutil.copy2(TMPL, bak)
print(f'✅ Backup: {bak}')

with open(TMPL, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Label — dodaj * uz "Klijent / Partner"
OLD_LABEL = 'data-hr="Klijent / Partner" data-en="Client / Partner">Klijent / Partner'
NEW_LABEL = 'data-hr="Klijent / Partner" data-en="Client / Partner">Klijent / Partner *'
if OLD_LABEL in content:
    content = content.replace(OLD_LABEL, NEW_LABEL, 1)
    changes += 1
    print('✅ Label označen s *')
else:
    print('⚠️  Label nije pronađen — provjeri ručno')

# 2. Validacija u saveOrder — dodaj provjeru client_info
# Tražimo postojeću validaciju za destination ili purpose i dodamo client_info ispred
OLD_VAL = "const destination = document.getElementById('destination').value;"
NEW_VAL = """const destination = document.getElementById('destination').value;
  const client_info = document.getElementById('client_info')?.value.trim() || '';
  if (!client_info) {
    toast('Klijent / Partner je obavezno polje!', 'error');
    document.getElementById('client_info')?.focus();
    return;
  }"""

# Fallback — traži po drugom markeru ako destination nije tu
OLD_VAL2 = "async function saveOrder(newStatus) {"
NEW_VAL2 = """async function saveOrder(newStatus) {
  const client_info_check = document.getElementById('client_info')?.value.trim() || '';
  if (!client_info_check) {
    toast('Klijent / Partner je obavezno polje!', 'error');
    document.getElementById('client_info')?.focus();
    return;
  }"""

if OLD_VAL in content and NEW_VAL not in content:
    content = content.replace(OLD_VAL, NEW_VAL, 1)
    changes += 1
    print('✅ Validacija client_info dodana u saveOrder (metoda 1)')
elif OLD_VAL2 in content and NEW_VAL2 not in content:
    content = content.replace(OLD_VAL2, NEW_VAL2, 1)
    changes += 1
    print('✅ Validacija client_info dodana u saveOrder (metoda 2)')
else:
    print('⚠️  saveOrder marker nije pronađen ili je već patchan')

with open(TMPL, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{"✅ Patch primijenjen" if changes else "❌ Nema promjena"} ({changes} izmjena)')
