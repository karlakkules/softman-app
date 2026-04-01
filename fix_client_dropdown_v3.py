#!/usr/bin/env python3
"""
fix_client_dropdown_v3.py

Popravlja bug gdje odabir klijenta iz dropdown liste prikazuje tekst filtera
umjesto odabranog klijenta.

Rješenje: flag-based pristup koji je cross-browser siguran.
  _qClientSelecting = true  →  postavlja se na mouseenter/pointerenter opcije
  onblur provjerava flag i ne resetira vrijednost

Primjenjuje fix na:
  - orders.html  (brzi unos, q-client)
  - form.html    (novi nalog, client_info_search)

Pokretanje:
    cd ~/Projects/Softman_app
    python3 fix_client_dropdown_v3.py
"""

import shutil, os, re

BASE   = os.path.dirname(os.path.abspath(__file__))
ORDERS = os.path.join(BASE, 'templates', 'orders.html')
FORM   = os.path.join(BASE, 'templates', 'form.html')

def read(p):
    with open(p, encoding='utf-8') as f: return f.read()

def write(p, c):
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def backup(p, suffix='.bak_v3'):
    shutil.copy2(p, p + suffix)
    print(f"  Backup → {p + suffix}")


# ─────────────────────────────────────────────────────────────────────────────
# Novi JS blok za orders.html — zamjenjuje cijeli q-client dropdown kod
# ─────────────────────────────────────────────────────────────────────────────

NEW_Q_CLIENT_JS = """\
// ── Quick modal — client dropdown ─────────────────────────────────────────
const _qClients = {{ clients_all | tojson }};
let _qClientSelecting = false;

function showQClientDropdown() {
  filterQClientDropdown();
  document.getElementById('q-client-dropdown').style.display = 'block';
}
function hideQClientDropdown() {
  document.getElementById('q-client-dropdown').style.display = 'none';
}
function hideQClientDropdownDelayed() {
  setTimeout(function() {
    if (!_qClientSelecting) hideQClientDropdown();
  }, 150);
}
function filterQClientDropdown() {
  const q = (document.getElementById('q-client').value || '').toLowerCase();
  const list = document.getElementById('q-client-dropdown');
  if (!list) return;
  const filtered = _qClients.filter(c =>
    !q || c.name.toLowerCase().includes(q) ||
    (c.oib && c.oib.includes(q)) ||
    (c.address && c.address.toLowerCase().includes(q))
  );
  const internoMatch = !q || 'interno'.includes(q);
  let html = '';
  if (internoMatch) {
    html += `<div class="q-client-option" style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);background:#f5f9ff;"
      onmouseenter="_qClientSelecting=true" onmouseleave="_qClientSelecting=false"
      onmousedown="event.preventDefault();selectQClient(0,'interno');"
      onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background='#f5f9ff'">
      <div style="font-weight:700;color:var(--navy);">Interno</div>
    </div>`;
  }
  if (filtered.length) {
    html += filtered.map(c => `
      <div class="q-client-option" style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);"
        onmouseenter="_qClientSelecting=true" onmouseleave="_qClientSelecting=false"
        onmousedown="event.preventDefault();selectQClient(${c.id},${JSON.stringify(c.name)});"
        onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background=''">
        <div style="font-weight:600;color:var(--navy);">${c.name}</div>
        ${c.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${c.oib}${c.address ? ' · '+c.address : ''}</div>` : ''}
      </div>`).join('');
  }
  if (!html) {
    html = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
  }
  list.innerHTML = html;
  list.style.display = 'block';
}
function selectQClient(id, name) {
  _qClientSelecting = false;
  document.getElementById('q-client-id').value = id;
  document.getElementById('q-client').value = name;
  hideQClientDropdown();
}"""


# ─────────────────────────────────────────────────────────────────────────────
# Novi JS blok za form.html — zamjenjuje _formClients dropdown kod
# ─────────────────────────────────────────────────────────────────────────────

NEW_FORM_CLIENT_JS = """\
// ── Klijent/Partner searchable dropdown (form.html) ───────────────────────
const _formClients = {{ clients | tojson }};
let _formClientSelecting = false;

function showFormClientDropdown() {
  filterFormClientDropdown();
  document.getElementById('form-client-dropdown').style.display = 'block';
}
function hideFormClientDropdown() {
  document.getElementById('form-client-dropdown').style.display = 'none';
}
function hideFormClientDropdownDelayed() {
  setTimeout(function() {
    if (!_formClientSelecting) hideFormClientDropdown();
  }, 150);
}
function filterFormClientDropdown() {
  const q = (document.getElementById('client_info_search').value || '').toLowerCase();
  const list = document.getElementById('form-client-dropdown');
  if (!list) return;
  const filtered = _formClients.filter(c =>
    !q || c.name.toLowerCase().includes(q) ||
    (c.oib && c.oib.includes(q)) ||
    (c.address && c.address.toLowerCase().includes(q))
  );
  const internoMatch = !q || 'interno'.includes(q);
  let html = '';
  if (internoMatch) {
    html += `<div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);background:#f5f9ff;"
      onmouseenter="_formClientSelecting=true" onmouseleave="_formClientSelecting=false"
      onmousedown="event.preventDefault();selectFormClient('interno');"
      onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background='#f5f9ff'">
      <div style="font-weight:700;color:var(--navy);">Interno</div>
    </div>`;
  }
  if (filtered.length) {
    html += filtered.map(c => `
      <div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);"
        onmouseenter="_formClientSelecting=true" onmouseleave="_formClientSelecting=false"
        onmousedown="event.preventDefault();selectFormClient(${JSON.stringify(c.name)});"
        onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background=''">
        <div style="font-weight:600;color:var(--navy);">${c.name}</div>
        ${c.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${c.oib}${c.address ? ' · '+c.address : ''}</div>` : ''}
      </div>`).join('');
  }
  if (!html) {
    html = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
  }
  list.innerHTML = html;
  list.style.display = 'block';
}
function selectFormClient(name) {
  _formClientSelecting = false;
  document.getElementById('client_info').value = name;
  document.getElementById('client_info_search').value = name;
  hideFormClientDropdown();
}
document.addEventListener('click', function(e) {
  const dd = document.getElementById('form-client-dropdown');
  const search = document.getElementById('client_info_search');
  if (dd && search && !search.contains(e.target) && !dd.contains(e.target)) {
    hideFormClientDropdown();
  }
});"""


def patch_orders():
    content = read(ORDERS)

    # Pronađi i zamijeni cijeli q-client JS blok
    pattern = re.compile(
        r'// ── Quick modal — client dropdown.*?'
        r'function selectQClient\([^)]*\)\s*\{[^}]*\}',
        re.DOTALL
    )
    m = pattern.search(content)
    if not m:
        print("GREŠKA orders.html: Ne mogu pronaći q-client dropdown JS blok.")
        print("  Pokušavam pronaći samo selectQClient...")
        # Fallback — zamijeni samo selectQClient + filterQClientDropdown
        pattern2 = re.compile(
            r'function filterQClientDropdown\(\).*?'
            r'function selectQClient\([^)]*\)\s*\{[^}]*\}',
            re.DOTALL
        )
        m = pattern2.search(content)
        if not m:
            print("GREŠKA orders.html: Ni fallback nije pronašao funkcije.")
            return False

    backup(ORDERS)
    content = content[:m.start()] + NEW_Q_CLIENT_JS + content[m.end():]
    write(ORDERS, content)
    print("OK: orders.html — q-client dropdown JS zamijenjen (flag fix).")
    return True


def patch_form():
    content = read(FORM)

    # Zamijeni _formClients JS blok
    pattern = re.compile(
        r'// ── Klijent/Partner searchable dropdown \(form\.html\).*?'
        r'(?=\n</script>|\n{% endblock %}|\nfunction )',
        re.DOTALL
    )
    m = pattern.search(content)
    if not m:
        print("GREŠKA form.html: Ne mogu pronaći _formClients JS blok.")
        print("  Možda fix_client_dropdown_v2.py nije bio primijenjen.")
        print("  Pokušavam dodati JS blok...")
        # Dodaj prije zadnjeg </script>
        endblock = content.rfind('{% endblock %}')
        script_end = content.rfind('</script>', 0, endblock)
        if script_end == -1:
            print("GREŠKA form.html: Nema </script> taga.")
            return False
        backup(FORM)
        content = content[:script_end] + '\n' + NEW_FORM_CLIENT_JS + '\n' + content[script_end:]
        write(FORM, content)
        print("OK: form.html — _formClients JS dodan (novi blok).")
        return True

    backup(FORM)
    content = content[:m.start()] + NEW_FORM_CLIENT_JS + '\n' + content[m.end():]
    write(FORM, content)
    print("OK: form.html — _formClients dropdown JS zamijenjen (flag fix).")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("fix_client_dropdown_v3.py")
    print("=" * 60)
    r1 = patch_orders()
    r2 = patch_form()
    print()
    if r1 and r2:
        print("✅ Gotovo — restartaj Flask i testiraj.")
        print()
        print("Kako radi fix:")
        print("  - onmouseenter opcije → _selecting = true")
        print("  - onblur input-a → sakrij dropdown SAMO ako _selecting = false")
        print("  - onmousedown opcije → preventDefault + selectClient()")
        print("  - selectClient() → _selecting = false, upiši ime, sakrij")
    else:
        print("⚠️  Neke promjene nisu primijenjene.")
