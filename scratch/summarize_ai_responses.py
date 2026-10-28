#!/usr/bin/env python3
import json

with open("/home/admin/ai-stack/scratch/ai_eval_18_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for r in data:
    qid = r['id']
    q_text = r['question']
    resp = r['response']
    print(f"\n{'='*20} CÂU {qid} ({r['elapsed']:.2f}s) {'='*20}")
    print(f"HỎI: {q_text}")
    try:
        obj = json.loads(resp)
        if "rendered_answer" in obj:
            print("AI TRẢ LỜI:", obj["rendered_answer"])
        elif "message" in obj:
            print("AI TRẢ LỜI:", obj["message"])
        elif "summary" in obj and obj["summary"]:
            print("AI TRẢ LỜI (summary):", json.dumps(obj["summary"], ensure_ascii=False))
        elif "rows" in obj and obj["rows"]:
            print(f"AI TRẢ LỜI ({len(obj['rows'])} dòng):", json.dumps(obj["rows"][:3], ensure_ascii=False))
        else:
            print("AI TRẢ LỜI:", str(obj)[:300])
    except Exception:
        print("AI TRẢ LỜI (raw):", str(resp)[:300])
