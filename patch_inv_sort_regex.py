#!/usr/bin/env python3
"""
Patch invoice_list.html - fix toIso regex u invSort funkciji.
Problem: /^(\d{2})\.(\d{2})\.(\d{4})/ ne matchira '19.3.2026' (1 znamenka za mjesec)
Fix: /^(\d{1,2})\.(\d{1,2})\.(\d{4})/
"""
import shutil, sys
from pathlib import Path

TEMPLATE = Path("templates/invoice_list.html")
if not TEMPLATE.exists():
    print(f"GREŠKA: {TEMPLATE} nije pronađen!")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE.with_suffix(".html.bak_iso"))
text = TEMPLATE.read_text(encoding="utf-8")

OLD = r"""      const toIso = v => {
        if (!v || v === '—') return '';
        const m = v.match(/^(\d{2})\.(\d{2})\.(\d{4})/);
        return m ? `${m[3]}-${m[2]}-${m[1]}` : v.substring(0, 10);
      };"""

NEW = r"""      const toIso = v => {
        if (!v || v === '—') return '';
        v = v.trim().replace(/\.+$/, '');
        const m = v.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
        if (m) return `${m[3]}-${m[2].padStart(2,'0')}-${m[1].padStart(2,'0')}`;
        if (/^\d{4}-\d{2}-\d{2}$/.test(v)) return v;
        return '';
      };"""

if OLD in text:
    text = text.replace(OLD, NEW)
    TEMPLATE.write_text(text, encoding="utf-8")
    print("✅ toIso regex popravljen — sada prepoznaje D.M.YYYY i DD.MM.YYYY")
else:
    print("⚠️  Pattern nije pronađen!")
    sys.exit(1)
