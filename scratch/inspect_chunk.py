with open('/app/build/_app/immutable/chunks/DqaovKft.js', 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('data:text/html')
if idx != -1:
    print(c[max(0, idx - 400):min(len(c), idx + 600)])
else:
    print('Not found')
