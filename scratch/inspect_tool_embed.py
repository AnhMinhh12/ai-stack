with open('/app/build/_app/immutable/chunks/CtDyIhYR.js', 'r', encoding='utf-8') as f:
    c = f.read()

for m in [m.start() for m in __import__('re').finditer(r'postMessage', c)]:
    print(c[m - 100:m + 300])
    print("=" * 40)
