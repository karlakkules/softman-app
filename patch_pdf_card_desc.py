import shutil
from pathlib import Path

APP = Path('app.py')
shutil.copy(APP, APP.with_suffix('.py.bak'))
c = APP.read_text(encoding='utf-8')

OLD = """    for exp in expenses:
        amt = f"{exp['amount']:.2f}" if exp['paid_privately'] and exp['amount'] else ''
        exp_rows.append([
            Paragraph(safe(exp['cat_name'] or ''), style('er1', 8)),
            Paragraph(safe(exp['description'] or ''), style('er2', 8)),
            Paragraph('✓' if exp['paid_privately'] else '', style('er3', 8, False, TA_CENTER)),
            Paragraph(amt, style('er4', 8, False, TA_RIGHT)),
        ])"""

NEW = """    for exp in expenses:
        amt = f"{exp['amount']:.2f}" if exp['paid_privately'] and exp['amount'] else ''
        is_card = not exp['paid_privately']
        desc = 'Plaćeno službenom karticom' if is_card else safe(exp['description'] or '')
        exp_rows.append([
            Paragraph(safe(exp['cat_name'] or ''), style('er1', 8)),
            Paragraph(desc, style('er2', 8)),
            Paragraph('✓' if exp['paid_privately'] else '', style('er3', 8, False, TA_CENTER)),
            Paragraph(amt, style('er4', 8, False, TA_RIGHT)),
        ])"""

if OLD in c:
    c = c.replace(OLD, NEW)
    print('✅ Opis troška karticom: "Plaćeno službenom karticom"')
else:
    print('❌ Pattern nije pronađen')
    exit(1)

APP.write_text(c, encoding='utf-8')
print('✅ Patch primijenjen!')
