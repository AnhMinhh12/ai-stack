import re

test_cases = [
    "khuôn 4509 có bao nhiêu cavity",
    "số cavity của mã khuôn K_101 40481 01 là bao nhiêu",
    "khuôn có cavity là bao nhiêu",
    "khuôn K_QC5-2919-000-V1 có bao nhiêu cavity",
    "Khuôn FE8-3324-001-11A đã chạy tổng cộng bao nhiêu shot",
    "hồ sơ khuôn K_RC6-3059-000-11A",
    "Các khuôn 4509 này được sử dụng cho sản phẩm nào?"
]

def extract_mold_code(q):
    # Pattern 1: After 'mã khuôn' or 'khuôn' until stop words
    stop_words = r"(?=\s+(?:có|co|là|la|được|duoc|đã|da|thuộc|thuoc|chạy|chay|ở|o|trong|này|nay|nào|nao|cho|$|[?,.]))"
    m = re.search(r"(?:mã\s+khu[oô]n|ma\s+khu[oô]n|khu[oô]n\s+mã|khu[oô]n)\s+([A-Z0-9_\-\s]{1,30}?)" + stop_words, q, re.I)
    if m:
        cand = m.group(1).strip()
        # Clean candidates
        if re.search(r"\d", cand) or cand.startswith("K_"):
            return cand
    # Pattern 2: Standalone K_ code
    m2 = re.search(r"\b(K_[A-Z0-9_\-]+)\b", q, re.I)
    if m2:
        return m2.group(1).strip()
    return None

for t in test_cases:
    code = extract_mold_code(t)
    clean = re.sub(r"[\s\-_]+", "", code).upper() if code else None
    print(f"Query: '{t}'")
    print(f"  -> Extracted code: '{code}' (clean: '{clean}')")
