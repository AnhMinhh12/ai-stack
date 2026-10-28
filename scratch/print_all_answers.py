import json

with open("/home/admin/ai-stack/scratch/ai_eval_18_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for r in data:
    qid = r['id']
    q_text = r['question']
    resp = r['response']
    print(f"\n{'='*25} CÂU {qid:02d} ({r['elapsed']:.2f}s) {'='*25}")
    print(f"HỎI: {q_text}")
    try:
        obj = json.loads(resp)
        if "rendered_answer" in obj:
            print("AI TRẢ LỜI:", obj["rendered_answer"])
        elif "message" in obj:
            print("AI TRẢ LỜI:", obj["message"])
        elif "summary" in obj and obj["summary"]:
            print("AI TRẢ LỜI (summary):", json.dumps(obj["summary"], ensure_ascii=False))
        else:
            print("AI TRẢ LỜI:", json.dumps(obj, ensure_ascii=False)[:300])
    except Exception:
        print("AI TRẢ LỜI (raw):", str(resp)[:300])
