#!/usr/bin/env python3
"""
Patch: form.html — postavi defaultne vrijednosti za polazak (07:00) i povratak (17:00)
        kada se otvara forma za NOVI putni nalog.
"""
import os, shutil, re

BASE = os.path.expanduser('~/Projects/Softman_app')
TMPL = os.path.join(BASE, 'templates', 'form.html')
BACKUP_DIR = os.path.join(BASE, '.backups')

os.makedirs(BACKUP_DIR, exist_ok=True)

# Backup
bak = os.path.join(BACKUP_DIR, 'form.html.bak_datetime_default')
shutil.copy2(TMPL, bak)
print(f'✅ Backup: {bak}')

with open(TMPL, 'r', encoding='utf-8') as f:
    content = f.read()

# Tražimo JS blok koji inicijalizira formu — dodat ćemo default datume
# nakon što se stranica učita, samo za novi nalog (kad nema order.id)

OLD = "// ── On employee change — fill position ───────────────────────────────────"

NEW = """// ── Default datetime za novi nalog ──────────────────────────────────────────
(function setDefaultDatetimes() {
  // Postavi defaultne vrijednosti samo za NOVI nalog (ne za uređivanje)
  const isNew = !document.getElementById('order-id');
  if (!isNew) return;
  const startEl = document.getElementById('trip_start_datetime');
  const endEl   = document.getElementById('trip_end_datetime');
  if (!startEl || !endEl) return;
  if (startEl.value && endEl.value) return; // već postavljeno
  // Danas u lokalnom formatu YYYY-MM-DD
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  const today = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
  startEl.value = `${today}T07:00`;
  endEl.value   = `${today}T17:00`;
  // Pokreni kalkulaciju dnevnica s defaultnim vrijednostima
  calcDnevnice();
})();

// ── On employee change — fill position ───────────────────────────────────"""

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open(TMPL, 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ Dodan default za polazak (07:00) i povratak (17:00) na novom putnom nalogu.')
else:
    print('❌ Nije pronađen marker u form.html — provjeri ručno.')
    print('   Traženi tekst: "// ── On employee change — fill position ───────────────────────────────────"')
