# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Trọng Phúc
- **MSSV:** 2A202602552
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/Wrxhard/K4-L3-DAY13-NguyenTrongPhuc-2A202602552-Monitoring-LLMOps
- **Commit SHA cuối:** `950b09e`
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** day13-k4-l3a-2A202602552

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/screenshots/01-pytest.png` |
| Log validator | `evidence/screenshots/02-log-validator.png` |
| Dashboard validator | `evidence/screenshots/03-dashboard-validator.png` |
| Structured log | `evidence/screenshots/04-structured-log.png` |
| PII redaction | `evidence/screenshots/05-pii-redaction.png` |
| Trace list, quan hệ cha–con và metadata | `evidence/screenshots/06-trace-list.png`, `evidence/screenshots/08-trace-metadata.png` |
| Trace waterfall | `evidence/screenshots/07-trace-waterfall.png` |
| Prompt versions | `evidence/screenshots/09-prompt-versions.png` |
| Prompt rollback | `evidence/screenshots/10a-prompt-promoted.png`, `evidence/screenshots/10b-prompt-rollback.png` |
| Dashboard runtime (ảnh do học viên chụp) | `evidence/screenshots/11-dashboard-overview.png` |
| Incident metric | `evidence/screenshots/12-incident-metric.png` |
| Incident log | `evidence/screenshots/13-incident-log.png` |
| Incident trace | `evidence/screenshots/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100; 42 records, 40 thiếu required fields/context, 0 correlation IDs | CP1: 100/100; 23 records, 11 correlation IDs, 0 PII leak | Đo lại sau khi xóa log baseline và chạy workload mới; [output](evidence/02-log-validator.txt). |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel contract | CP2: 6/6 | Validator cấu trúc; runtime HTTP 200 và sáu panel có dữ liệu trong [evidence](evidence/11-dashboard-runtime.txt). |
| `pytest` | 22 passed, 2 cảnh báo không ghi được pytest cache | CP2: 28 passed | Chạy bằng `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`. |
| Số traces hợp lệ | 10 root traces mới trên Langfuse | CP2: 10 trace mới, mỗi trace có root + 2 child | Đã đối chiếu project cá nhân, quan hệ parent và log correlation ID. |
| Số PII leak | 0 theo log validator | 0 trên 44 log records | `validate_logs.py` đạt 100/100. |
| Latency P95 / TTFT P95 | 1672 ms / 68 ms | 1583 ms / 55 ms | Dashboard 60 phút lúc kiểm tra CP2. |
| Retrieval success rate | Chưa có panel | 100% | 21 request trong cửa sổ dashboard. |

### Baseline CP0 — 29/09/2026, 14:32 Asia/Ho_Chi_Minh

- `GET http://127.0.0.1:8000/health`: HTTP 200, `ok: true`, `tracing_enabled: true`; cả ba incident flag đều `false`.
- Chạy `python scripts/load_test.py` với 10 sample queries: 10/10 phản hồi HTTP 200. `data/logs.jsonl` đã tạo, 42 dòng sau hai lượt baseline. Lượt đầu bị sandbox chặn mạng nên không xuất trace; lượt thứ hai chạy API với quyền mạng và tạo 10 trace mới.
- Langfuse Cloud: project ID `cmumcnrm613mfad0cxhxxbqrb` trong `Nguyen's Organization`, tên hiển thị `day13-k4-l3a-2A202602552`. Baseline có 10 root observations `lab-agent-run` tại 14:32:49–14:32:55. Trace mẫu: `73522435190535796b676011e2eb4cb4` ([mở trace](https://cloud.langfuse.com/project/cmumcnrm613mfad0cxhxxbqrb/traces?traceId=73522435190535796b676011e2eb4cb4)). Project gắn với key trong `.env` và phiên Langfuse cá nhân đang đăng nhập; kiểm tra lại sau đổi tên thấy 20 root traces.
- Log validator 30/100 là baseline bình thường của starter; `correlation_id` hiện là `MISSING`. Prompt `day13-chat`/`production` chưa có trên Langfuse nên trace ghi `prompt_source=local-fallback`. Các việc này thuộc CP1/CP2.
- Trạng thái CP0: hoàn thành; health, log, workload, tests và trace trong project cá nhân đúng tên đã được kiểm chứng.

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware clear structlog contextvars ở đầu mỗi request; dùng `x-request-id` khi khớp `req-<8-hex>`, nếu không sẽ sinh ID mới. ID được bind vào context, đưa vào `request.state`, response body và header `x-request-id`. Header `x-response-time-ms` chứa thời gian xử lý.
- **Các metadata được ghi vào structured log:** Trước `request_received`, `/chat` bind `user_id_hash`, `session_id`, `feature`, `model`, `env` cùng `correlation_id` từ middleware. Không ghi user ID nguyên văn.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` xử lý đệ quy mọi chuỗi trong event, gồm metadata, payload lồng nhau và danh sách, sau bước format exception nhưng trước `JsonlFileProcessor` và JSON renderer. Pattern bao phủ email, điện thoại Việt Nam, CCCD và thẻ với các dấu phân cách thông dụng.
- **Cách kiểm chứng kết quả:** Đã xóa `data/logs.jsonl` baseline sau khi lưu số liệu CP0, khởi động lại API rồi chạy 10 sample queries và một request PII thử nghiệm. `validate_logs.py` đạt 100/100 trên 23 records, 11 ID duy nhất, không có PII leak; [output](evidence/02-log-validator.txt) và [sample log đã scrub](evidence/04-structured-log.txt). Request thử trả `req-a1b2c3d4` ở cả header và body; health trả HTTP 200, `ok: true`, kèm hai response headers. Toàn bộ 26 tests pass.

## 5. Tracing và prompt versioning

- **Project và traces:** Project Langfuse cá nhân `day13-k4-l3a-2A202602552` (`cmumcnrm613mfad0cxhxxbqrb`). Chạy workload 10 request HTTP 200 sau khi thêm child spans; 10 trace ID và kết quả kiểm tra trực tiếp bằng Langfuse API ở [evidence](evidence/06-trace-verification.txt). Script `scripts/verify_cp2_traces.py` có thể chạy lại.
- **Cấu trúc:** Mỗi trace có root `lab-agent-run` (AGENT), child `retrieval` (RETRIEVER) và `fake-llm` (GENERATION), cùng parent ID của root. Generation lưu model `claude-sonnet-4-5`, prompt link `day13-chat` v1, input/output tokens và cost. Trace mẫu `c9aee46406dcec5ffbbf2e2aa23126ef`: retrieval 0,001 s, generation 0,152 s, root 0,155 s; waterfall chỉ rõ LLM là bước chậm. Root/generation không lưu raw input/output.
- **Metadata và nối log:** `user_id` là SHA-256 rút gọn 12 hex; `session_id`, feature, model, env `dev`, `correlation_id` hiện trên trace. Script xác minh cả 10 correlation ID khớp dòng `response_sent` trong `data/logs.jsonl`. Ví dụ trace trên có `req-ba26a24e`.
- **Prompt name:** text prompt `day13-chat`, giữ `{{feature}}`, `{{docs}}`, `{{message}}`.
- **Version/label baseline:** v1 có `baseline` và `production`; template ba dòng `Feature`, `Docs`, `Question`.
- **Version/label candidate:** v2 có `candidate` và `latest`; chỉ thêm câu `Answer in at most three sentences.`
- **Cùng input:** `Explain the observability workflow`; trace `3650ec0fb005867ce1ccb0ee49d446b2` dùng `baseline`/v1, trace `3bd11d375b393b3f5fb18c943e7d4737` dùng `candidate`/v2. Cả hai có `prompt_source=langfuse` và prompt link/version đúng, không phải local fallback.
- **Promote/rollback `production`:** Chuyển label `production` sang v2, chạy cùng input tạo trace `4902161ca7360eca6e9ef243dd537349` (production/v2). Sau đó chuyển `production` về v1; xác minh API trả v1 có `baseline, production`, v2 có `candidate, latest`, `production=v1`. [Evidence trạng thái trước/sau](evidence/10-prompt-rollback.txt) và [kiểm tra trace](evidence/06-trace-verification.txt).

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard local tại `http://127.0.0.1:8501`, chạy bằng `python -m dashboard.server`. Nguồn duy nhất `data/logs.jsonl`, cửa sổ 60 phút, refresh 30 giây. Sáu panel khớp `config/dashboard.yaml`: latency P50/P95/P99 + TTFT P95; traffic; error rate + breakdown + retrieval success; cost; input/output tokens; quality proxy. Mỗi panel có tên, đơn vị và threshold line. Lúc xác minh: 21 requests, P95 1583 ms, TTFT P95 55 ms, error 0%, retrieval success 100%, cost 0,042111 USD, tokens 712/2665, quality 0,88. [Runtime values](evidence/11-dashboard-runtime.txt), [validator 6/6](evidence/03-dashboard-validator.txt). Học viên sẽ tự chụp ảnh dashboard runtime và đặt tại `evidence/11-dashboard-overview.png`.
- **SLO và lý do chọn:** `fast_successful_requests`: 99,5% request trong 28 ngày phải có `response_sent` với latency ≤3000 ms. Baseline CP0 P95 1672 ms nên ngưỡng 3000 ms phát hiện suy giảm lớn mà không báo động từ dao động thường. Guardrails: error rate ≤2%, daily cost ≤2,5 USD, quality proxy ≥0,75, retrieval success ≥90%.
- **Error budget:** 100% − 99,5% = 0,5% request xấu trong rolling 28 ngày, tức `floor(0.005 × tổng request_received)`. Với 1000 request được phép tối đa 5 request lỗi/chậm; với 10.000 request là 50. Baseline 21 request là mẫu nhỏ, không dùng để kết luận SLO 28 ngày.
- **Ba alert và runbook:** `user_latency_p95_high` warning khi P95 >3000 ms trong 5 phút; `user_request_failure_rate_high` critical khi error rate >2% trong 5 phút; `user_quality_proxy_low` warning khi mean quality <0,75 trong 15 phút. Mỗi alert có minimum sample, duration, owner, Slack `#day13-llmops-alerts` và [runbook ba bước](../docs/alerts.md) trong `config/alert_rules.yaml`. Đây là cấu hình đặc tả, chưa có bộ gửi Slack tự động.

## 7. Điều tra challenge

> Phần này dành riêng cho Checkpoint 3 (CP3). Sẽ được cập nhật chi tiết ngay khi nhận file sự cố `config/challenge.json` từ Lab Coach.

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 29/09/2026, 16:09 (Asia/Ho_Chi_Minh)
- **Triệu chứng từ metrics:** Latency P95 tăng vọt bất thường (Spike) vượt mốc báo động trên Dashboard. Các request bị nghẽn, thời gian phản hồi ở máy khách (client latency) cộng dồn lên tới hơn 13000ms (13s).
- **Log line và correlation ID liên quan:** Lọc `data/logs.jsonl` tìm được nhóm request bị chậm. Một `correlation_id` tiêu biểu là `req-f394f1ba` (ghi nhận server `latency_ms`: 2653ms).
- **Trace ID và span gây ảnh hưởng:** Tra cứu `req-f394f1ba` trên Langfuse. Quan sát biểu đồ Waterfall, span `retrieval` bị kéo dài bất thường mất 2.5s (2500ms), trong khi bình thường chỉ tốn vài mili-giây.
- **Root cause:** Sự cố `rag_slow` được kích hoạt khiến hàm `retrieve()` bị delay cố tình (`time.sleep(2.5)`). Tệ hơn, việc dùng hàm đồng bộ `time.sleep` chặn đứng (block) toàn bộ event loop của ứng dụng, gây ra "starvation", khiến các request đồng thời bị xếp hàng chờ, cộng dồn độ trễ lên đến 13s ở máy khách.
- **Fix action:** Đã vô hiệu hóa sự cố bằng lệnh `python scripts/inject_incident.py --disable` (gọi API `/incidents/rag_slow/disable`). Hotfix mã nguồn nếu cần: Đẩy các hàm blocking I/O (như gọi Vector DB) vào threadpool hoặc dùng `await asyncio.sleep` thay cho `time.sleep`.
- **Preventive measure:** Áp dụng Circuit Breaker hoặc Strict Timeout (ví dụ 1000ms) cho các module gọi ngoại vi (retriever/database) để "fail-fast". Bổ sung Alert Rule giám sát riêng Latency P95 của span `retrieval` trên Langfuse.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  Thiết kế kiến trúc Logging theo mô hình Structured Context-Bound với Structlog: Mọi request đi qua middleware đều được gán `correlation_id` duy nhất và lưu vào request contextvars. Tất cả các log lines, response headers và metadata trong Langfuse trace (`user_id_hash`, `session_id`, `feature`, `model`, `correlation_id`) đều được liên kết chặt chẽ. Đặc biệt, bộ xử lý `scrub_event` đệ quy bảo đảm loại bỏ 100% PII (Email, Phone VN, CCCD, Thẻ tín dụng) trước khi lưu vào disk hoặc xuất ra console, đáp ứng triệt để yêu cầu bảo mật dữ liệu người dùng.

- **Một lỗi/blocker đã gặp:**
  Gặp lỗi `PermissionError: [WinError 5] Access is denied: 'C:\Users\wrxha\AppData\Local\Temp\pytest-of-wrxha'` khi chạy `pytest` trên hệ điều hành Windows, khiến 6 bài test sử dụng fixture `tmp_path` bị gián đoạn mặc dù code logic hoàn toàn chính xác.

- **Cách tìm nguyên nhân và xử lý:**
  Kiểm tra chi tiết stacktrace của pytest (`_pytest/pathlib.py`), phát hiện thư mục `pytest-of-wrxha` trong Windows Temp bị một tiến trình chạy trước đó giữ quyền khóa ACL độc quyền. Giải pháp xử lý: tạo `conftest.py` ở root và `tests/conftest.py` để override biến môi trường `TEMP`/`TMP` và thiết lập `config.option.basetemp` trỏ về thư mục cục bộ `.pytest_temp` bên trong project, đồng thời bổ sung `pytest.ini` với `-p no:cacheprovider`. Kết quả giải quyết triệt để vấn đề, toàn bộ 28/28 tests vượt qua thành công (100% pass).

- **Cách hiểu luồng Metrics → Logs → Traces:**
  Ba trụ cột quan sát hoạt động theo mô hình phễu điều tra (Funnel of Observability):
  1. **Metrics (Dashboard & Alerts):** Lớp phát hiện đầu tiên (Detection). Giúp phát hiện triệu chứng diện rộng như Latency P95 vượt ngưỡng 3000ms hoặc Error rate tăng đột biến.
  2. **Logs (Structured Logging):** Lớp định vị ngữ cảnh (Isolation). Dựa vào khoảng thời gian xảy ra sự cố từ Metrics, kỹ sư truy vấn `data/logs.jsonl` để lọc các log lỗi, lấy ra metadata liên quan và đặc biệt là `correlation_id` cụ thể của các request gặp lỗi.
  3. **Traces (Distributed Tracing trên Langfuse):** Lớp chẩn đoán gốc rễ (Root Cause Analysis). Lấy `correlation_id` tìm trace trên Langfuse, quan sát biểu đồ Waterfall của cây spans (`lab-agent-run` ➔ `retrieval` ➔ `fake-llm`), từ đó biết chính xác bước nào bị nghẽn (ví dụ do retrieval chậm hay LLM sinh token chậm) cùng chi tiết prompt version, input/output tokens và error stack trace.

- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - **Prompt Versioning & Rollback:** Đối với ứng dụng LLM, prompt đóng vai trò như mã nguồn logic nghiệp vụ. Việc version hóa trên Langfuse cho phép thử nghiệm an toàn các biến thể (candidate vs baseline). Khi phiên bản mới gặp sự cố (hallucination, trả lời sai, chậm), cơ chế rollback tức thời (chuyển nhãn `production` về phiên bản cũ) giúp phục hồi hệ thống trong vài giây mà không cần deploy lại code.
  - **Token & Cost Monitoring:** Khác với phần mềm truyền thống, mỗi truy vấn LLM tiêu tốn chi phí điện toán trực tiếp (USD). Giám sát token/cost giúp phát hiện các truy vấn bất thường, nguy cơ vòng lặp vô hạn, hoặc prompt injection làm tiêu hao ngân sách.
  - **SLO & Error Budget:** Đặt ra ranh giới định lượng (99.5% request đạt latency ≤ 3000ms). Error budget là công cụ điều tiết: khi budget còn dồi dào, đội ngũ có thể tự tin release prompt mới; khi budget bị bào mòn, ưu tiên hàng đầu là ổn định hệ thống.

- **Điều quan trọng nhất đã học:**
  Hiểu rõ và làm chủ bức tranh toàn cảnh của hệ thống Observability cho ứng dụng AI (LLMOps) theo chuẩn production: kết hợp hài hòa giữa Structured Logging bảo mật PII, Phân tầng Tracing quan sát chuyên sâu từng mắt xích AI, Dashboard theo dõi 4 golden signals và quản lý vòng đời Prompt an toàn.

- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  Đang chờ nhận challenge chính thức cho Checkpoint 3 (`config/challenge.json`) từ Lab Coach để tiến hành inject sự cố, thu thập metrics/logs/traces thực tế và hoàn tất phần 7. Đang chụp và hoàn thiện bộ ảnh evidence lưu trữ vào thư mục `submission/evidence/screenshots/`.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

