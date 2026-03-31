#!/usr/bin/env python3
"""
fix_invoice_sort_v2.py
Dodaje sortiranje po kolonama u invoice_list.html.
Radi direktno na lokalnoj datoteci bez ovisnosti o GitHub verziji.

Pokreni iz korijena projekta:
    python fix_invoice_sort_v2.py
"""

import shutil, re
from pathlib import Path

INVOICE_PATH = Path("templates/invoice_list.html")

if not INVOICE_PATH.exists():
    print(f"❌ Nije pronađeno: {INVOICE_PATH}")
    exit(1)

shutil.copy2(INVOICE_PATH, INVOICE_PATH.with_suffix(".html.bak_sortv2"))
print("✅ Backup kreiran")

invoice = INVOICE_PATH.read_text(encoding="utf-8")

# ── Provjeri je li sort već dodan ────────────────────────────────────────────
if 'invSort(' in invoice:
    print("ℹ️  Sort je već dodan u datoteku.")
    exit(0)

# ── 1. Zamijeni thead regex-om (fleksibilno prema whitespace razlikama) ──────
OLD_THEAD_PATTERN = r'(<thead>\s*<tr>\s*)<th[^>]*></th>\s*<th[^>]*>Broj računa</th>\s*<th[^>]*>Partner</th>\s*<th[^>]*>OIB</th>\s*<th[^>]*>Iznos</th>\s*<th[^>]*>Datum</th>\s*<th[^>]*>Dospije[^<]*</th>\s*<th[^>]*>Pla[^<]*</th>\s*<th[^>]*>Likvidirano</th>\s*<th[^>]*>.*?</th>\s*<th[^>]*>Korisnik</th>\s*<th[^>]*>Akcije</th>\s*</tr>'

NEW_THEAD = '''<thead>
        <tr>
          <th style="width:32px;"></th>
          <th class="inv-sortable" data-col="broj" style="width:120px;cursor:pointer;user-select:none;white-space:nowrap;" onclick="invSort('broj')">Broj računa <span class="inv-si" id="inv-si-broj">↕</span></th>
          <th class="inv-sortable" data-col="partner" style="cursor:pointer;user-select:none;" onclick="invSort('partner')">Partner <span class="inv-si" id="inv-si-partner">↕</span></th>
          <th class="inv-sortable" data-col="oib" style="width:95px;cursor:pointer;user-select:none;" onclick="invSort('oib')">OIB <span class="inv-si" id="inv-si-oib">↕</span></th>
          <th class="inv-sortable" data-col="iznos" style="text-align:right;width:90px;cursor:pointer;user-select:none;" onclick="invSort('iznos')">Iznos <span class="inv-si" id="inv-si-iznos">↕</span></th>
          <th class="inv-sortable" data-col="datum" style="width:88px;cursor:pointer;user-select:none;" onclick="invSort('datum')">Datum <span class="inv-si" id="inv-si-datum">↕</span></th>
          <th class="inv-sortable" data-col="dospijece" style="width:88px;cursor:pointer;user-select:none;" onclick="invSort('dospijece')">Dospijeće <span class="inv-si" id="inv-si-dospijece">↕</span></th>
          <th class="inv-sortable" data-col="placeno" style="text-align:center;width:72px;cursor:pointer;user-select:none;" onclick="invSort('placeno')">Plaćeno <span class="inv-si" id="inv-si-placeno">↕</span></th>
          <th class="inv-sortable" data-col="likvidirano" style="text-align:center;width:82px;cursor:pointer;user-select:none;" onclick="invSort('likvidirano')">Likvidirano <span class="inv-si" id="inv-si-likvidirano">↕</span></th>
          <th style="width:32px;text-align:center;" title="Napomena">💬</th>
          <th style="width:75px;">Korisnik</th>
          <th style="width:100px;">Akcije</th>
        </tr>
      </thead>'''

match = re.search(OLD_THEAD_PATTERN, invoice, re.DOTALL)
if match:
    invoice = invoice[:match.start()] + NEW_THEAD + invoice[match.end():]
    print("✅ thead zamijenjen (regex)")
else:
    # Fallback: jednostavna zamjena teksta za najčešći slučaj
    simple_old = '<th style="width:120px;">Broj računa</th>'
    simple_new = '<th class="inv-sortable" data-col="broj" style="width:120px;cursor:pointer;user-select:none;white-space:nowrap;" onclick="invSort(\'broj\')">Broj računa <span class="inv-si" id="inv-si-broj">↕</span></th>'
    if simple_old in invoice:
        invoice = invoice.replace('<th style="width:120px;">Broj računa</th>', simple_new)
        invoice = invoice.replace('<th>Partner</th>', '<th class="inv-sortable" data-col="partner" style="cursor:pointer;user-select:none;" onclick="invSort(\'partner\')">Partner <span class="inv-si" id="inv-si-partner">↕</span></th>')
        invoice = invoice.replace('<th style="width:95px;">OIB</th>', '<th class="inv-sortable" data-col="oib" style="width:95px;cursor:pointer;user-select:none;" onclick="invSort(\'oib\')">OIB <span class="inv-si" id="inv-si-oib">↕</span></th>')
        invoice = invoice.replace('<th style="text-align:right;width:90px;">Iznos</th>', '<th class="inv-sortable" data-col="iznos" style="text-align:right;width:90px;cursor:pointer;user-select:none;" onclick="invSort(\'iznos\')">Iznos <span class="inv-si" id="inv-si-iznos">↕</span></th>')
        invoice = invoice.replace('<th style="width:88px;">Datum</th>', '<th class="inv-sortable" data-col="datum" style="width:88px;cursor:pointer;user-select:none;" onclick="invSort(\'datum\')">Datum <span class="inv-si" id="inv-si-datum">↕</span></th>')
        invoice = invoice.replace('<th style="width:88px;">Dospijeće</th>', '<th class="inv-sortable" data-col="dospijece" style="width:88px;cursor:pointer;user-select:none;" onclick="invSort(\'dospijece\')">Dospijeće <span class="inv-si" id="inv-si-dospijece">↕</span></th>')
        invoice = invoice.replace('<th style="text-align:center;width:72px;">Plaćeno</th>', '<th class="inv-sortable" data-col="placeno" style="text-align:center;width:72px;cursor:pointer;user-select:none;" onclick="invSort(\'placeno\')">Plaćeno <span class="inv-si" id="inv-si-placeno">↕</span></th>')
        invoice = invoice.replace('<th style="text-align:center;width:82px;">Likvidirano</th>', '<th class="inv-sortable" data-col="likvidirano" style="text-align:center;width:82px;cursor:pointer;user-select:none;" onclick="invSort(\'likvidirano\')">Likvidirano <span class="inv-si" id="inv-si-likvidirano">↕</span></th>')
        print("✅ thead zamijenjen (zamjena po th elementima)")
    else:
        print("⚠️  Thead nije pronađen — ispisujem prvih 200 znakova thead bloka:")
        idx = invoice.find('<thead>')
        if idx >= 0:
            print(invoice[idx:idx+400])
        exit(1)

# ── 2. Dodaj data-* atribute na <tr> u tbody ─────────────────────────────────
# Tražimo <tr data-id="{{ inv.id }}" i dodajemo data atribute
OLD_TR = 'data-payment="{{ inv.paid_card_last4 or \'\' }}"'
NEW_TR = '''data-payment="{{ inv.paid_card_last4 or '' }}"
            data-broj="{{ inv.invoice_number or '' }}"
            data-partner="{{ inv.partner_name or '' }}"
            data-oib="{{ inv.partner_oib or '' }}"
            data-iznos="{{ inv.amount_total or 0 }}"
            data-datum="{{ inv.invoice_date or '' }}"
            data-dospijece="{{ inv.due_date or '' }}"
            data-placeno="{{ inv.is_paid or 0 }}"
            data-likvidirano="{{ inv.is_liquidated or 0 }}"'''

if OLD_TR in invoice and 'data-iznos' not in invoice:
    invoice = invoice.replace(OLD_TR, NEW_TR)
    print("✅ tbody tr: Dodani data-* atributi")
elif 'data-iznos' in invoice:
    print("ℹ️  data-* atributi već postoje")
else:
    print("⚠️  <tr> pattern nije pronađen")

# ── 3. Dodaj CSS + JS sort na kraj (ispred zadnjeg {% endblock %}) ────────────
SORT_CODE = """
<style>
.inv-sortable { cursor:pointer; user-select:none; }
.inv-sortable:hover { background: var(--gray-100); }
.inv-si { font-size:10px; color:var(--gray-400); margin-left:2px; }
.inv-sort-asc .inv-si, .inv-sort-desc .inv-si { color:var(--accent); }
</style>

<script>
let _invSortCol = 'datum';
let _invSortDir = -1;

function invSort(col) {
  if (_invSortCol === col) {
    _invSortDir *= -1;
  } else {
    _invSortCol = col;
    _invSortDir = ['datum','dospijece','iznos'].includes(col) ? -1 : 1;
  }

  // Ikone
  document.querySelectorAll('.inv-sortable').forEach(th => {
    th.classList.remove('inv-sort-asc','inv-sort-desc');
  });
  document.querySelectorAll('.inv-si').forEach(el => el.textContent = '↕');
  const activeTh = document.querySelector('.inv-sortable[data-col="' + col + '"]');
  if (activeTh) {
    activeTh.classList.add(_invSortDir === 1 ? 'inv-sort-asc' : 'inv-sort-desc');
    const si = document.getElementById('inv-si-' + col);
    if (si) si.textContent = _invSortDir === 1 ? '▲' : '▼';
  }

  const tbody = document.getElementById('inv-tbody');
  if (!tbody) return;
  const rows = Array.from(tbody.querySelectorAll('tr[data-id]'));

  rows.sort((a, b) => {
    let av = (a.dataset[_invSortCol] || '').trim();
    let bv = (b.dataset[_invSortCol] || '').trim();

    if (['iznos','placeno','likvidirano'].includes(_invSortCol)) {
      return (parseFloat(av||0) - parseFloat(bv||0)) * _invSortDir;
    }

    if (['datum','dospijece'].includes(_invSortCol)) {
      const toIso = v => {
        if (!v || v==='—') return '';
        const m = v.match(/^(\\d{1,2})[\\.\\-](\\d{1,2})[\\.\\-](\\d{4})/);
        return m ? m[3]+'-'+m[2].padStart(2,'0')+'-'+m[1].padStart(2,'0') : v.substring(0,10);
      };
      av = toIso(av); bv = toIso(bv);
      if (!av && !bv) return 0;
      if (!av) return _invSortDir;
      if (!bv) return -_invSortDir;
      return av.localeCompare(bv) * _invSortDir;
    }

    if (!av && !bv) return 0;
    if (!av) return _invSortDir;
    if (!bv) return -_invSortDir;
    return av.localeCompare(bv, 'hr') * _invSortDir;
  });

  rows.forEach(r => tbody.appendChild(r));
}

document.addEventListener('DOMContentLoaded', () => { invSort('datum'); });
</script>
"""

# Dodaj ispred zadnjeg {% endblock %}
last_endblock = invoice.rfind('{% endblock %}')
if last_endblock >= 0:
    invoice = invoice[:last_endblock] + SORT_CODE + '\n' + invoice[last_endblock:]
    print("✅ CSS + JS sort dodan")
else:
    invoice += SORT_CODE
    print("✅ CSS + JS sort dodan (fallback)")

INVOICE_PATH.write_text(invoice, encoding="utf-8")
print(f"\n✅ invoice_list.html ažuriran — refresh stranice (bez restarta app.py)")
