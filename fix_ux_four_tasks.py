#!/usr/bin/env python3
"""
fix_ux_four_tasks.py

4 poboljšanja u orders.html i invoice_list.html:

1. Neupareni troškovi — PN select prikazuje datum putovanja uz broj PN
2. Unos troška — upozorenje ako postoji trošak s istim datumom i iznosom
3. Ulazni računi — filter po koloni (kao u Putnim nalozima)
4. Unos troška — kategorija je obavezno polje

Pokreni iz korijena projekta:
    python fix_ux_four_tasks.py
"""

import shutil, re
from pathlib import Path

ORDERS_PATH  = Path("templates/orders.html")
INVOICE_PATH = Path("templates/invoice_list.html")

for p in [ORDERS_PATH, INVOICE_PATH]:
    if not p.exists():
        print(f"❌ Nije pronađeno: {p}")
        exit(1)

shutil.copy2(ORDERS_PATH,  ORDERS_PATH.with_suffix(".html.bak3"))
shutil.copy2(INVOICE_PATH, INVOICE_PATH.with_suffix(".html.bak3"))
print("✅ Backupi kreirani (.bak3)")

# ═══════════════════════════════════════════════════════════════════
# PATCH 1 + 2 + 4 — orders.html
# ═══════════════════════════════════════════════════════════════════
orders = ORDERS_PATH.read_text(encoding="utf-8")

# ── FIX 1: loadActivePnList — dodaj datum putovanja u label ──────────────
OLD_LOAD_PN = """  const sel = document.getElementById('exp-pn-select');
  sel.innerHTML = '<option value="">— Bez veze (neupareno) —</option>';
  _expActivePnList.forEach(pn => {
    const label = `PN ${pn.auto_id} — ${pn.destination || ''} — ${pn.employee_name || ''} — ${pn.purpose || ''}`;
    sel.innerHTML += `<option value="${pn.id}">${label}</option>`;
  });"""

NEW_LOAD_PN = """  const sel = document.getElementById('exp-pn-select');
  sel.innerHTML = '<option value="">— Bez veze (neupareno) —</option>';
  _expActivePnList.forEach(pn => {
    // Formatiraj datum putovanja uz broj PN
    let dateStr = '';
    if (pn.departure_date) {
      const d = pn.departure_date;
      // YYYY-MM-DD → DD.MM.YYYY.
      dateStr = d.length >= 10 ? `${d.slice(8,10)}.${d.slice(5,7)}.${d.slice(0,4)}.` : d;
    }
    const dateLabel = dateStr ? ` [${dateStr}]` : '';
    const label = `PN ${pn.auto_id}${dateLabel} — ${pn.destination || ''} — ${pn.employee_name || ''} — ${pn.purpose || ''}`;
    sel.innerHTML += `<option value="${pn.id}">${label}</option>`;
  });"""

if OLD_LOAD_PN in orders:
    orders = orders.replace(OLD_LOAD_PN, NEW_LOAD_PN)
    print("✅ Fix 1: PN select prikazuje datum putovanja")
else:
    print("⚠️  Fix 1: Nije pronađen loadActivePnList blok — provjeri ručno")

# ── FIX 2 + 4: saveExpense — kategorija obavezna + duplikat provjera ────
OLD_SAVE_EXP = """async function saveExpense() {
  const amount = parseFloat(document.getElementById('exp-amount').value);
  if (!amount || amount <= 0) { toast('Unesite iznos!', 'error'); return; }"""

NEW_SAVE_EXP = """async function saveExpense() {
  const amount = parseFloat(document.getElementById('exp-amount').value);
  if (!amount || amount <= 0) { toast('Unesite iznos!', 'error'); return; }

  // FIX 4: Kategorija je obavezno polje
  const categoryEl = document.getElementById('exp-category');
  if (!categoryEl.value) {
    categoryEl.style.border = '2px solid #c0392b';
    categoryEl.focus();
    toast('Kategorija troška je obavezno polje!', 'error');
    setTimeout(() => { categoryEl.style.border = ''; }, 2500);
    return;
  }

  // FIX 2: Provjeri duplikat (isti datum + isti iznos)
  const docDate = document.getElementById('exp-doc-date').value;
  if (docDate && amount > 0) {
    try {
      const chkRes = await fetch(`/api/pn-expenses/check-duplicate?date=${docDate}&amount=${amount}`);
      if (chkRes.ok) {
        const chkData = await chkRes.json();
        if (chkData.found) {
          const existing = chkData.expenses.map(e =>
            `• ${e.doc_date} · ${parseFloat(e.amount).toFixed(2)} € · ${e.description || 'bez opisa'} · ${e.category_name || ''}`
          ).join('\\n');
          const confirmed = confirm(
            `⚠️ Upozorenje: Već postoji trošak s istim datumom (${docDate}) i iznosom (${amount.toFixed(2)} €):\\n\\n${existing}\\n\\nJesi li siguran/na da želiš evidentirati ovaj trošak?`
          );
          if (!confirmed) return;
        }
      }
    } catch(e) { /* tiho — nastavi sa spremanjem */ }
  }"""

if OLD_SAVE_EXP in orders:
    orders = orders.replace(OLD_SAVE_EXP, NEW_SAVE_EXP)
    print("✅ Fix 2: Duplikat provjera pri unosu troška")
    print("✅ Fix 4: Kategorija troška je obavezno polje")
else:
    print("⚠️  Fix 2+4: Nije pronađen saveExpense blok")

# ── FIX 1 za unmatched modal: PN select u linkPnExpense ──────────────────
# U openUnmatched, gdje se gradi HTML za svaki unmatched trošak, postoji select za PN
# Trebamo dodati datum i tamo — ali taj select se gradi dinamički iz istog _expActivePnList
# Patch: zamijeni buildUnmatchedRowHtml label isti kao gore

OLD_UNMATCHED_OPTS = """    const pnOptions = '<option value="">— odaberi PN —</option>' +
      _cachedPnList.map(pn =>
        `<option value="${pn.id}">PN ${pn.auto_id} — ${pn.destination || ''} — ${pn.employee_name || ''}</option>`
      ).join('');"""

NEW_UNMATCHED_OPTS = """    const pnOptions = '<option value="">— odaberi PN —</option>' +
      _cachedPnList.map(pn => {
        let dateStr = '';
        if (pn.departure_date) {
          const d = pn.departure_date;
          dateStr = d.length >= 10 ? `${d.slice(8,10)}.${d.slice(5,7)}.${d.slice(0,4)}.` : d;
        }
        const dateLabel = dateStr ? ` [${dateStr}]` : '';
        return `<option value="${pn.id}">PN ${pn.auto_id}${dateLabel} — ${pn.destination || ''} — ${pn.employee_name || ''}</option>`;
      }).join('');"""

if OLD_UNMATCHED_OPTS in orders:
    orders = orders.replace(OLD_UNMATCHED_OPTS, NEW_UNMATCHED_OPTS)
    print("✅ Fix 1b: Neupareni troškovi PN select prikazuje datum")
else:
    # Alternativni pattern
    alt_old = """      _cachedPnList.map(pn =>
        `<option value="${pn.id}">PN ${pn.auto_id} — ${pn.destination || ''} — ${pn.employee_name || ''}</option>`
      ).join('');"""
    alt_new = """      _cachedPnList.map(pn => {
        let dateStr = '';
        if (pn.departure_date) {
          const d = pn.departure_date;
          dateStr = d.length >= 10 ? `${d.slice(8,10)}.${d.slice(5,7)}.${d.slice(0,4)}.` : d;
        }
        const dateLabel = dateStr ? ` [${dateStr}]` : '';
        return `<option value="${pn.id}">PN ${pn.auto_id}${dateLabel} — ${pn.destination || ''} — ${pn.employee_name || ''}</option>`;
      }).join('');"""
    if alt_old in orders:
        orders = orders.replace(alt_old, alt_new)
        print("✅ Fix 1b (alt): Neupareni troškovi PN select prikazuje datum")
    else:
        print("ℹ️  Fix 1b: Nije pronađen unmatched PN select blok (možda već ispravno)")

ORDERS_PATH.write_text(orders, encoding="utf-8")
print(f"✅ orders.html ažuriran")

# ═══════════════════════════════════════════════════════════════════
# PATCH 3 — invoice_list.html — filter po koloni
# ═══════════════════════════════════════════════════════════════════
invoice = INVOICE_PATH.read_text(encoding="utf-8")

# Dodaj stil za col-filter ako ga nema
if 'col-filter' not in invoice:
    OLD_SCRIPT_START = "<script>\nlet _currentFile = null;"
    NEW_SCRIPT_START = """<style>
.inv-col-filter { width:100%; padding:3px 6px; font-size:11px; border:1px solid var(--gray-200);
  border-radius:4px; background:white; color:var(--gray-700); box-sizing:border-box; }
.inv-col-filter:focus { outline:none; border-color:var(--accent); }
#inv-col-filters th { padding:4px 5px; font-weight:normal; background:var(--gray-50); }
</style>
<script>
let _currentFile = null;"""
    if OLD_SCRIPT_START in invoice:
        invoice = invoice.replace(OLD_SCRIPT_START, NEW_SCRIPT_START)
        print("✅ Fix 3: Dodan CSS za col-filtere u invoice_list")

# Dodaj red s filterima u thead tablice ulaznih računa
OLD_THEAD = """        <tr>
          <th style="width:32px;"></th>
          <th style="width:120px;">Broj računa</th>
          <th>Partner</th>
          <th style="width:95px;">OIB</th>
          <th style="text-align:right;width:90px;">Iznos</th>
          <th style="width:88px;">Datum</th>
          <th style="width:88px;">Dospijeće</th>
          <th style="text-align:center;width:72px;">Plaćeno</th>
          <th style="text-align:center;width:82px;">Likvidirano</th>
          <th style="width:32px;text-align:center;" title="Napomena">💬</th>
          <th style="width:75px;">Korisnik</th>
          <th style="width:100px;">Akcije</th>
        </tr>
      </thead>"""

NEW_THEAD = """        <tr>
          <th style="width:32px;"></th>
          <th style="width:120px;">Broj računa</th>
          <th>Partner</th>
          <th style="width:95px;">OIB</th>
          <th style="text-align:right;width:90px;">Iznos</th>
          <th style="width:88px;">Datum</th>
          <th style="width:88px;">Dospijeće</th>
          <th style="text-align:center;width:72px;">Plaćeno</th>
          <th style="text-align:center;width:82px;">Likvidirano</th>
          <th style="width:32px;text-align:center;" title="Napomena">💬</th>
          <th style="width:75px;">Korisnik</th>
          <th style="width:100px;">Akcije</th>
        </tr>
        <tr id="inv-col-filters">
          <th></th>
          <th><input class="inv-col-filter" data-col="broj" placeholder="Filtriraj..." oninput="invColFilter()"></th>
          <th><input class="inv-col-filter" data-col="partner" placeholder="Filtriraj..." oninput="invColFilter()"></th>
          <th><input class="inv-col-filter" data-col="oib" placeholder="Filtriraj..." oninput="invColFilter()"></th>
          <th></th>
          <th><input class="inv-col-filter" data-col="datum" placeholder="Filtriraj..." oninput="invColFilter()"></th>
          <th><input class="inv-col-filter" data-col="dospijece" placeholder="Filtriraj..." oninput="invColFilter()"></th>
          <th></th><th></th><th></th>
          <th><input class="inv-col-filter" data-col="korisnik" placeholder="Filtriraj..." oninput="invColFilter()"></th>
          <th></th>
        </tr>
      </thead>"""

if OLD_THEAD in invoice:
    invoice = invoice.replace(OLD_THEAD, NEW_THEAD)
    print("✅ Fix 3: Dodan red s filterima u thead invoice_list tablice")
else:
    print("⚠️  Fix 3: Thead nije pronađen — provjeri ručno")

# Dodaj data-col atribute na <td> u tbody — trebamo za filter logiku
# Koristimo pristup: dodaj data atribute na <tr> i filtriramo u JS

# Dodaj data-* atribute na <tr> redove u tbody
OLD_TR = """        <tr data-id="{{ inv.id }}"
            data-paid="{{ inv.is_paid }}"
            data-liq="{{ inv.is_liquidated }}"
            data-search="{{ inv.partner_name }} {{ inv.invoice_number }} {{ inv.partner_oib }}"
            data-payment="{{ inv.paid_card_last4 or '' }}"
            style="cursor:pointer;"
            ondblclick="if(!event.target.closest('button,a,input')) openEditModal(this)">"""

NEW_TR = """        <tr data-id="{{ inv.id }}"
            data-paid="{{ inv.is_paid }}"
            data-liq="{{ inv.is_liquidated }}"
            data-search="{{ inv.partner_name }} {{ inv.invoice_number }} {{ inv.partner_oib }}"
            data-payment="{{ inv.paid_card_last4 or '' }}"
            data-broj="{{ inv.invoice_number or '' }}"
            data-partner="{{ inv.partner_name or '' }}"
            data-oib="{{ inv.partner_oib or '' }}"
            data-datum="{{ inv.invoice_date or '' }}"
            data-dospijece="{{ inv.due_date or '' }}"
            data-korisnik="{{ inv.created_by_username or '' }}"
            style="cursor:pointer;"
            ondblclick="if(!event.target.closest('button,a,input')) openEditModal(this)">"""

if OLD_TR in invoice:
    invoice = invoice.replace(OLD_TR, NEW_TR)
    print("✅ Fix 3: Dodani data-* atributi na <tr> redove")
else:
    print("⚠️  Fix 3: <tr> pattern nije pronađen")

# Dodaj invColFilter JS funkciju u script blok
OLD_FILTER_FN = "function filterInv() {"
NEW_FILTER_FN = """function invColFilter() {
  const filters = {};
  document.querySelectorAll('.inv-col-filter').forEach(inp => {
    const val = inp.value.trim().toLowerCase();
    if (val) filters[inp.dataset.col] = val;
  });
  document.querySelectorAll('#inv-tbody tr[data-id]').forEach(row => {
    let show = true;
    for (const [col, val] of Object.entries(filters)) {
      const cellVal = (row.dataset[col] || '').toLowerCase();
      if (!cellVal.includes(val)) { show = false; break; }
    }
    // Postavi display samo ako ostali filteri prolaze
    if (!show) { row.style.display = 'none'; return; }
    // Provjeri i globalne filtere (search, paid, liq, payment)
    const search = document.getElementById('inv-search')?.value.toLowerCase() || '';
    const paid = document.getElementById('inv-paid')?.value || '';
    const liq = document.getElementById('inv-liq')?.value || '';
    const payment = document.getElementById('inv-payment')?.value || '';
    const ms = !search || (row.dataset.search || '').toLowerCase().includes(search);
    const mp = !paid || row.dataset.paid === paid;
    const ml = !liq || row.dataset.liq === liq;
    const mpm = !payment || row.dataset.payment === payment;
    row.style.display = (ms && mp && ml && mpm) ? '' : 'none';
  });
}

function filterInv() {"""

if OLD_FILTER_FN in invoice:
    invoice = invoice.replace(OLD_FILTER_FN, NEW_FILTER_FN)
    print("✅ Fix 3: Dodana invColFilter() JS funkcija")
else:
    print("⚠️  Fix 3: filterInv() nije pronađen za dodavanje invColFilter")

INVOICE_PATH.write_text(invoice, encoding="utf-8")
print(f"✅ invoice_list.html ažuriran")

# ═══════════════════════════════════════════════════════════════════
# PATCH — app.py: dodaj /api/pn-expenses/check-duplicate endpoint
# ═══════════════════════════════════════════════════════════════════
APP_PATH = Path("app.py")
if APP_PATH.exists():
    app = APP_PATH.read_text(encoding="utf-8")

    CHECK_DUP_ENDPOINT = '''@app.route('/api/pn-expenses/check-duplicate', methods=['GET'])
@login_required
def check_pn_expense_duplicate():
    """Provjeri postoji li trošak s istim datumom i iznosom."""
    date_val = request.args.get('date', '')
    amount_val = request.args.get('amount', '0')
    try:
        amount = float(amount_val)
    except:
        return jsonify({'found': False})
    if not date_val or amount <= 0:
        return jsonify({'found': False})
    conn = get_db()
    rows = conn.execute("""
        SELECT pe.*, ec.name as category_name
        FROM pn_expenses pe
        LEFT JOIN expense_categories ec ON ec.id = pe.category_id
        WHERE pe.doc_date = ? AND ABS(pe.amount - ?) < 0.005
        ORDER BY pe.created_at DESC
        LIMIT 5
    """, (date_val, amount)).fetchall()
    conn.close()
    if not rows:
        return jsonify({'found': False})
    return jsonify({'found': True, 'expenses': rows_to_dicts(rows)})


'''

    # Dodaj ispred check-duplicate markera ili ispred calculate_dnevnice
    DUP_MARKER = "@app.route('/api/pn-expenses/check-duplicate'"
    CALC_MARKER = "@app.route('/api/calculate_dnevnice', methods=['POST'])"

    if DUP_MARKER in app:
        print("ℹ️  app.py: check-duplicate endpoint već postoji")
    elif CALC_MARKER in app:
        app = app.replace(CALC_MARKER, CHECK_DUP_ENDPOINT + CALC_MARKER)
        APP_PATH.write_text(app, encoding="utf-8")
        print("✅ app.py: Dodan /api/pn-expenses/check-duplicate endpoint")
    else:
        print("⚠️  app.py: Nije pronađen marker za dodavanje check-duplicate endpointa")
else:
    print("⚠️  app.py nije pronađen — check-duplicate endpoint nije dodan")

print("""
✅ SVE GOTOVO!

Sažetak promjena:
  1. PN select (Neupareni troškovi + Unos troška) — prikazuje datum: PN 2026-14 [07.03.2026.]
  2. Unos troška — upozorenje ako postoji isti datum + iznos
  3. Ulazni računi — filter po svakoj koloni (Broj, Partner, OIB, Datum, Dospijeće, Korisnik)
  4. Unos troška — kategorija je obavezno polje (crveni border + toast)

Restart:
  Ctrl+C pa python app.py
""")
