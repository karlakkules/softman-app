#!/usr/bin/env python3
"""
fix_client_dropdown_v4.py

Korijen problema: inline event handleri (onmouseenter, onmousedown)
u innerHTML stringu ne rade pouzdano u svim browserima.

Rješenje: event delegation — jedan listener na dropdown containeru,
data-name i data-id atributi na opcijama, bez ijednog inline handlera.

Pokretanje:
    cd ~/Projects/Softman_app
    python3 fix_client_dropdown_v4.py
"""

import shutil, os, re

BASE   = os.path.dirname(os.path.abspath(__file__))
ORDERS = os.path.join(BASE, 'templates', 'orders.html')
FORM   = os.path.join(BASE, 'templates', 'form.html')

def read(p):
    with open(p, encoding='utf-8') as f: return f.read()

def write(p, c):
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def backup(p):
    shutil.copy2(p, p + '.bak_v4')
    print(f"  Backup → {p}.bak_v4")


# ─────────────────────────────────────────────────────────────────────────────
# ORDERS.HTML — novi q-client JS (event delegation)
# ─────────────────────────────────────────────────────────────────────────────

NEW_Q_CLIENT_JS = """\
// ── Quick modal — client dropdown ─────────────────────────────────────────
const _qClients = {{ clients_all | tojson }};

function showQClientDropdown() {
  filterQClientDropdown();
  document.getElementById('q-client-dropdown').style.display = 'block';
}
function hideQClientDropdown() {
  document.getElementById('q-client-dropdown').style.display = 'none';
}
function hideQClientDropdownDelayed() {
  setTimeout(hideQClientDropdown, 200);
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
    html += `<div class="qc-opt" data-name="interno" data-id="0"
      style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);background:#f5f9ff;">
      <div style="font-weight:700;color:var(--navy);">Interno</div>
    </div>`;
  }
  html += filtered.map(c => `
    <div class="qc-opt" data-name=${JSON.stringify(c.name)} data-id="${c.id}"
      style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);">
      <div style="font-weight:600;color:var(--navy);">${c.name}</div>
      ${c.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${c.oib}${c.address ? ' · '+c.address : ''}</div>` : ''}
    </div>`).join('');
  if (!html) {
    html = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
  }
  list.innerHTML = html;
  list.style.display = 'block';
}
// Event delegation — jedan listener, bez inline handlera
document.addEventListener('DOMContentLoaded', function() {
  const qDrop = document.getElementById('q-client-dropdown');
  if (!qDrop) return;
  // Hover
  qDrop.addEventListener('mouseover', function(e) {
    const opt = e.target.closest('.qc-opt');
    if (opt) { qDrop.querySelectorAll('.qc-opt').forEach(o => o.style.background = ''); opt.style.background = 'var(--accent-light)'; }
  });
  qDrop.addEventListener('mouseout', function(e) {
    const opt = e.target.closest('.qc-opt');
    if (opt) opt.style.background = opt.dataset.id === '0' ? '#f5f9ff' : '';
  });
  // Klik — mousedown s preventDefault sprječava blur na inputu
  qDrop.addEventListener('mousedown', function(e) {
    const opt = e.target.closest('.qc-opt');
    if (!opt) return;
    e.preventDefault();
    const name = opt.dataset.name;
    const id   = opt.dataset.id;
    document.getElementById('q-client-id').value = id;
    document.getElementById('q-client').value = name;
    hideQClientDropdown();
  });
});\
"""


# ─────────────────────────────────────────────────────────────────────────────
# FORM.HTML — novi _formClients JS (event delegation)
# ─────────────────────────────────────────────────────────────────────────────

NEW_FORM_CLIENT_JS = """\
// ── Klijent/Partner searchable dropdown (form.html) ───────────────────────
const _formClients = {{ clients | tojson }};

function showFormClientDropdown() {
  filterFormClientDropdown();
  document.getElementById('form-client-dropdown').style.display = 'block';
}
function hideFormClientDropdown() {
  document.getElementById('form-client-dropdown').style.display = 'none';
}
function hideFormClientDropdownDelayed() {
  setTimeout(hideFormClientDropdown, 200);
}
function filterFormClientDropdown() {
  const q = (document.getElementById('client_info_search').value || '').toLowerCase();
  const list = document.getElementById('form-client-dropdown');
  if (!list) return;
  const filtered = _formClients.filter(c =>
    !q || c.name.toLowerCase().includes(c) ||
    (c.oib && c.oib.includes(q)) ||
    (c.address && c.address.toLowerCase().includes(q))
  );
  const internoMatch = !q || 'interno'.includes(q);
  let html = '';
  if (internoMatch) {
    html += `<div class="fc-opt" data-name="interno"
      style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);background:#f5f9ff;">
      <div style="font-weight:700;color:var(--navy);">Interno</div>
    </div>`;
  }
  html += filtered.map(c => `
    <div class="fc-opt" data-name=${JSON.stringify(c.name)}
      style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);">
      <div style="font-weight:600;color:var(--navy);">${c.name}</div>
      ${c.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${c.oib}${c.address ? ' · '+c.address : ''}</div>` : ''}
    </div>`).join('');
  if (!html) {
    html = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
  }
  list.innerHTML = html;
  list.style.display = 'block';
}
document.addEventListener('DOMContentLoaded', function() {
  const fcDrop = document.getElementById('form-client-dropdown');
  if (!fcDrop) return;
  // Hover
  fcDrop.addEventListener('mouseover', function(e) {
    const opt = e.target.closest('.fc-opt');
    if (opt) { fcDrop.querySelectorAll('.fc-opt').forEach(o => o.style.background = ''); opt.style.background = 'var(--accent-light)'; }
  });
  fcDrop.addEventListener('mouseout', function(e) {
    const opt = e.target.closest('.fc-opt');
    if (opt) opt.style.background = opt.dataset.name === 'interno' ? '#f5f9ff' : '';
  });
  // Klik
  fcDrop.addEventListener('mousedown', function(e) {
    const opt = e.target.closest('.fc-opt');
    if (!opt) return;
    e.preventDefault();
    const name = opt.dataset.name;
    document.getElementById('client_info').value = name;
    document.getElementById('client_info_search').value = name;
    hideFormClientDropdown();
  });
  // Zatvori kad klik van
  document.addEventListener('click', function(e) {
    const search = document.getElementById('client_info_search');
    if (fcDrop && search && !search.contains(e.target) && !fcDrop.contains(e.target)) {
      hideFormClientDropdown();
    }
  });
});\
"""


def patch_orders():
    content = read(ORDERS)

    pattern = re.compile(
        r'// ── Quick modal — client dropdown.*?'
        r'(?=\n// ═|$)',
        re.DOTALL
    )
    m = pattern.search(content)
    if not m:
        # Širi fallback
        pattern2 = re.compile(
            r'(?:const _qClients|// ── Quick modal — client).*?'
            r'function selectQClient\([^)]*\)\s*\{[^}]*\}',
            re.DOTALL
        )
        m = pattern2.search(content)
        if not m:
            print("GREŠKA orders.html: Ne mogu pronaći q-client blok.")
            return False

    backup(ORDERS)
    content = content[:m.start()] + NEW_Q_CLIENT_JS + '\n\n' + content[m.end():]
    write(ORDERS, content)
    print("OK: orders.html — q-client dropdown zamijenjen (event delegation).")
    return True


def patch_form():
    content = read(FORM)

    # Ima li već novi kod?
    if '_formClients' in content:
        pattern = re.compile(
            r'// ── Klijent/Partner searchable dropdown.*?'
            r'(?=\n</script>|\Z)',
            re.DOTALL
        )
        m = pattern.search(content)
        if m:
            backup(FORM)
            content = content[:m.start()] + NEW_FORM_CLIENT_JS + '\n' + content[m.end():]
            write(FORM, content)
            print("OK: form.html — _formClients dropdown zamijenjen (event delegation).")
            return True
        print("UPOZORENJE form.html: _formClients postoji ali blok nije pronađen — dodajem na kraj.")

    # Dodaj prije zadnjeg </script>
    endblock = content.rfind('{% endblock %}')
    script_end = content.rfind('</script>', 0, endblock)
    if script_end == -1:
        print("GREŠKA form.html: Nema </script> taga.")
        return False
    backup(FORM)
    content = content[:script_end] + '\n' + NEW_FORM_CLIENT_JS + '\n' + content[script_end:]
    write(FORM, content)
    print("OK: form.html — _formClients dropdown dodan (event delegation).")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("fix_client_dropdown_v4.py")
    print("=" * 60)
    r1 = patch_orders()
    r2 = patch_form()
    print()
    if r1 and r2:
        print("✅ Gotovo — restartaj Flask i testiraj.")
    else:
        print("⚠️  Neke promjene nisu primijenjene.")
