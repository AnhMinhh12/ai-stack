import glob, os

for f in glob.glob('/app/build/**/*.js', recursive=True):
    if not os.path.isfile(f):
        continue
    with open(f, 'r', encoding='utf-8') as fp:
        c = fp.read()
        idx = c.find('<iframe')
        while idx != -1:
            snippet = c[max(0, idx - 100):min(len(c), idx + 300)]
            if 'border-0' in snippet:
                print("FILE:", f)
                print("SNIPPET:", snippet)
                print("-" * 50)
            idx = c.find('<iframe', idx + 1)
