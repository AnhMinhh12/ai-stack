# PILOT-20260909 — bước 7: deploy pilot và nghiệm thu

**UTC:** 2026-09-09  
**Host:** `edgexpert-f3a2`  
**Trạng thái:** `blocked` — runtime smoke pass; promotion gates upstream chưa đạt.

## Evidence runtime smoke

| Kiểm tra | Kết quả |
| --- | --- |
| `python3 scripts/staging_smoke_check.py` | pass |
| Compose config | pass |
| Runtime | 8/8 healthy |
| Nginx syntax | pass |
| Open WebUI/vLLM/Tika/Langfuse health | pass |
| vLLM authenticated `/v1/models` | pass |
| Qdrant authenticated `/collections` | pass |
| `scripts/pilot_gate_check.py` | blocked đúng vì upstream gates |

Runtime smoke không bao gồm upload/RAG ACL/trace/capacity/DR/rollback và không đủ để
phê duyệt pilot. Không có thay đổi traffic hoặc dữ liệu pilot được thực hiện.

## Blocker

- Owner/approver và pilot scope chưa ký.
- Release scan/digest/rollback, IAM E2E, trace/alert, clean-room DR và capacity/soak
  vẫn chưa đạt.
- Checklist đầy đủ ở [pilot-acceptance-checklist](../../pilot-acceptance-checklist.md).
