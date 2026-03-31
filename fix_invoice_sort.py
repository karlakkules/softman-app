#!/usr/bin/env python3
"""
fix_invoice_sort.py
Dodaje sortiranje po kolonama u formu Ulazni računi.
Kolone: Broj računa, Partner, OIB, Iznos, Datum, Dospijeće, Plaćeno, Likvidirano

Pokreni iz korijena projekta:
    python fix_invoice_sort.py
"""

import shutil
from pathlib import Path

INVOICE_PATH = Path("templates/invoice_list.html")

if not INVOICE_PATH.exists():
    print(f"❌ Nije pronađeno: {INVOICE_PATH}")
    exit(1)

shutil.copy2(INVOICE_PATH, INVOICE_PATH.with_suffix(".html.bak_sort"))
print("✅ Backup kreiran (.bak_sort)")

invoice = INVOICE_PATH.read_text(encoding="utf-8")

# ── 1. Zamijeni thead — dodaj sortable klase i data-col atribute ─────────────
OLD_THEAD = """      <thead>
        <tr>
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

NEW_THEAD = """      <thead>
        <tr>
          <th style="width:32px;"></th>
          <th class="inv-sortable" data-col="broj" style="width:120px;cursor:pointer;user-select:none;" onclick="invSort('broj')">Broj računa <span class="inv-sort-icon" id="inv-sort-broj">↕</span></th>
          <th class="inv-sortable" data-col="partner" style="cursor:pointer;user-select:none;" onclick="invSort('partner')">Partner <span class="inv-sort-icon" id="inv-sort-partner">↕</span></th>
          <th class="inv-sortable" data-col="oib" style="width:95px;cursor:pointer;user-select:none;" onclick="invSort('oib')">OIB <span class="inv-sort-icon" id="inv-sort-oib">↕</span></th>
          <th class="inv-sortable" data-col="iznos" style="text-align:right;width:90px;cursor:pointer;user-select:none;" onclick="invSort('iznos')">Iznos <span class="inv-sort-icon" id="inv-sort-iznos">↕</span></th>
          <th class="inv-sortable" data-col="datum" style="width:88px;cursor:pointer;user-select:none;" onclick="invSort('datum')">Datum <span class="inv-sort-icon" id="inv-sort-datum">↕</span></th>
          <th class="inv-sortable" data-col="dospijece" style="width:88px;cursor:pointer;user-select:none;" onclick="invSort('dospijece')">Dospijeće <span class="inv-sort-icon" id="inv-sort-dospijece">↕</span></th>
          <th class="inv-sortable" data-col="placeno" style="text-align:center;width:72px;cursor:pointer;user-select:none;" onclick="invSort('placeno')">Plaćeno <span class="inv-sort-icon" id="inv-sort-placeno">↕</span></th>
          <th class="inv-sortable" data-col="likvidirano" style="text-align:center;width:82px;cursor:pointer;user-select:none;" onclick="invSort('likvidirano')">Likvidirano <span class="inv-sort-icon" id="inv-sort-likvidirano">↕</span></th>
          <th style="width:32px;text-align:center;" title="Napomena">💬</th>
          <th style="width:75px;">Korisnik</th>
          <th style="width:100px;">Akcije</th>
        </tr>
      </thead>"""

if OLD_THEAD in invoice:
    invoice = invoice.replace(OLD_THEAD, NEW_THEAD)
    print("✅ thead: Dodane sortable kolone")
else:
    print("⚠️  thead: Pattern nije pronađen — provjeri ručno")

# ── 2. Dodaj data-* atribute na <tr> redove (za sort logiku) ────────────────
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
            data-iznos="{{ inv.amount_total or 0 }}"
            data-datum="{{ inv.invoice_date or '' }}"
            data-dospijece="{{ inv.due_date or '' }}"
            data-placeno="{{ inv.is_paid or 0 }}"
            data-likvidirano="{{ inv.is_liquidated or 0 }}"
            style="cursor:pointer;"
            ondblclick="if(!event.target.closest('button,a,input')) openEditModal(this)">"""

if OLD_TR in invoice:
    invoice = invoice.replace(OLD_TR, NEW_TR)
    print("✅ tbody tr: Dodani data-* atributi za sortiranje")
else:
    print("⚠️  tbody tr: Pattern nije pronađen — provjeri ručno")

# ── 3. Dodaj CSS + JS za sortiranje ispred </script> ────────────────────────
SORT_CSS_JS = """
<style>
.inv-sortable:hover { background: var(--gray-100); }
.inv-sort-icon { font-size: 10px; color: var(--gray-400); margin-left: 3px; }
.inv-sort-asc .inv-sort-icon  { color: var(--accent); }
.inv-sort-desc .inv-sort-icon { color: var(--accent); }
</style>
<script>
// ── Invoice sort ─────────────────────────────────────────────────────────────
let _invSortCol = 'datum';
let _invSortDir = -1; // -1 = desc (noviji gore), 1 = asc

function invSort(col) {
  if (_invSortCol === col) {
    _invSortDir *= -1;
  } else {
    _invSortCol = col;
    // Datumi i iznos — desc po defaultu, ostalo asc
    _invSortDir = ['datum','dospijece','iznos'].includes(col) ? -1 : 1;
  }

  // Ažuriraj ikone
  document.querySelectorAll('.inv-sortable').forEach(th => {
    th.classList.remove('inv-sort-asc', 'inv-sort-desc');
    const icon = th.querySelector('.inv-sort-icon');
    if (icon) icon.textContent = '↕';
  });
  const activeTh = document.querySelector(`.inv-sortable[data-col="${col}"]`);
  if (activeTh) {
    activeTh.classList.add(_invSortDir === 1 ? 'inv-sort-asc' : 'inv-sort-desc');
    const icon = activeTh.querySelector('.inv-sort-icon');
    if (icon) icon.textContent = _invSortDir === 1 ? '▲' : '▼';
  }

  const tbody = document.getElementById('inv-tbody');
  const rows = Array.from(tbody.querySelectorAll('tr[data-id]'));

  rows.sort((a, b) => {
    let aVal = (a.dataset[_invSortCol] || '').trim();
    let bVal = (b.dataset[_invSortCol] || '').trim();

    // Numeričke kolone
    if (['iznos','placeno','likvidirano'].includes(_invSortCol)) {
      return (parseFloat(aVal || 0) - parseFloat(bVal || 0)) * _invSortDir;
    }

    // Datum kolone — YYYY-MM-DD ili DD.MM.YYYY. format
    if (['datum','dospijece'].includes(_invSortCol)) {
      // Konvertiraj DD.MM.YYYY. u YYYY-MM-DD za usporedbu
      const toIso = v => {
        if (!v || v === '—') return '';
        const m = v.match(/^(\d{2})\.(\d{2})\.(\d{4})/);
        return m ? `${m[3]}-${m[2]}-${m[1]}` : v.substring(0, 10);
      };
      aVal = toIso(aVal);
      bVal = toIso(bVal);
      if (!aVal && !bVal) return 0;
      if (!aVal) return 1;
      if (!bVal) return -1;
      return aVal.localeCompare(bVal) * _invSortDir;
    }

    // Tekstualne kolone
    if (!aVal && !bVal) return 0;
    if (!aVal) return 1 * _invSortDir;
    if (!bVal) return -1 * _invSortDir;
    return aVal.localeCompare(bVal, 'hr') * _invSortDir;
  });

  rows.forEach(row => tbody.appendChild(row));
}

// Inicijalni sort po datumu desc (najnoviji gore) — pozovi kad se stranica učita
document.addEventListener('DOMContentLoaded', () => {
  invSort('datum');
});
</script>
"""

# Dodaj ispred {% endblock %} na kraju
END_BLOCK = "{% endblock %}"
# Pronađi zadnji {% endblock %}
last_endblock_idx = invoice.rfind(END_BLOCK)

if last_endblock_idx >= 0:
    invoice = invoice[:last_endblock_idx] + SORT_CSS_JS + "\n" + invoice[last_endblock_idx:]
    print("✅ CSS + JS za sortiranje dodan na kraj datoteke")
else:
    invoice += SORT_CSS_JS
    print("✅ CSS + JS za sortiranje dodan (fallback — na kraj datoteke)")

INVOICE_PATH.write_text(invoice, encoding="utf-8")
print(f"\n✅ invoice_list.html ažuriran")
print("""
Što je dodano:
  - Klik na zaglavlje kolone sortira tablicu (▲ asc / ▼ desc)
  - Sortabilne kolone: Broj računa, Partner, OIB, Iznos, Datum, Dospijeće, Plaćeno, Likvidirano
  - Inicijalni sort: Datum descending (najnoviji gore)
  - Datumi se ispravno uspoređuju bez obzira na DD.MM.YYYY. format

Restart: Ctrl+C pa python app.py
""")
