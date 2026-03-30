#!/usr/bin/env python3
"""
Patch: invoice_list.html
- Fix: likvidacijski modal počinje na stranici 1 (ne zadnjoj)
- Dodaje navigacijske gumbe ◀ / ▶ za listanje stranica PDF-a
"""
import shutil, os, sys

TEMPLATE = os.path.join(os.path.dirname(__file__), 'templates', 'invoice_list.html')

if not os.path.exists(TEMPLATE):
    print(f"❌ Nije pronađen: {TEMPLATE}")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE + '.bak2')
print("✅ Backup kreiran: invoice_list.html.bak2")

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    src = f.read()

# --- Patch 1: Fix openLiquidateModal - _liqPageNum = numPages → _liqPageNum = 1 ---
OLD1 = ('_liqPdfDoc = await loadingTask.promise; '
        '_liqPageNum = _liqPdfDoc.numPages; '
        'document.getElementById(\'liq-page-info\').textContent = `Stranica ${_liqPageNum} / ${_liqPdfDoc.numPages}`;')

NEW1 = ('_liqPdfDoc = await loadingTask.promise; '
        '_liqPageNum = 1; '
        'document.getElementById(\'liq-page-info\').textContent = `Stranica ${_liqPageNum} / ${_liqPdfDoc.numPages}`; '
        'document.getElementById(\'liq-prev-btn\').style.display = _liqPdfDoc.numPages > 1 ? \'\' : \'none\'; '
        'document.getElementById(\'liq-next-btn\').style.display = _liqPdfDoc.numPages > 1 ? \'\' : \'none\';')

# --- Patch 2: Dodaj navigacijske gumbe u header bar likvidacijskog modala ---
# Tražimo "Stranica X / Y" span i dodajemo gumbe kraj njega
OLD2 = ('<span id="liq-page-info" style="margin-left:auto;color:var(--gray-400);"></span></div>')

NEW2 = ('<button id="liq-prev-btn" onclick="liqPrevPage()" '
        'style="display:none;margin-left:auto;padding:2px 10px;background:#f0f4f8;border:1px solid var(--gray-300);'
        'border-radius:5px;cursor:pointer;font-size:13px;color:var(--navy);" title="Prethodna stranica">◀</button>'
        '<span id="liq-page-info" style="margin:0 6px;color:var(--gray-400);font-size:13px;white-space:nowrap;"></span>'
        '<button id="liq-next-btn" onclick="liqNextPage()" '
        'style="display:none;padding:2px 10px;background:#f0f4f8;border:1px solid var(--gray-300);'
        'border-radius:5px;cursor:pointer;font-size:13px;color:var(--navy);" title="Sljedeća stranica">▶</button>'
        '</div>')

# --- Patch 3: Dodaj JS funkcije liqPrevPage / liqNextPage ispred closeLiquidateModal ---
OLD3 = 'function closeLiquidateModal() {'

NEW3 = ('async function liqPrevPage() {\n'
        '  if (!_liqPdfDoc || _liqPageNum <= 1) return;\n'
        '  _liqPageNum--;\n'
        '  document.getElementById(\'liq-page-info\').textContent = `Stranica ${_liqPageNum} / ${_liqPdfDoc.numPages}`;\n'
        '  await renderLiqPage();\n'
        '}\n'
        'async function liqNextPage() {\n'
        '  if (!_liqPdfDoc || _liqPageNum >= _liqPdfDoc.numPages) return;\n'
        '  _liqPageNum++;\n'
        '  document.getElementById(\'liq-page-info\').textContent = `Stranica ${_liqPageNum} / ${_liqPdfDoc.numPages}`;\n'
        '  await renderLiqPage();\n'
        '}\n'
        'function closeLiquidateModal() {')

patches = [
    ("openLiquidateModal - počni od str.1", OLD1, NEW1),
    ("navigacijski gumbi u header",         OLD2, NEW2),
    ("JS funkcije liqPrevPage/liqNextPage",  OLD3, NEW3),
]

ok = True
for label, old, new in patches:
    if old not in src:
        print(f"⚠️  PATCH PRESKOČEN — pattern nije pronađen: {label}")
        print(f"   Tražim: {repr(old[:100])}")
        ok = False
    else:
        src = src.replace(old, new, 1)
        print(f"✅ Patch primijenjen: {label}")

if ok:
    with open(TEMPLATE, 'w', encoding='utf-8') as f:
        f.write(src)
    print("\n🎉 invoice_list.html uspješno ažuriran!")
    print("   Likvidacijski modal sad počinje na str. 1 i ima ◀ ▶ navigaciju.")
else:
    print("\n❌ Neki patchi nisu primijenjeni.")
    # Ispis stvarnog sadržaja za dijagnozu
    lines = src.splitlines()
    print("\n=== Redovi oko 'liqPageNum' ===")
    for i, line in enumerate(lines, 1):
        if 'liqPageNum' in line or 'liq-page-info' in line or 'numPages' in line:
            print(f"{i:5d}: {repr(line[:120])}")
