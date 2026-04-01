import shutil
from pathlib import Path

APP = Path('app.py')
shutil.copy(APP, APP.with_suffix('.py.bak'))
c = APP.read_text(encoding='utf-8')

# Fix 1: stupac "početno" — piši start_km_d umjesto cur_km
old = """        daily_data.append([
            P(date_str, align=TA_CENTER, size=8),
            P(f"{cur_km:,.0f}", align=TA_CENTER, size=8),
            P(f"{end_km_d:,.0f}", align=TA_CENTER, size=8),"""
new = """        daily_data.append([
            P(date_str, align=TA_CENTER, size=8),
            P(f"{start_km_d:,.0f}", align=TA_CENTER, size=8),
            P(f"{end_km_d:,.0f}", align=TA_CENTER, size=8),"""

if old in c:
    c = c.replace(old, new)
    print('✅ PDF: početno km piše start_km_d')
else:
    print('❌ Pattern nije pronađen')

# Fix 2: isti elif bug kao u Excelu — pn_label iz pn_list po datumu
old = """            elif official > 0 and raw_comment in ('PN', 'PN+privatno'):
                comment = raw_comment
            else:
                comment = raw_comment if raw_comment else ('privatno' if private > 0 else '')
            cur_km     = end_km_d
        else:
            start_km_d = cur_km
            official   = pn_official.get(date_str, 0) if is_pn else 0"""
new = """            elif official > 0 and raw_comment in ('PN', 'PN+privatno'):
                _pn_match = next((p for p in pn_list if p.get('departure_date', '') == date_str), None)
                if _pn_match:
                    _pn_lbl = f"PN {_pn_match['auto_id']}"
                    comment = _pn_lbl if raw_comment == 'PN' else f"{_pn_lbl}+privatno"
                else:
                    comment = raw_comment
            else:
                comment = raw_comment if raw_comment else ('privatno' if private > 0 else '')
            cur_km     = end_km_d
        else:
            start_km_d = cur_km
            official   = pn_official.get(date_str, 0) if is_pn else 0"""

if old in c:
    c = c.replace(old, new)
    print('✅ PDF: elif grana piše PN broj iz pn_list')
else:
    print('⚠️  elif pattern nije pronađen — nije kritično za km prikaz')

APP.write_text(c, encoding='utf-8')
print('\n✅ Patch primijenjen!')
