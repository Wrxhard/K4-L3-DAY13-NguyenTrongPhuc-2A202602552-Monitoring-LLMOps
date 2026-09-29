# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Trọng Phúc
- **MSSV:** 2A202602552
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/Wrxhard/K4-L3-DAY13-NguyenTrongPhuc-2A202602552-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** day13-k4-l3a-2A202602552

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100; 42 records, 40 thiếu required fields/context, 0 correlation IDs | | Chưa đạt ở CP0; TODO thuộc CP1. |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel contract | | Chỉ xác nhận cấu hình, chưa xác nhận dashboard runtime. |
| `pytest` | 22 passed, 2 cảnh báo không ghi được pytest cache | | Chạy bằng `.venv\Scripts\python.exe -m pytest -q`. |
| Số traces hợp lệ | 10 root traces mới trên Langfuse | | Đã xác nhận trong project cá nhân đúng tên lab. |
| Số PII leak | 0 theo log validator | | Kết quả chỉ trên 42 log records hiện có. |
| Latency P95 / TTFT P95 | 1672 ms / 68 ms | | `/metrics` sau workload 10 request có mạng Langfuse. |
| Retrieval success rate | | | |

### Baseline CP0 — 29/09/2026, 14:32 Asia/Ho_Chi_Minh

- `GET http://127.0.0.1:8000/health`: HTTP 200, `ok: true`, `tracing_enabled: true`; cả ba incident flag đều `false`.
- Chạy `python scripts/load_test.py` với 10 sample queries: 10/10 phản hồi HTTP 200. `data/logs.jsonl` đã tạo, 42 dòng sau hai lượt baseline. Lượt đầu bị sandbox chặn mạng nên không xuất trace; lượt thứ hai chạy API với quyền mạng và tạo 10 trace mới.
- Langfuse Cloud: project ID `cmumcnrm613mfad0cxhxxbqrb` trong `Nguyen's Organization`, tên hiển thị `day13-k4-l3a-2A202602552`. Baseline có 10 root observations `lab-agent-run` tại 14:32:49–14:32:55. Trace mẫu: `73522435190535796b676011e2eb4cb4` ([mở trace](https://cloud.langfuse.com/project/cmumcnrm613mfad0cxhxxbqrb/traces?traceId=73522435190535796b676011e2eb4cb4)). Project gắn với key trong `.env` và phiên Langfuse cá nhân đang đăng nhập; kiểm tra lại sau đổi tên thấy 20 root traces.
- Log validator 30/100 là baseline bình thường của starter; `correlation_id` hiện là `MISSING`. Prompt `day13-chat`/`production` chưa có trên Langfuse nên trace ghi `prompt_source=local-fallback`. Các việc này thuộc CP1/CP2.
- Trạng thái CP0: hoàn thành; health, log, workload, tests và trace trong project cá nhân đúng tên đã được kiểm chứng.

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
- **Các metadata được ghi vào structured log:**
- **Cách bảo đảm PII được scrub trước khi ghi:**
- **Cách kiểm chứng kết quả:**

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
- **SLO và lý do chọn:**
- **Cách tính error budget:**
- **Ba alert và runbook tương ứng:**

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
