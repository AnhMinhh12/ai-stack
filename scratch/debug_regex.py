import re

def normalize_text(text: str) -> str:
    # simple test
    return text.lower()

questions = [
    "khuôn 4509 có bao nhiêu cavity",
    "số cavity của mã khuôn K_101 40481 01 là bao nhiêu",
    "khuôn có cavity là bao nhiêu",
    "khuôn K_QC5-2919-000-V1 có bao nhiêu cavity"
]

for q in questions:
    print("\n--- Testing:", q)
    norm = q.lower()
    is_ng = bool(re.search(r"\b(?:ng|loi|hong|sua chua|bao tri)\b", norm))
    is_total = not is_ng and any(t in norm for t in ("tong so", "so luong", "bao nhieu", "thong ke", "tat ca", "co bao nhieu"))
    print("is_total:", is_total)
    
    m1 = re.search(r"\b(K_[A-Z0-9_\-]+)\b", q, re.I)
    print("m1 (K_...):", m1.group(1) if m1 else None)
    
    m2 = re.search(r"(?:ma\s+khuon\s+|khuon\s+ma\s+|khuon\s+|khuôn\s+)([A-Z0-9_\-]+)", q, re.I)
    print("m2 (khuon ...):", m2.group(1) if m2 else None)
    
    m3 = re.search(r"\b([A-Z0-9]+[_\-][A-Z0-9_\-]+)\b", q, re.I)
    print("m3 (code with hyphen):", m3.group(1) if m3 else None)
