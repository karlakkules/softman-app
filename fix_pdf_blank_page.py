#!/usr/bin/env python3
"""
fix_pdf_blank_page.py
Zamjenjuje PageBreak s CondPageBreak u create_pdf funkciji u app.py
kako bi se eliminirala prazna stranica u PDF-u putnih naloga.

Pokretanje:
    cd ~/Projects/Softman_app
    python3 fix_pdf_blank_page.py
"""

import re
import shutil
import os

APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
BAK_PATH = APP_PATH + '.bak_fix_blank_page'

def patch():
    with open(APP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # ── 1. Dodaj CondPageBreak u import ───────────────────────────────────────
    old_import = 'from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image, PageBreak'
    new_import = 'from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image, PageBreak, CondPageBreak'

    if old_import not in content:
        # Možda je već patchano ili se format razlikuje
        if 'CondPageBreak' in content:
            print("INFO: CondPageBreak već postoji u importu — preskačem import patch.")
        else:
            print("GREŠKA: Ne mogu pronaći import liniju. Provjeri app.py ručno.")
            return False
    else:
        content = content.replace(old_import, new_import, 1)
        print("OK: Import ažuriran (dodano CondPageBreak).")

    # ── 2. Zamijeni PageBreak() s CondPageBreak unutar create_pdf ─────────────
    # Pronađi create_pdf funkciju i zamijeni samo unutar nje
    func_start = content.find('def create_pdf(')
    if func_start == -1:
        print("GREŠKA: Ne mogu pronaći create_pdf funkciju.")
        return False

    # Pronađi sljedeću def na razini 0 uvlake nakon create_pdf
    # (sve između create_pdf i sljedeće top-level def/@app.route)
    func_end_match = re.search(r'\n(?:def |@app\.)', content[func_start + 10:])
    if func_end_match:
        func_end = func_start + 10 + func_end_match.start()
    else:
        func_end = len(content)

    func_body = content[func_start:func_end]

    # Broj zamjena PageBreak() → CondPageBreak(50*mm) unutar create_pdf
    # Koristimo 50mm praga: prelomi stranicu samo ako ima < 50mm slobodnog prostora
    new_func_body = func_body.replace('story.append(PageBreak())', 'story.append(CondPageBreak(50*mm))')

    count = func_body.count('story.append(PageBreak())')
    if count == 0:
        print("UPOZORENJE: Nije pronađen 'story.append(PageBreak())' unutar create_pdf.")
        print("  Tražim alternativne oblike...")
        # Alternativni oblik
        alt_count = func_body.count('PageBreak()')
        if alt_count > 0:
            print(f"  Pronađeno {alt_count}x 'PageBreak()' — zamjenjujem direktno.")
            new_func_body = func_body.replace('PageBreak()', 'CondPageBreak(50*mm)')
            count = alt_count
        else:
            print("  Nije pronađen ni jedan PageBreak() u create_pdf. Nema što patchati.")
            print("  Provjeri app.py — možda je struktura drugačija.")
            return False

    print(f"OK: Zamijenjeno {count}x PageBreak() → CondPageBreak(50*mm) u create_pdf.")

    content = content[:func_start] + new_func_body + content[func_end:]

    # ── 3. Spremi backup i novi file ──────────────────────────────────────────
    shutil.copy2(APP_PATH, BAK_PATH)
    print(f"OK: Backup spremljen → {BAK_PATH}")

    with open(APP_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"OK: app.py ažuriran.")
    print()
    print("Restartaj Flask server pa generiraj testni PDF za provjeru.")
    return True

if __name__ == '__main__':
    patch()
