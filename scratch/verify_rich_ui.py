with open('erp_ai/rich_ui.py') as f:
    code = f.read()

print('Has transparent background:', 'background:transparent!important' in code)
print('Has no dark bg-page:', '--bg-page' not in code)
print('Has safe legend labels:', 'generateLabels()' in code)
print('Has chartColors:', 'chartColors' in code)
