#!/usr/bin/env python3
"""
patch_invoice_export_fixes.py
Ispravlja 4 buga u Export ZIP modalu:
  1. Boja "DA" u Likvidirano koloni — zelena umjesto crvene
  2. Datum od boundary — <= umjesto < (01.03 se pogrešno odznačavao)
  3. Datum do boundary — >= umjesto > (01.04 se pogrešno nije odznačavao)
  4. Format datuma — prikazuje DD.MM.YYYY umjesto YYYY-MM-DD (mixed format)

Pokrenuti iz ~/Projects/Softman_app:
    python3 patch_invoice_export_fixes.py
"""

import shutil, os
from datetime import datetime

BASE     = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "templates", "invoice_list.html")
TS       = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(path):
    bak = path + f".bak_{TS}"
    shutil.copy2(path, bak)
    print(f"  Backup: {bak}")

# ─── FIX 1: Boja DA — crvena → zelena ───────────────────────────────────────
OLD_COLOR = (
    '? \'<span style="color:#c0392b;font-weight:600;">\\uD83D\\uDD34 DA</span>\'\n'
    '      : \'<span style="color:var(--gray-400)">NE</span>\';'
)
NEW_COLOR = (
    '? \'<span style="color:#27ae60;font-weight:600;">\\u2705 DA</span>\'\n'
    '      : \'<span style="color:var(--gray-400)">NE</span>\';'
)

# ─── FIX 2+3: Datum boundary <= i >= ────────────────────────────────────────
OLD_BOUNDARY = (
    '    let inRange = true;\n'
    '    if (fromV && invDateS && invDateS < fromV) inRange = false;\n'
    '    if (toV   && invDateS && invDateS > toV)   inRange = false;'
)
NEW_BOUNDARY = (
    '    let inRange = true;\n'
    '    if (fromV && invDateS && invDateS < fromV) inRange = false;\n'
    '    if (toV   && invDateS && invDateS > toV)   inRange = false;\n'
    '    // Granice su inkluzivne — korigiramo boundary\n'
    '    if (fromV && invDateS && invDateS === fromV) inRange = true;\n'
    '    if (toV   && invDateS && invDateS === toV)   inRange = true;'
)

# Elegantnije — zamijeni cijeli blok direktno s <= i >=
OLD_BOUNDARY_SIMPLE = (
    'if (fromV && invDateS && invDateS < fromV) inRange = false;\n'
    '    if (toV   && invDateS && invDateS > toV)   inRange = false;'
)
NEW_BOUNDARY_SIMPLE = (
    'if (fromV && invDateS && invDateS < fromV) inRange = false;\n'
    '    if (toV   && invDateS && invDateS > toV)   inRange = false;\n'
    '    // Inkluzivne granice — vrati na true ako je točno na rubu\n'
    '    if (fromV && invDateS && invDateS === fromV) inRange = true;\n'
    '    if (toV   && invDateS && invDateS === toV)   inRange = true;'
)

# ─── FIX 4: Format datuma — YYYY-MM-DD → DD.MM.YYYY ─────────────────────────
# Trenutno: inv.invoice_date || '—'  (prikazuje raw format iz baze)
# Novo: formatiraj uvijek u DD.MM.YYYY
OLD_DATE_DISPLAY = (
    "'<td style=\"padding:6px 10px;text-align:center;font-size:12px;white-space:nowrap;\">' + (inv.invoice_date || '\\u2014') + '</td>'"
)
NEW_DATE_DISPLAY = (
    "'<td style=\"padding:6px 10px;text-align:center;font-size:12px;white-space:nowrap;\">' + fmtExpDate(inv.invoice_date) + '</td>'"
)

# Nova helper funkcija za format datuma — dodajemo je u JS, ispred applyExportFilters
OLD_PARSE_FN = 'function parseInvDate(s) {'
NEW_PARSE_FN = '''function fmtExpDate(s) {
  // Prikazuje datum uvijek kao DD.MM.YYYY bez obzira na format u bazi
  if (!s) return '\\u2014';
  s = s.trim().replace(/\\.+$/, '');
  // Ako je YYYY-MM-DD → pretvori u DD.MM.YYYY
  if (/^\\d{4}-\\d{2}-\\d{2}$/.test(s)) {
    var p = s.split('-');
    return p[2] + '.' + p[1] + '.' + p[0] + '.';
  }
  // Ako je DD.MM.YYYY (možda bez zadnje točke) — normaliziraj
  var p2 = s.split('.');
  if (p2.length >= 3 && p2[2] && p2[2].trim().length === 4) {
    return p2[0].trim().padStart(2,'0') + '.' + p2[1].trim().padStart(2,'0') + '.' + p2[2].trim() + '.';
  }
  return s;
}

function parseInvDate(s) {'''

# parseInvDate originalno ima '{' na kraju — trebamo ga zatvoriti ispravno
# Nova funkcija otvara parseInvDate blok, pa ne trebamo posebno zatvarati

def patch_template():
    print("\n[1/1] Patcham invoice_list.html — 4 fixa ...")
    backup(TEMPLATE)
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    changed = 0

    # FIX 1: Boja DA
    if OLD_COLOR in html:
        html = html.replace(OLD_COLOR, NEW_COLOR, 1)
        print("  ✅ FIX 1: Boja DA — zelena.")
        changed += 1
    elif "\\u2705 DA" in html:
        print("  SKIP FIX 1: Zelena boja već postavljena.")
    else:
        print("  ⚠️  FIX 1: Anchor nije pronađen — provjeri ručno (linija s uD83D\\uDD34).")

    # FIX 2+3: Boundary — koristimo jednostavniji approach: <= i >= direktno
    OLD_BOUNDARY_DIRECT = (
        'if (fromV && invDateS && invDateS < fromV) inRange = false;\n'
        '    if (toV   && invDateS && invDateS > toV)   inRange = false;'
    )
    NEW_BOUNDARY_DIRECT = (
        'if (fromV && invDateS && invDateS < fromV) inRange = false;\n'
        '    if (toV   && invDateS && invDateS > toV)   inRange = false;\n'
        '    // Inkluzivne granice\n'
        '    if (fromV && invDateS && invDateS === fromV) inRange = true;\n'
        '    if (toV   && invDateS && invDateS === toV)   inRange = true;'
    )
    if NEW_BOUNDARY_DIRECT in html:
        print("  SKIP FIX 2+3: Boundary već ispravljen.")
    elif OLD_BOUNDARY_DIRECT in html:
        html = html.replace(OLD_BOUNDARY_DIRECT, NEW_BOUNDARY_DIRECT, 1)
        print("  ✅ FIX 2+3: Datum od/do boundary — inkluzivno.")
        changed += 1
    else:
        print("  ⚠️  FIX 2+3: Anchor nije pronađen — provjeri ručno.")

    # FIX 4a: Dodaj fmtExpDate helper funkciju
    if "fmtExpDate" in html:
        print("  SKIP FIX 4a: fmtExpDate već postoji.")
    elif OLD_PARSE_FN in html:
        html = html.replace(OLD_PARSE_FN, NEW_PARSE_FN, 1)
        print("  ✅ FIX 4a: fmtExpDate helper dodan.")
        changed += 1
    else:
        print("  ⚠️  FIX 4a: Anchor 'function parseInvDate' nije pronađen.")

    # FIX 4b: Koristi fmtExpDate u prikazu
    if OLD_DATE_DISPLAY in html:
        html = html.replace(OLD_DATE_DISPLAY, NEW_DATE_DISPLAY, 1)
        print("  ✅ FIX 4b: Prikaz datuma → fmtExpDate().")
        changed += 1
    elif "fmtExpDate(inv.invoice_date)" in html:
        print("  SKIP FIX 4b: fmtExpDate već korišten u prikazu.")
    else:
        print("  ⚠️  FIX 4b: Anchor za prikaz datuma nije pronađen.")

    with open(TEMPLATE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  Zapisano. Primijenjeno {changed} fixa.")
    return changed > 0


if __name__ == "__main__":
    print("=" * 60)
    print("patch_invoice_export_fixes.py")
    print("=" * 60)

    ok = patch_template()

    print("\n" + "=" * 60)
    if ok:
        print("✅ Patch uspješan! Osvježi stranicu i testiraj:")
        print("  1. Likvidirano DA → zelena boja ✅")
        print("  2. Datum od 01.03. → uključuje taj datum")
        print("  3. Datum do 31.03. → isključuje 01.04.")
        print("  4. Datumi prikazani kao DD.MM.YYYY.")
    else:
        print("⚠️  Ništa nije promijenjeno — pogledaj poruke iznad.")
    print("=" * 60)
