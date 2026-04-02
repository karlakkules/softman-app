#!/usr/bin/env python3
"""
patch_invoice_export_fixes_v2.py
Zamjenjuje cijeli JS blok za export modal s ispravnom verzijom.

Fiksevi:
  1. Datum od/do — usporedba bez Date objekta (izbjegava timezone bug)
  2. Format datuma — DD-MM-YYYY (s crticom)
  3. Sortiranje — od najnovijih prema najstarijima (client-side)
  4. Boja DA ostaje zelena (već ispravno)

Pokrenuti iz ~/Projects/Softman_app:
    python3 patch_invoice_export_fixes_v2.py
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

# ── Stari JS blok koji zamjenjujemo (od fmtExpDate do kraja applyExportFilters) ──
# Tražimo od "function fmtExpDate" do "updateExpCount();" koji zatvara forEach
OLD_JS_START = "function fmtExpDate(s) {"

# Novi, ispravljeni JS blok
NEW_JS_BLOCK = r"""function toIsoDateStr(s) {
  // Pretvara bilo koji format datuma u YYYY-MM-DD string za usporedbu
  // BEZ korištenja Date objekta (izbjegava timezone offset bugove)
  if (!s) return null;
  s = s.trim().replace(/\.+$/, '');
  // Već YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  // DD.MM.YYYY ili D.M.YYYY
  var p = s.split('.');
  if (p.length >= 3 && p[2] && p[2].trim().length === 4) {
    return p[2].trim() + '-' + p[1].trim().padStart(2,'0') + '-' + p[0].trim().padStart(2,'0');
  }
  return null;
}

function getYearFromDateStr(s) {
  // Izvuci godinu bez Date objekta
  var iso = toIsoDateStr(s);
  return iso ? parseInt(iso.slice(0, 4), 10) : null;
}

function fmtExpDate(s) {
  // Prikaz uvijek kao DD-MM-YYYY
  if (!s) return '\u2014';
  var iso = toIsoDateStr(s);
  if (iso) {
    var parts = iso.split('-');
    return parts[2] + '-' + parts[1] + '-' + parts[0];
  }
  return s;
}

function applyExportFilters() {
  var year  = parseInt(document.getElementById('exp-year').value, 10);
  var fromV = document.getElementById('exp-date-from').value; // YYYY-MM-DD ili ''
  var toV   = document.getElementById('exp-date-to').value;   // YYYY-MM-DD ili ''

  var tbody = document.getElementById('exp-tbody');
  tbody.innerHTML = '';
  var totalVisible = 0;

  // Sortiraj od najnovijeg prema najstarijem (string usporedba radi za YYYY-MM-DD)
  var sorted = _expAllInvoices.slice().sort(function(a, b) {
    var da = toIsoDateStr(a.invoice_date) || '';
    var db = toIsoDateStr(b.invoice_date) || '';
    if (db > da) return 1;
    if (db < da) return -1;
    return b.id - a.id;
  });

  sorted.forEach(function(inv) {
    var invYear = getYearFromDateStr(inv.invoice_date);

    // Filter godinom — miče red s popisa
    if (invYear !== year) return;

    var invIso = toIsoDateStr(inv.invoice_date); // YYYY-MM-DD ili null

    // Filter datum od/do — inkluzivne granice, bez Date objekta
    var inRange = true;
    if (fromV && invIso && invIso < fromV) inRange = false;
    if (toV   && invIso && invIso > toV)   inRange = false;

    totalVisible++;

    var isLiq = inv.is_liquidated
      ? '<span style="color:#27ae60;font-weight:600;">\u2705 DA</span>'
      : '<span style="color:var(--gray-400)">NE</span>';
    var amount = inv.amount_total != null
      ? Number(inv.amount_total).toFixed(2) + ' \u20AC'
      : '\u2014';

    var tr = document.createElement('tr');
    tr.dataset.id = inv.id;
    tr.style.cssText = 'border-bottom:1px solid var(--gray-100);cursor:pointer;';
    tr.innerHTML =
      '<td style="text-align:center;padding:6px 8px;">' +
        '<input type="checkbox" class="exp-row-cb" data-id="' + inv.id + '" ' + (inRange ? 'checked' : '') + ' onchange="updateExpCount()">' +
      '</td>' +
      '<td style="padding:6px 10px;font-weight:600;font-size:13px;">' + (inv.invoice_number || '\u2014') + '</td>' +
      '<td style="padding:6px 10px;font-size:13px;">' + (inv.partner_name || '\u2014') + '</td>' +
      '<td style="padding:6px 10px;font-size:11px;color:var(--gray-500);">' + (inv.partner_oib || '\u2014') + '</td>' +
      '<td style="padding:6px 10px;text-align:right;font-weight:600;font-size:13px;">' + amount + '</td>' +
      '<td style="padding:6px 10px;text-align:center;font-size:12px;white-space:nowrap;">' + fmtExpDate(inv.invoice_date) + '</td>' +
      '<td style="padding:6px 10px;text-align:center;font-size:12px;">' + isLiq + '</td>';

    tr.addEventListener('click', function(e) {
      if (e.target.type === 'checkbox') return;
      var cb = this.querySelector('.exp-row-cb');
      cb.checked = !cb.checked;
      updateExpCount();
    });
    tbody.appendChild(tr);
  });

  if (totalVisible === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--gray-400);">Nema ra\u010duna za odabranu godinu.</td></tr>';
  }

  updateExpCount();
}"""

def patch_template():
    print("\n[1/1] Patcham invoice_list.html ...")
    backup(TEMPLATE)
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    # Provjeri je li već novi blok
    if "toIsoDateStr" in html:
        print("  SKIP: Novi JS blok već postoji (toIsoDateStr).")
        return True

    # Pronađi početak starog bloka
    start_idx = html.find(OLD_JS_START)
    if start_idx == -1:
        print("  GREŠKA: Nije pronađen 'function fmtExpDate' — provjeri template.")
        return False

    # Pronađi kraj starog bloka — završava s "updateExpCount();\n}" nakon applyExportFilters
    # Tražimo zatvaranje applyExportFilters funkcije
    # Ključ: "updateExpCount();\n}" — zadnji poziv updateExpCount unutar applyExportFilters
    end_marker = "  updateExpCount();\n}"
    end_idx = html.find(end_marker, start_idx)
    if end_idx == -1:
        # Pokušaj bez leading spacea
        end_marker = "  updateExpCount();\n}"
        end_idx = html.rfind("updateExpCount();\n}", start_idx, start_idx + 8000)
        if end_idx == -1:
            print("  GREŠKA: Nije pronađen kraj applyExportFilters bloka.")
            # Debug: prikaži što ima od start_idx
            print("  Debug — sadržaj od 'fmtExpDate' na 200 znakova:")
            print("  " + repr(html[start_idx:start_idx+200]))
            return False

    end_idx += len(end_marker)

    # Zamijeni stari blok s novim
    html = html[:start_idx] + NEW_JS_BLOCK + html[end_idx:]
    print("  OK: JS blok zamijenjen (fmtExpDate + parseInvDate + applyExportFilters).")

    with open(TEMPLATE, "w", encoding="utf-8") as f:
        f.write(html)
    print("  Zapisano.")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("patch_invoice_export_fixes_v2.py")
    print("=" * 60)

    ok = patch_template()

    print("\n" + "=" * 60)
    if ok:
        print("✅ Patch uspješan! Osvježi stranicu i testiraj:")
        print("  1. Datum od 01.03. → uključuje 01.03. (checkbox ON)")
        print("  2. Datum do 31.03. → isključuje 01.04. (checkbox OFF)")
        print("  3. Datumi prikazani kao DD-MM-YYYY (s crticom)")
        print("  4. Sortirano od najnovijeg prema najstarijem")
    else:
        print("⚠️  Patch nije uspio — pogledaj poruke iznad.")
    print("=" * 60)
