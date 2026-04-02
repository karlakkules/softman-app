#!/usr/bin/env python3
"""
patch_invoice_export.py  (v2 — ispravljena verzija)
Dodaje Export ZIP funkcionalnost u Ulazne račune.

Što radi:
1. Dodaje gumb "Export" između "Dobavljači" i "Izbrisani" u invoice_list.html
2. Dodaje Export modal s filterima + checkbox listom računa
3. Dodaje Flask rute /api/invoices/all-for-export i /invoices/export-zip u app.py

Pokrenuti iz ~/Projects/Softman_app:
    python3 patch_invoice_export.py
"""

import shutil, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "templates", "invoice_list.html")
APP_PY   = os.path.join(BASE, "app.py")
TS       = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(path):
    bak = path + f".bak_{TS}"
    shutil.copy2(path, bak)
    print(f"  Backup: {bak}")

# ─────────────────────────────────────────────────────────────
# 1. TEMPLATE — dodaj gumb i modal
# ─────────────────────────────────────────────────────────────

EXPORT_BTN_OLD = '<button class="btn btn-secondary" onclick="openSuppliersModal()" title="Upravljanje dobavljačima">🏢 Dobavljači</button>\n<a href="/invoices/deleted" class="btn btn-secondary" title="Izbrisani računi">🗑 Izbrisani</a>'

EXPORT_BTN_NEW = '<button class="btn btn-secondary" onclick="openSuppliersModal()" title="Upravljanje dobavljačima">🏢 Dobavljači</button>\n<button class="btn btn-secondary" onclick="openExportModal()" title="Export računa u ZIP">📦 Export</button>\n<a href="/invoices/deleted" class="btn btn-secondary" title="Izbrisani računi">🗑 Izbrisani</a>'

EXPORT_MODAL_AND_JS = '''
<!-- ── EXPORT MODAL ── -->
<div class="modal-overlay" id="export-modal" style="z-index:1010;">
  <div class="modal" style="width:860px;max-width:96vw;max-height:92vh;display:flex;flex-direction:column;">
    <div class="modal-header" style="flex-shrink:0;">
      <span class="modal-title">📦 Export računa (ZIP)</span>
      <button class="btn btn-ghost btn-icon" onclick="closeExportModal()">✕</button>
    </div>

    <!-- Filteri -->
    <div style="padding:12px 20px;border-bottom:1px solid var(--gray-100);display:flex;gap:10px;flex-wrap:wrap;align-items:center;flex-shrink:0;background:var(--gray-50);">
      <div style="display:flex;align-items:center;gap:6px;">
        <label style="font-size:12px;font-weight:600;color:var(--gray-600);">Godina:</label>
        <select id="exp-year" class="form-control" style="width:90px;" onchange="applyExportFilters()">
          <option value="2026" selected>2026</option>
          <option value="2027">2027</option>
          <option value="2028">2028</option>
          <option value="2029">2029</option>
          <option value="2030">2030</option>
        </select>
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <label style="font-size:12px;font-weight:600;color:var(--gray-600);">Datum od:</label>
        <input type="date" id="exp-date-from" class="form-control" style="width:140px;" onchange="applyExportFilters()">
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <label style="font-size:12px;font-weight:600;color:var(--gray-600);">Datum do:</label>
        <input type="date" id="exp-date-to" class="form-control" style="width:140px;" onchange="applyExportFilters()">
      </div>
      <div style="margin-left:auto;display:flex;gap:8px;align-items:center;">
        <button class="btn btn-sm btn-secondary" onclick="expSelectAll()">Označi sve</button>
        <button class="btn btn-sm btn-secondary" onclick="expDeselectAll()">Odznači sve</button>
        <span id="exp-count-label" style="font-size:12px;color:var(--gray-500);"></span>
      </div>
    </div>

    <!-- Tablica -->
    <div style="flex:1;overflow-y:auto;padding:0;">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="position:sticky;top:0;background:var(--gray-50);z-index:2;">
            <th style="width:36px;padding:8px;text-align:center;border-bottom:2px solid var(--gray-200);">
              <input type="checkbox" id="exp-check-all" onchange="expToggleAll(this.checked)" title="Označi/odznači sve">
            </th>
            <th style="padding:8px 10px;text-align:left;font-size:12px;border-bottom:2px solid var(--gray-200);white-space:nowrap;">Broj računa</th>
            <th style="padding:8px 10px;text-align:left;font-size:12px;border-bottom:2px solid var(--gray-200);">Partner</th>
            <th style="padding:8px 10px;text-align:left;font-size:12px;border-bottom:2px solid var(--gray-200);">OIB</th>
            <th style="padding:8px 10px;text-align:right;font-size:12px;border-bottom:2px solid var(--gray-200);">Iznos</th>
            <th style="padding:8px 10px;text-align:center;font-size:12px;border-bottom:2px solid var(--gray-200);">Datum</th>
            <th style="padding:8px 10px;text-align:center;font-size:12px;border-bottom:2px solid var(--gray-200);">Likvidirano</th>
          </tr>
        </thead>
        <tbody id="exp-tbody"></tbody>
      </table>
    </div>

    <!-- Footer -->
    <div class="modal-footer" style="flex-shrink:0;">
      <span id="exp-selected-label" style="font-size:12px;color:var(--gray-500);margin-right:auto;"></span>
      <button class="btn btn-secondary" onclick="closeExportModal()">Odustani</button>
      <button class="btn btn-primary" id="exp-export-btn" onclick="doExport()">📦 Export ZIP</button>
    </div>
  </div>
</div>

<script>
// ── Export modal ────────────────────────────────────────────────────────────
let _expAllInvoices = [];

async function openExportModal() {
  document.getElementById('export-modal').classList.add('open');
  document.getElementById('exp-tbody').innerHTML =
    '<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--gray-400);">Učitavanje...</td></tr>';

  try {
    const res = await fetch('/api/invoices/all-for-export');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    _expAllInvoices = await res.json();
  } catch(e) {
    document.getElementById('exp-tbody').innerHTML =
      '<tr><td colspan="7" style="text-align:center;padding:20px;color:red;">Greška: ' + e.message + '</td></tr>';
    return;
  }

  document.getElementById('exp-year').value = '2026';
  document.getElementById('exp-date-from').value = '';
  document.getElementById('exp-date-to').value = '';
  document.getElementById('exp-check-all').checked = false;

  applyExportFilters();
}

function closeExportModal() {
  document.getElementById('export-modal').classList.remove('open');
}

function parseInvDate(s) {
  if (!s) return null;
  s = s.trim().replace(/\\.+$/, '');
  if (/^\\d{4}-\\d{2}-\\d{2}$/.test(s)) return new Date(s + 'T00:00:00');
  const p = s.split('.');
  if (p.length >= 3 && p[2] && p[2].trim().length === 4) {
    const d = p[0].trim().padStart(2,'0');
    const m = p[1].trim().padStart(2,'0');
    const y = p[2].trim();
    return new Date(y + '-' + m + '-' + d + 'T00:00:00');
  }
  return null;
}

function applyExportFilters() {
  const year  = parseInt(document.getElementById('exp-year').value, 10);
  const fromV = document.getElementById('exp-date-from').value;
  const toV   = document.getElementById('exp-date-to').value;

  const tbody = document.getElementById('exp-tbody');
  tbody.innerHTML = '';
  let totalVisible = 0;

  _expAllInvoices.forEach(function(inv) {
    const invDate = parseInvDate(inv.invoice_date);
    const invYear = invDate ? invDate.getFullYear() : null;

    // Filter godinom — miče red s popisa
    if (invYear !== year) return;

    // Datum za usporedbu kao YYYY-MM-DD string
    const invDateS = invDate ? invDate.toISOString().slice(0,10) : null;

    // Filter datum od/do — mijenja samo checkbox stanje
    let inRange = true;
    if (fromV && invDateS && invDateS < fromV) inRange = false;
    if (toV   && invDateS && invDateS > toV)   inRange = false;

    totalVisible++;

    const isLiq = inv.is_liquidated
      ? '<span style="color:#c0392b;font-weight:600;">\\uD83D\\uDD34 DA</span>'
      : '<span style="color:var(--gray-400)">NE</span>';
    const amount = inv.amount_total != null
      ? Number(inv.amount_total).toFixed(2) + ' \\u20AC'
      : '\\u2014';

    const tr = document.createElement('tr');
    tr.dataset.id = inv.id;
    tr.style.cssText = 'border-bottom:1px solid var(--gray-100);cursor:pointer;';
    tr.innerHTML =
      '<td style="text-align:center;padding:6px 8px;">' +
        '<input type="checkbox" class="exp-row-cb" data-id="' + inv.id + '" ' + (inRange ? 'checked' : '') + ' onchange="updateExpCount()">' +
      '</td>' +
      '<td style="padding:6px 10px;font-weight:600;font-size:13px;">' + (inv.invoice_number || '\\u2014') + '</td>' +
      '<td style="padding:6px 10px;font-size:13px;">' + (inv.partner_name || '\\u2014') + '</td>' +
      '<td style="padding:6px 10px;font-size:11px;color:var(--gray-500);">' + (inv.partner_oib || '\\u2014') + '</td>' +
      '<td style="padding:6px 10px;text-align:right;font-weight:600;font-size:13px;">' + amount + '</td>' +
      '<td style="padding:6px 10px;text-align:center;font-size:12px;white-space:nowrap;">' + (inv.invoice_date || '\\u2014') + '</td>' +
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
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--gray-400);">Nema računa za odabranu godinu.</td></tr>';
  }

  updateExpCount();
}

function expSelectAll() {
  document.querySelectorAll('.exp-row-cb').forEach(function(cb) { cb.checked = true; });
  updateExpCount();
}
function expDeselectAll() {
  document.querySelectorAll('.exp-row-cb').forEach(function(cb) { cb.checked = false; });
  updateExpCount();
}
function expToggleAll(checked) {
  document.querySelectorAll('.exp-row-cb').forEach(function(cb) { cb.checked = checked; });
  updateExpCount();
}

function updateExpCount() {
  var all = document.querySelectorAll('.exp-row-cb');
  var sel = document.querySelectorAll('.exp-row-cb:checked');
  document.getElementById('exp-count-label').textContent = all.length + ' račun(a) ukupno';
  document.getElementById('exp-selected-label').textContent = 'Odabrano: ' + sel.length + ' račun(a)';
  var allCb = document.getElementById('exp-check-all');
  if (all.length > 0) {
    allCb.checked = sel.length === all.length;
    allCb.indeterminate = sel.length > 0 && sel.length < all.length;
  }
  document.getElementById('exp-export-btn').disabled = sel.length === 0;
}

async function doExport() {
  var ids = Array.from(document.querySelectorAll('.exp-row-cb:checked')).map(function(cb) { return Number(cb.dataset.id); });
  if (!ids.length) { alert('Nema odabranih računa!'); return; }

  var btn = document.getElementById('exp-export-btn');
  btn.disabled = true;
  btn.textContent = '\\u23F3 Priprema ZIP-a...';

  try {
    var res = await fetch('/invoices/export-zip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: ids })
    });
    if (!res.ok) {
      var msg = 'Greška pri generiranju ZIP-a';
      try { var d = await res.json(); msg = d.error || msg; } catch(e) {}
      alert(msg);
      return;
    }
    var blob = await res.blob();
    var url  = URL.createObjectURL(blob);
    var a    = document.createElement('a');
    a.href = url;
    a.download = 'racuni_export_' + new Date().toISOString().slice(0,10) + '.zip';
    document.body.appendChild(a);
    a.click();
    setTimeout(function() { URL.revokeObjectURL(url); a.remove(); }, 1000);
  } finally {
    btn.disabled = false;
    btn.textContent = '\\uD83D\\uDCE6 Export ZIP';
  }
}
</script>
'''

def patch_template():
    print("\n[1/2] Patcham invoice_list.html ...")
    backup(TEMPLATE)
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    if "openExportModal" in html:
        print("  SKIP: Export gumb već postoji.")
    elif EXPORT_BTN_OLD not in html:
        print("  GREŠKA: Nije pronađen anchor za gumb!")
        # Prikaži prvih 200 znakova za debug
        idx = html.find("openSuppliersModal")
        if idx >= 0:
            print("  Debug — našao openSuppliersModal, okolina:")
            print("  " + repr(html[max(0,idx-10):idx+150]))
        return False
    else:
        html = html.replace(EXPORT_BTN_OLD, EXPORT_BTN_NEW, 1)
        print("  OK: Export gumb dodan.")

    if "export-modal" in html:
        print("  SKIP: Export modal već postoji.")
    else:
        idx = html.rfind("{% endblock %}")
        if idx == -1:
            print("  GREŠKA: Nije pronađen {% endblock %}")
            return False
        html = html[:idx] + EXPORT_MODAL_AND_JS + "\n" + html[idx:]
        print("  OK: Export modal i JS dodani.")

    with open(TEMPLATE, "w", encoding="utf-8") as f:
        f.write(html)
    print("  Zapisano.")
    return True


# ─────────────────────────────────────────────────────────────
# 2. app.py — rute
# Napomene:
#   - stored_path i liquidated_pdf_path su APSOLUTNI putevi u bazi
#   - import re se dodaje lokalno unutar funkcije (pattern iz app.py)
#   - io je već importan globalno u app.py
# ─────────────────────────────────────────────────────────────

API_ALL_FOR_EXPORT = """
@app.route('/api/invoices/all-for-export')
@login_required
def api_invoices_all_for_export():
    \"\"\"Vraća sve (neobrisane) račune za export modal.\"\"\"
    user = get_current_user()
    if not (user.get('is_admin') or user.get('can_view_invoices')):
        return jsonify({'error': 'Nedovoljna prava'}), 403
    conn = get_db()
    rows = conn.execute(\"\"\"
        SELECT id, invoice_number, partner_name, partner_oib,
               invoice_date, amount_total, is_liquidated,
               liquidated_pdf_path, stored_path
        FROM invoices
        WHERE is_deleted = 0 OR is_deleted IS NULL
        ORDER BY invoice_date DESC, id DESC
    \"\"\").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

"""

API_EXPORT_ZIP = """
@app.route('/invoices/export-zip', methods=['POST'])
@login_required
def invoices_export_zip():
    \"\"\"Generira ZIP od likvidirani PDF-ova (ili originala) za odabrane račune.\"\"\"
    import zipfile, re as _re
    user = get_current_user()
    if not (user.get('is_admin') or user.get('can_view_invoices')):
        return jsonify({'error': 'Nedovoljna prava'}), 403

    data = request.get_json(force=True)
    ids  = data.get('ids', [])
    if not ids:
        return jsonify({'error': 'Nema odabranih računa'}), 400

    placeholders = ','.join('?' for _ in ids)
    conn = get_db()
    rows = conn.execute(
        f\"\"\"SELECT id, invoice_number, partner_name, invoice_date,
                   stored_path, liquidated_pdf_path, is_liquidated
            FROM invoices
            WHERE id IN ({placeholders}) AND (is_deleted=0 OR is_deleted IS NULL)\"\"\",
        ids
    ).fetchall()
    conn.close()

    def safe_filename(inv_number, partner, inv_id):
        def clean(s):
            return _re.sub(r'[^\\w\\-.]', '_', (s or '').strip())[:40]
        return f"{clean(inv_number)}_{clean(partner)}_{inv_id}.pdf"

    zip_buf = io.BytesIO()
    added = 0

    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for row in rows:
            inv = dict(row)
            # Apsolutni putevi — direktno provjeri os.path.exists
            liq  = inv.get('liquidated_pdf_path')
            orig = inv.get('stored_path')
            pdf_path = None
            if liq and os.path.exists(liq):
                pdf_path = liq
            elif orig and os.path.exists(orig):
                pdf_path = orig

            if pdf_path:
                fname = safe_filename(
                    inv.get('invoice_number'),
                    inv.get('partner_name'),
                    inv['id']
                )
                # Izbjegni duplikata u ZIP arhivi
                existing = zf.namelist()
                base_fname = fname
                counter = 1
                while fname in existing:
                    name_part, ext_part = os.path.splitext(base_fname)
                    fname = f"{name_part}_{counter}{ext_part}"
                    counter += 1
                zf.write(pdf_path, fname)
                added += 1

    if added == 0:
        return jsonify({'error': 'Nijedan odabrani račun nema PDF datoteku na disku.'}), 404

    zip_buf.seek(0)
    return send_file(
        zip_buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"racuni_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    )

"""

ANCHOR_MARKER = "@app.route('/invoices/deleted')"

def patch_app_py():
    print("\n[2/2] Patcham app.py ...")
    backup(APP_PY)
    with open(APP_PY, encoding="utf-8") as f:
        src = f.read()

    if ANCHOR_MARKER not in src:
        print(f"  GREŠKA: Marker '{ANCHOR_MARKER}' nije pronađen u app.py!")
        return False

    if "api_invoices_all_for_export" in src:
        print("  SKIP: all-for-export ruta već postoji.")
    else:
        src = src.replace(ANCHOR_MARKER, API_ALL_FOR_EXPORT + ANCHOR_MARKER, 1)
        print("  OK: all-for-export ruta dodana.")

    if "invoices_export_zip" in src:
        print("  SKIP: export-zip ruta već postoji.")
    else:
        src = src.replace(ANCHOR_MARKER, API_EXPORT_ZIP + ANCHOR_MARKER, 1)
        print("  OK: export-zip ruta dodana.")

    with open(APP_PY, "w", encoding="utf-8") as f:
        f.write(src)
    print("  Zapisano.")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("patch_invoice_export.py  (v2)")
    print("=" * 60)

    ok1 = patch_template()
    ok2 = patch_app_py()

    print("\n" + "=" * 60)
    if ok1 and ok2:
        print("✅ Patch uspješan!")
        print("\nPokreni Flask i testiraj:")
        print("  1. Otvori Ulazni računi")
        print("  2. Klikni gumb '📦 Export'")
        print("  3. Odaberi godinu / filtriraj datumom")
        print("  4. Selektiraj račune → klikni 'Export ZIP'")
    else:
        print("⚠️  Nešto nije patchano — pogledaj poruke iznad!")
    print("=" * 60)
