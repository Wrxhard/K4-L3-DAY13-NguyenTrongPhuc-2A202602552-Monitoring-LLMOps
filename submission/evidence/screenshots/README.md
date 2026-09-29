# Chụp evidence từng ảnh (PowerShell, Windows)

Lưu ảnh thật vào **thư mục này** với tên trong bảng bên dưới. Nhấn `Win + Shift + S`, chọn vùng đủ rộng để đọc rõ kết quả, rồi lưu PNG đúng tên. Không mở/chụp Langfuse API Keys, `.env`, secret hoặc dữ liệu người dùng thật. Dùng project Langfuse cá nhân `day13-k4-l3a-2A202602552`.

Theo `docs/SUBMISSION.md`, **01–03 được phép dùng `.txt`**, nhưng bạn có thể chụp ảnh cho đồng bộ. 04–11 cần ảnh runtime; 12–14 thuộc CP3 và chỉ thực hiện khi đã nhận challenge riêng từ Lab Coach.

## 0. Chuẩn bị môi trường

Mở PowerShell trong thư mục repository này. Mọi lệnh bên dưới chạy từ root repo. Không cần activate venv vì dùng đường dẫn Python trực tiếp.

```powershell
Set-Location 'C:\Users\wrxha\Desktop\VinAI20K\Lab_Day_13\K4-L3-DAY13-NguyenTrongPhuc-2A202602552-Monitoring-LLMOps'
New-Item -ItemType Directory -Force submission\evidence\screenshots
Test-Path .venv\Scripts\python.exe
Test-Path .env
```

Hai lệnh `Test-Path` phải trả `True`. Nếu chưa có venv, làm theo `README.md` để cài `requirements.txt`; nếu thiếu `.env`, điền key project của bạn theo `.env.example` nhưng **không chụp file này**.

Mở **terminal A** tại root repo và để chạy API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000
```

Mở **terminal B** tại root repo và để chạy dashboard:

```powershell
.\.venv\Scripts\python.exe -m dashboard.server --host 127.0.0.1 --port 8501
```

Nếu cổng đã được dùng vì API/dashboard vẫn đang chạy, giữ tiến trình cũ, không khởi động thêm. Dùng **terminal C** cho các lệnh chụp. Kiểm tra:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/health) | ConvertTo-Json
(Invoke-RestMethod http://127.0.0.1:8501/api/dashboard).panels.Count
```

Kết quả mong đợi: `ok: true`, `tracing_enabled: true` và `6` panel. Dashboard chỉ xem **60 phút gần nhất**; nếu để quá lâu, chạy lại load test ở bước 06 rồi đợi refresh.

## 1. Chụp 01–05: tests và log

Chạy từng khối trong terminal C, chụp output ngay sau lệnh. Với 04/05, terminal nên đủ rộng để thấy log đã format.

| Ảnh cần lưu | Lệnh / màn hình cần chụp | Nội dung phải thấy |
|---|---|---|
| `01-pytest.png` | `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` | `28 passed` (hoặc số mới nhất) |
| `02-log-validator.png` | `.\.venv\Scripts\python.exe scripts\validate_logs.py` | Score ít nhất 80/100, PII leak 0 |
| `03-dashboard-validator.png` | `.\.venv\Scripts\python.exe scripts\validate_dashboard.py` | `HỢP LỆ: 6/6 panel` |
| `04-structured-log.png` | Lệnh ngay dưới bảng | `request_received`/`response_sent`, `correlation_id`, metadata, latency |
| `05-pii-redaction.png` | Probe giả và log ngay dưới bảng | PII giả trong input, log chỉ có `[REDACTED_...]` |

Tạo request mới và xem log dễ đọc cho ảnh 04:

```powershell
.\.venv\Scripts\python.exe scripts\load_test.py --concurrency 5
.\.venv\Scripts\python.exe scripts\evidence_log_view.py --latest
```

Ảnh 05 dùng **dữ liệu giả** và một correlation ID cố định. Chụp lệnh chứa input giả cùng log đã scrub; không dùng thông tin thật:

```powershell
$body = @{user_id='capture-user'; session_id='capture-pii'; feature='qa'; message='Contact test@example.com 0901234567 001234567890 4111111111111111'} | ConvertTo-Json -Compress
$response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/chat' -Method Post -ContentType 'application/json' -Headers @{'x-request-id'='req-cafe0001'} -Body $body
$body
$response.Headers['x-request-id']
.\.venv\Scripts\python.exe scripts\evidence_log_view.py --id req-cafe0001
```

Sau probe, chạy lại `validate_logs.py` nếu muốn ảnh 02 phản ánh toàn bộ log mới.

## 2. Chụp 06–08: trace Langfuse

```powershell
.\.venv\Scripts\python.exe scripts\load_test.py --concurrency 5
.\.venv\Scripts\python.exe scripts\verify_cp2_traces.py
```

Đợi trace được gửi lên Langfuse, mở [traces của project cá nhân](https://cloud.langfuse.com/project/cmumcnrm613mfad0cxhxxbqrb/traces). Chọn khoảng thời gian chứa workload vừa chạy.

| Ảnh cần lưu | Màn hình cần chụp |
|---|---|
| `06-trace-list.png` | Tên project và ít nhất 10 trace mới trong danh sách; có thể lọc theo thời gian vừa chạy. |
| `07-trace-waterfall.png` | Mở một trace mới, mở rộng cây để thấy `lab-agent-run` → `retrieval` và `fake-llm`, cùng thanh thời gian. [Trace mẫu đã xác minh](https://cloud.langfuse.com/project/cmumcnrm613mfad0cxhxxbqrb/traces?traceId=c9aee46406dcec5ffbbf2e2aa23126ef). |
| `08-trace-metadata.png` | Cùng trace: `correlation_id`, hashed `user_id`, `session_id`, feature/model/env, prompt `day13-chat` v1, tokens và cost. Có thể chụp 2 ảnh `08a`/`08b` nếu không cùng một khung. |

Ghi lại **trace ID và correlation ID của trace bạn chọn** trong `submission/REPORT.md`. Đừng chụp trang API Keys. Nếu `verify_cp2_traces.py` báo lỗi vì log cũ đã mất, dùng trace list và log workload mới để chọn ID; script này kiểm chứng 10 trace CP2 đã tạo trước đó.

## 3. Chụp 09–10: prompt version và rollback

Trong project Langfuse, mở **Prompts → day13-chat**. Helper dưới đây chỉ dùng input thử an toàn, mỗi lệnh `run` tạo một trace với cùng input `Explain the observability workflow`.

```powershell
.\.venv\Scripts\python.exe scripts\evidence_prompt.py status
.\.venv\Scripts\python.exe scripts\evidence_prompt.py run --label baseline
.\.venv\Scripts\python.exe scripts\evidence_prompt.py run --label candidate
```

Ghi hai `trace_id` được in ra. Mở hai trace đó để thấy `prompt_label`/`prompt_version` v1 và v2. Chụp `09-prompt-versions.png` trên trang prompt có v1/v2 và labels `baseline`, `candidate`, `production`.

Chạy lần lượt, **chụp sau từng trạng thái**:

```powershell
.\.venv\Scripts\python.exe scripts\evidence_prompt.py promote
.\.venv\Scripts\python.exe scripts\evidence_prompt.py run --label production
```

Refresh trang prompt: `production` phải ở v2. Chụp `10a-prompt-promoted.png`, ghi trace ID production/v2. Sau đó rollback:

```powershell
.\.venv\Scripts\python.exe scripts\evidence_prompt.py rollback
.\.venv\Scripts\python.exe scripts\evidence_prompt.py status
```

Refresh trang prompt: `production` phải trở lại v1. Chụp `10b-prompt-rollback.png`. **Đừng dừng sau promote**; để `production` ở v1 như báo cáo CP2. Ghi ba trace ID mới vào report nếu bạn dùng chúng thay cho ID cũ.

## 4. Chụp 11: dashboard runtime

Chạy lại workload nếu dữ liệu đã cũ, rồi mở [dashboard local](http://127.0.0.1:8501):

```powershell
.\.venv\Scripts\python.exe scripts\load_test.py --concurrency 5
```

Chờ tối đa 30 giây để dashboard tự refresh. Chụp `11-dashboard-overview.png`: cả 6 panel có dữ liệu, tên, đơn vị, 60 min và threshold/SLO line. Nếu một ảnh không đọc rõ, lưu thêm `11a-dashboard-latency-errors.png` và `11b-dashboard-cost-token-quality.png`.

## 5. Chụp 12–14 sau khi CP3 được mở

**Chỉ chạy challenge chính thức khi Lab Coach đã gửi file riêng `config/challenge.json` đúng lớp.** Không tự tạo hoặc chỉnh sửa file này.

```powershell
.\.venv\Scripts\python.exe scripts\inject_incident.py
.\.venv\Scripts\python.exe scripts\load_test.py --challenge --concurrency 5
```

- `12-incident-metric.png`: panel dashboard bất thường và khoảng thời gian sự cố.
- `13-incident-log.png`: tìm một `correlation_id` bất thường trong `data/logs.jsonl`, rồi chạy `.\.venv\Scripts\python.exe scripts\evidence_log_view.py --id req-xxxxxxxx` với ID thật; chụp log.
- `14-incident-trace.png`: mở trace Langfuse có cùng `correlation_id`, chụp span gây lỗi/chậm.

Ghi challenge ID, metric, log ID, trace ID, root cause, fix và phòng ngừa vào phần 7 của `submission/REPORT.md`. Không chụp/commit `config/challenge.json`.

## 6. Sau khi chụp

Đối chiếu file ảnh trong thư mục này:

```powershell
Get-ChildItem submission\evidence\screenshots\*.png | Select-Object Name,Length
```

Ảnh `01–11` nên có trước khi nộp CP2/CP4; ảnh `12–14` đợi CP3. Cập nhật đường dẫn ảnh **tương đối** trong `submission/REPORT.md`, ví dụ `evidence/screenshots/07-trace-waterfall.png`. Kiểm tra ảnh không lộ key/secret/PII thật. **Không commit hoặc push cho đến khi bạn yêu cầu.**
