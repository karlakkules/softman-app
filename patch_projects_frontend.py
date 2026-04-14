#!/usr/bin/env python3
"""
Patch: dashboard.html + base.html
  1. Dashboard — widget za sate po projektima danas
  2. base.html — nav link za Projekte
"""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

changes = 0

# ── 1. dashboard.html ─────────────────────────────────────────────────────────
DASH = os.path.join(BASE, 'templates', 'dashboard.html')
shutil.copy2(DASH, os.path.join(BACKUP_DIR, 'dashboard.html.bak_projects'))

with open(DASH, 'r', encoding='utf-8') as f:
    dash = f.read()

WIDGET = """
  <!-- Projekti — sati danas -->
  <div class="card" style="border-top:3px solid #8e44ad;">
    <div class="card-header" style="background:#f5eef8;">
      <span class="card-title" style="color:#6c3483;">📁 Projekti — sati danas</span>
      <a href="/projects" style="font-size:12px;color:#8e44ad;text-decoration:none;font-weight:600;">Svi →</a>
    </div>
    <div class="card-body" style="padding-top:8px;">
      {% if project_hours_today %}
        {% for ph in project_hours_today %}
        <div style="margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">
            <span style="color:var(--gray-700);font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:70%;">{{ ph.name }}</span>
            <span style="color:var(--navy);font-weight:700;">{{ '%.1f'|format(ph.hours) }}h</span>
          </div>
          <div style="height:5px;background:var(--gray-100);border-radius:3px;overflow:hidden;">
            <div style="height:5px;border-radius:3px;background:{{ ph.color or '#8e44ad' }};width:{{ [(ph.hours / [project_hours_today_total, 0.1]|max * 100)|int, 100]|min }}%;"></div>
          </div>
        </div>
        {% endfor %}
        <div style="margin-top:8px;padding-top:8px;border-top:1px solid var(--gray-100);display:flex;justify-content:space-between;font-size:12px;">
          <span style="color:var(--gray-500);">Ukupno danas</span>
          <span style="font-weight:700;color:var(--navy);">{{ '%.1f'|format(project_hours_today_total) }}h</span>
        </div>
      {% else %}
        <div style="color:var(--gray-400);font-size:13px;text-align:center;padding:12px 0;">Nema unosa za danas</div>
        <a href="/projects" style="display:block;text-align:center;font-size:12px;color:#8e44ad;font-weight:600;margin-top:4px;text-decoration:none;">+ Unesi sate</a>
      {% endif %}
    </div>
  </div>

"""

# Ubaci widget u donji red (grid-template-columns:repeat(3,1fr)) — prije Radno vrijeme kartice
ANCHOR_DASH = "<!-- Zaposlenici radno vrijeme -->"
if ANCHOR_DASH in dash and 'project_hours_today' not in dash:
    dash = dash.replace(ANCHOR_DASH, WIDGET + ANCHOR_DASH)
    # Promijeni grid na 4 kolone u donjem redu
    dash = dash.replace(
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">',
        '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">',
        1
    )
    changes += 1
    print('✅ Dashboard widget za projekte dodan')
else:
    print('⚠️  Dashboard widget već postoji ili anchor nije pronađen')

with open(DASH, 'w', encoding='utf-8') as f:
    f.write(dash)

# ── 2. base.html — nav link ───────────────────────────────────────────────────
BASE_HTML = os.path.join(BASE, 'templates', 'base.html')
shutil.copy2(BASE_HTML, os.path.join(BACKUP_DIR, 'base.html.bak_projects'))

with open(BASE_HTML, 'r', encoding='utf-8') as f:
    base = f.read()

NAV_ANCHOR = '<a href="/worktime" class="nav-item {% if active==\'worktime\' %}active{% endif %}">'
NAV_NEW = """<a href="/projects" class="nav-item {% if active=='projects' %}active{% endif %}">
      <span class="icon">📁</span>
      <span>Projekti</span>
    </a>
    """ + NAV_ANCHOR

if '/projects' not in base and NAV_ANCHOR in base:
    base = base.replace(NAV_ANCHOR, NAV_NEW, 1)
    changes += 1
    print('✅ Nav link za Projekte dodan u base.html')
else:
    print('⚠️  Nav link već postoji ili anchor nije pronađen')

with open(BASE_HTML, 'w', encoding='utf-8') as f:
    f.write(base)

print(f'\n{"✅ Frontend patch gotov" if changes else "❌ Bez promjena"} ({changes} izmjena)')
print('\nPokreni:')
print('  1. python3 patch_projects_backend.py')
print('  2. python3 patch_projects_frontend.py')
print('  3. Kopiraj projects_list.html u templates/')
print('  4. Restart Flask')
