#!/usr/bin/env python3
"""
Patch v4 za templates/invoice_list.html:
  1. Ukloni kolonu redni broj (td loop.index + th prazni)
  2. Plaćeno i Likvidirano gumbi/badge skraći za ~20% (font-size, padding)
  3. Ukloni <th>Korisnik</th> iz headera (ostao od prethodnog patcha)

Pokreni: python3 patch_invoice_list_v4.py
"""
import shutil, os, re

TARGET = os.path.join('templates', 'invoice_list.html')
BACKUP = TARGET + '.bak_v4'

if not os.path.exists(TARGET):
    print(f"❌ Nije pronađen: {TARGET}"); exit(1)

shutil.copy2(TARGET, BACKUP)
print(f"✅ Backup: {BACKUP}")

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

fixes = 0

# ═══════════════════════════════════════════════════════════════════════════
# FIX 1: Ukloni th redni broj (prazni th na početku)
# ═══════════════════════════════════════════════════════════════════════════
for pattern in [
    '          <th style="width:28px;"></th>\n',
    '          <th style="width:32px;"></th>\n',
    '          <th style="width:30px;"></th>\n',
]:
    if pattern in content:
        content = content.replace(pattern, '', 1); fixes += 1
        print(f"✅ FIX 1a: Prazni th uklonjen")
        break
else:
    # regex fallback
    content, n = re.subn(r'          <th style="width:\d+px;"></th>\n', '', content, count=1)
    if n: fixes += 1; print("✅ FIX 1a: Prazni th uklonjen (regex)")
    else: print("⚠️  FIX 1a: Prazni th nije pronađen")

# FIX 1b: Ukloni th Korisnik (ostao od v3)
for pattern in [
    '          <th style="width:75px;">Korisnik</th>\n',
    '          <th style="width:70px;">Korisnik</th>\n',
    '          <th style="width:80px;">Korisnik</th>\n',
]:
    if pattern in content:
        content = content.replace(pattern, '', 1); fixes += 1
        print("✅ FIX 1b: th Korisnik uklonjen")
        break
else:
    content, n = re.subn(r'          <th style="[^"]*">\s*Korisnik\s*</th>\n', '', content, count=1)
    if n: fixes += 1; print("✅ FIX 1b: th Korisnik uklonjen (regex)")
    else: print("⚠️  FIX 1b: th Korisnik nije pronađen (možda već uklonjen)")

# FIX 1c: Ukloni td redni broj (loop.index)
OLD_LOOPIDX = '          <td style="text-align:center;color:var(--gray-500);font-size:12px;">{{ loop.index }}</td>\n'
if OLD_LOOPIDX in content:
    content = content.replace(OLD_LOOPIDX, '', 1); fixes += 1
    print("✅ FIX 1c: td loop.index uklonjen")
else:
    content, n = re.subn(r'          <td[^>]*>\s*\{\{\s*loop\.index\s*\}\}\s*</td>\n', '', content, count=1)
    if n: fixes += 1; print("✅ FIX 1c: td loop.index uklonjen (regex)")
    else: print("⚠️  FIX 1c: td loop.index nije pronađen")

# FIX 1d: colspan prilagodi — smanji za 2 (redni br + korisnik)
for old_cs, new_cs in [('colspan="13"','colspan="11"'), ('colspan="12"','colspan="10"'),
                        ('colspan="11"','colspan="10"')]:  # već je 11 od v3
    if old_cs in content:
        content = content.replace(old_cs, new_cs, 1); fixes += 1
        print(f"✅ FIX 1d: colspan {old_cs} → {new_cs}")
        break

# ═══════════════════════════════════════════════════════════════════════════
# FIX 2: Plaćeno gumbi/badge — manji font i padding (~20% manje)
# ═══════════════════════════════════════════════════════════════════════════

# Gumb ✅ DA (admin/editor)
OLD_PAID_BTN = 'style="font-size:11px;padding:2px 8px;background:#f0faf4;color:#27ae60;border:1px solid #a8d5b5;cursor:pointer;"'
NEW_PAID_BTN = 'style="font-size:10px;padding:1px 5px;background:#f0faf4;color:#27ae60;border:1px solid #a8d5b5;cursor:pointer;"'
if OLD_PAID_BTN in content:
    content = content.replace(OLD_PAID_BTN, NEW_PAID_BTN); fixes += 1
    print("✅ FIX 2a: ✅ DA gumb manji")

# Badge ✅ DA (read-only)
OLD_PAID_BADGE = 'style="background:#f0faf4;color:#27ae60;border:1px solid #a8d5b5;"'
NEW_PAID_BADGE = 'style="background:#f0faf4;color:#27ae60;border:1px solid #a8d5b5;font-size:10px;padding:1px 5px;"'
if OLD_PAID_BADGE in content:
    content = content.replace(OLD_PAID_BADGE, NEW_PAID_BADGE); fixes += 1
    print("✅ FIX 2b: ✅ DA badge manji")

# Gumb Označi
OLD_OZNACI = 'style="font-size:11px;padding:2px 8px;background:#fff8e1;color:#e67e22;border:1px solid #f0c14b;"'
NEW_OZNACI = 'style="font-size:10px;padding:1px 5px;background:#fff8e1;color:#e67e22;border:1px solid #f0c14b;"'
if OLD_OZNACI in content:
    content = content.replace(OLD_OZNACI, NEW_OZNACI); fixes += 1
    print("✅ FIX 2c: Označi gumb manji")

# Likvidirano: badge 🔴 DA
OLD_LIQ_BADGE = 'style="background:#fdecea;color:#c0392b;border:1px solid #f5aca6;">🔴 DA</span>'
NEW_LIQ_BADGE = 'style="background:#fdecea;color:#c0392b;border:1px solid #f5aca6;font-size:10px;padding:1px 5px;">✅ DA</span>'
if OLD_LIQ_BADGE in content:
    content = content.replace(OLD_LIQ_BADGE, NEW_LIQ_BADGE); fixes += 1
    print("✅ FIX 2d: Likvidirano badge manji")

# Gumb Likvidiraj
OLD_LIQ_BTN = 'style="font-size:11px;padding:2px 8px;background:#fdecea;color:#c0392b;border:1px solid #f5aca6;"'
NEW_LIQ_BTN = 'style="font-size:10px;padding:1px 5px;background:#fdecea;color:#c0392b;border:1px solid #f5aca6;"'
if OLD_LIQ_BTN in content:
    content = content.replace(OLD_LIQ_BTN, NEW_LIQ_BTN); fixes += 1
    print("✅ FIX 2e: Likvidiraj gumb manji")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 Patch v4 završen! ({fixes} fixa)")
print("   git add templates/invoice_list.html && git commit -m 'ui: ukloni redni br i korisnik kolonu, manji placeno/liq gumbi' && git push origin main")
