import glob, re

for f in glob.glob('/app/build/**/*.js', recursive=True):
    try:
        with open(f, 'r', encoding='utf-8') as fp:
            content = fp.read()
            if 'iframe' in content.lower():
                matches = re.findall(r'<iframe[^>]*>|sandbox[=:][^,}"]*', content)
                if matches:
                    print(f, matches[:5])
    except Exception as e:
        pass
