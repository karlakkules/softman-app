#!/usr/bin/env python3
"""
fix_client_dropdown_v2.py

1. form.html — zamijeni <select id="client_info"> s custom searchable dropdownom
   (input za pretragu + hidden field za vrijednost, identično brzom unosu)

2. orders.html — popravi selectQClient bug:
   - onmousedown → pointer event koji radi prije blur
   - selectQClient sprema ime u input I u hidden field ispravno

Pokretanje:
    cd ~/Projects/Softman_app
    python3 fix_client_dropdown_v2.py
"""

import shutil, os, re

BASE   = os.path.dirname(os.path.abspath(__file__))
FORM   = os.path.join(BASE, 'templates', 'form.html')
ORDERS = os.path.join(BASE, 'templates', 'orders.html')

def read(p):
    with open(p, encoding='utf-8') as f: return f.read()

def write(p, c):
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def backup(p, suffix):
    shutil.copy2(p, p + suffix)

# ─────────────────────────────────────────────────────────────────────────────
# 1. form.html — zamijeni select s custom searchable dropdownom
# ─────────────────────────────────────────────────────────────────────────────

# Novi HTML za klijent polje — identičan pattern kao brzi unos
NEW_CLIENT_FIELD = '''      <div class="form-group">
        <label class="form-label" data-hr="Klijent / Partner" data-en="Client / Partner">Klijent / Partner</label>
        <div style="position:relative;">
          <input type="text" class="form-control" id="client_info_search"
            placeholder="Pretraži klijenta..."
            autocomplete="off"
            oninput="filterFormClientDropdown()"
            onfocus="showFormClientDropdown()"
            onblur="hideFormClientDropdownDelayed()"
            value="{{ order.client_info if order else '' }}">
          <input type="hidden" id="client_info" value="{{ order.client_info if order else '' }}">
          <div id="form-client-dropdown" style="display:none;position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid var(--gray-300);border-radius:6px;box-shadow:0 4px 12px rgba(0,0,0,0.1);z-index:9999;max-height:220px;overflow-y:auto;margin-top:2px;"></div>
        </div>
      </div>'''

# Script koji ide na kraj form.html (prije </script> ili u scripts block)
FORM_CLIENT_SCRIPT = """
// ── Klijent/Partner searchable dropdown (form.html) ───────────────────────
const _formClients = {{ clients | tojson }};
function showFormClientDropdown() { filterFormClientDropdown(); document.getElementById('form-client-dropdown').style.display = 'block'; }
function hideFormClientDropdown() { document.getElementById('form-client-dropdown').style.display = 'none'; }
function hideFormClientDropdownDelayed() { setTimeout(hideFormClientDropdown, 200); }
function filterFormClientDropdown() {
  const q = (document.getElementById('client_info_search').value || '').toLowerCase();
  const list = document.getElementById('form-client-dropdown');
  if (!list) return;
  const filtered = _formClients.filter(c => !q || c.name.toLowerCase().includes(q) || (c.oib && c.oib.includes(q)) || (c.address && c.address.toLowerCase().includes(q)));
  const internoMatch = !q || 'interno'.includes(q);
  let html = '';
  if (internoMatch) {
    html += `<div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);background:#f5f9ff;"
      onpointerdown="event.preventDefault();selectFormClient('interno');"
      onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background='#f5f9ff'">
      <div style="font-weight:700;color:var(--navy);">Interno</div>
    </div>`;
  }
  if (filtered.length) {
    html += filtered.map(c => `
      <div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);"
        onpointerdown="event.preventDefault();selectFormClient(${JSON.stringify(c.name)});"
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
  document.getElementById('client_info').value = name;
  document.getElementById('client_info_search').value = name;
  hideFormClientDropdown();
}
// Zatvori dropdown kad klik van
document.addEventListener('click', function(e) {
  const dd = document.getElementById('form-client-dropdown');
  const search = document.getElementById('client_info_search');
  if (dd && search && !search.contains(e.target) && !dd.contains(e.target)) {
    hideFormClientDropdown();
  }
});
"""

def patch_form():
    content = read(FORM)

    # ── Zamijeni select (ili stari input+datalist) s novim custom dropdownom ──
    # Pronađi po id="client_info" — može biti select ili input
    # Regex koji hvata cijeli form-group blok koji sadrži client_info
    pattern = re.compile(
        r'<div class="form-group">\s*'
        r'<label[^>]*>Klijent / Partner</label>\s*'
        r'(?:'
            r'<select[^>]*id="client_info"[^>]*>.*?</select>'  # select varijanta
            r'|'
            r'<input[^>]*id="client_info"[^>]*>.*?(?:<datalist.*?</datalist>)?'  # input varijanta
            r'|'
            r'<div[^>]*>.*?</div>'  # custom dropdown varijanta
        r')\s*'
        r'</div>',
        re.DOTALL
    )

    if 'id="client_info_search"' in content:
        print("INFO: Searchable dropdown u form.html već postoji — preskačem HTML.")
    else:
        match = pattern.search(content)
        if not match:
            print("GREŠKA: Ne mogu pronaći Klijent/Partner blok u form.html.")
            return False
        content = content[:match.start()] + NEW_CLIENT_FIELD + content[match.end():]
        print("OK: Klijent/Partner polje u form.html zamijenjeno searchable dropdownom.")

    # ── Dodaj JS skriptu ──
    if '_formClients' in content:
        print("INFO: JS za form client dropdown već postoji — preskačem.")
    else:
        # Umetni prije zatvaranja </script> taga u scripts bloku
        # ili prije {% endblock %}
        if '{% endblock %}' in content:
            # Nađi zadnji </script> prije {% endblock %}
            endblock_pos = content.rfind('{% endblock %}')
            script_end = content.rfind('</script>', 0, endblock_pos)
            if script_end != -1:
                content = content[:script_end] + FORM_CLIENT_SCRIPT + content[script_end:]
                print("OK: JS za form client dropdown dodan u form.html.")
            else:
                # Dodaj novi script tag
                content = content[:endblock_pos] + '<script>' + FORM_CLIENT_SCRIPT + '</script>\n' + content[endblock_pos:]
                print("OK: JS za form client dropdown dodan u form.html (novi script tag).")
        else:
            print("GREŠKA: Ne mogu pronaći {% endblock %} u form.html.")
            return False

    backup(FORM, '.bak_clientv2')
    write(FORM, content)
    print("OK: form.html ažuriran.")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 2. orders.html — popravi selectQClient (onmousedown → onpointerdown + preventDefault)
# ─────────────────────────────────────────────────────────────────────────────

def patch_orders():
    content = read(ORDERS)

    # Bug: onmousedown na div ne poziva preventDefault pa blur ukrade fokus
    # i oninput resetira display vrijednost. Koristimo onpointerdown + preventDefault.
    # Zamijeni cijelu filterQClientDropdown + selectQClient funkciju

    old_pattern = re.compile(
        r'function filterQClientDropdown\(\).*?'
        r'function selectQClient\([^)]*\)\s*\{[^\}]*\}',
        re.DOTALL
    )

    NEW_Q_CLIENT_FUNCS = """function filterQClientDropdown() {
  const q = (document.getElementById('q-client').value || '').toLowerCase();
  const list = document.getElementById('q-client-dropdown');
  if (!list) return;
  const filtered = _qClients.filter(c => !q || c.name.toLowerCase().includes(q) || (c.oib && c.oib.includes(q)) || (c.address && c.address.toLowerCase().includes(q)));
  const internoMatch = !q || 'interno'.includes(q);
  let html = '';
  if (internoMatch) {
    html += `<div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);background:#f5f9ff;"
      onpointerdown="event.preventDefault();selectQClient(0, 'interno');"
      onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background='#f5f9ff'">
      <div style="font-weight:700;color:var(--navy);">Interno</div>
    </div>`;
  }
  if (filtered.length) {
    html += filtered.map(c => `
      <div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);"
        onpointerdown="event.preventDefault();selectQClient(${c.id}, ${JSON.stringify(c.name)});"
        onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background=''">
        <div style="font-weight:600;color:var(--navy);">${c.name}</div>
        ${c.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${c.oib}${c.address ? ' · '+c.address : ''}</div>` : ''}
      </div>`).join('');
  }
  if (!html) {
    list.innerHTML = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
    list.style.display = 'block'; return;
  }
  list.innerHTML = html;
  list.style.display = 'block';
}
function selectQClient(id, name) {
  document.getElementById('q-client-id').value = id;
  document.getElementById('q-client').value = name;
  hideQClientDropdown();
}"""

    match = old_pattern.search(content)
    if not match:
        print("GREŠKA: Ne mogu pronaći filterQClientDropdown u orders.html.")
        return False

    content = content[:match.start()] + NEW_Q_CLIENT_FUNCS + content[match.end():]
    backup(ORDERS, '.bak_clientv2')
    write(ORDERS, content)
    print("OK: filterQClientDropdown i selectQClient popravljeni u orders.html (onpointerdown fix).")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("fix_client_dropdown_v2.py")
    print("=" * 60)
    r1 = patch_form()
    r2 = patch_orders()
    print()
    if r1 and r2:
        print("✅ Gotovo — restartaj Flask i testiraj oba dropdowna.")
    else:
        print("⚠️  Neke promjene nisu primijenjene.")
