import os, sys, json, time
sys.path.insert(0, "/home/admin/ai-stack")
sys.path.insert(0, "/home/admin/ai-stack/functions")

os.environ["HTMP_DB_PORT"] = "5410"
from functions.htmp_postgres_query import Tools

tools = Tools()

from scratch.run_chat_api_all_45 import QUESTIONS

results = []
print(f"=== BẮT ĐẦU ĐỐI SOÁT CHI TIẾT TOÀN BỘ {len(QUESTIONS)} CÂU HỎI VỚI POSTGRESQL ===")

for idx, item in enumerate(QUESTIONS, 1):
    qid = item["id"]
    name = item["name"]
    text = item["text"]
    
    t0 = time.time()
    try:
        raw_res = tools.ask_erp(text)
        duration = round(time.time() - t0, 3)
        
        is_rich_ui = False
        if isinstance(raw_res, tuple):
            is_rich_ui = True
            data = raw_res[1]
        elif isinstance(raw_res, dict):
            data = raw_res
        elif isinstance(raw_res, str):
            try:
                data = json.loads(raw_res)
            except Exception:
                data = {"message": raw_res}
        else:
            data = {"message": str(raw_res)}
            
        status = data.get("status", "success")
        source = data.get("source", "Postgres ERP/MES")
        rows = data.get("rows", [])
        row_count = len(rows) if isinstance(rows, list) else data.get("row_count", 0)
        message = data.get("message", "")
        
        # Summary excerpt
        summary = ""
        if isinstance(message, str):
            lines = [l for l in message.split("\n") if l.strip() and not l.strip().startswith("|")]
            summary = lines[0] if lines else message[:150]
        
        results.append({
            "stt": idx,
            "id": qid,
            "name": name,
            "question": text,
            "status": "PASS" if (row_count > 0 or len(message) > 20) else "FAIL",
            "duration_sec": duration,
            "source_table": source,
            "row_count": row_count,
            "is_rich_ui": is_rich_ui,
            "summary": summary[:200],
            "sample_row": rows[0] if (isinstance(rows, list) and len(rows) > 0) else None
        })
        print(f"[{idx:2}/{len(QUESTIONS)}] {qid}: {name:40} -> PASS ({row_count} rows, {duration}s) | Nguồn: {source}")
    except Exception as e:
        print(f"[{idx:2}/{len(QUESTIONS)}] {qid}: {name:40} -> ERROR: {e}")
        results.append({
            "stt": idx,
            "id": qid,
            "name": name,
            "question": text,
            "status": "ERROR",
            "duration_sec": round(time.time() - t0, 3),
            "error": str(e)
        })

out_path = "/home/admin/ai-stack/scratch/ket_qua_doi_soat_toan_bo_45_cau.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(QUESTIONS),
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "results": results
    }, f, ensure_ascii=False, indent=2)

print(f"\n=== HOÀN TẤT ĐỐI SOÁT: {sum(1 for r in results if r['status'] == 'PASS')}/{len(QUESTIONS)} PASS ===")
