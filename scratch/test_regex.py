import re

q = "Tra cứu hồ sơ khuôn của mã khuôn K_RC6-3059-000-11A"
m = re.search(r"(?:ma\s+khuon\s+|khuon\s+ma\s+|khuon\s+)([A-Z0-9_\-]+)", q, re.I)
print("Match 1:", m.group(1) if m else None)

# Also test line:
mold_match = re.search(r"\b(K_[A-Z0-9_\-]+)\b", q, re.I)
print("Match 2:", mold_match.group(1) if mold_match else None)
