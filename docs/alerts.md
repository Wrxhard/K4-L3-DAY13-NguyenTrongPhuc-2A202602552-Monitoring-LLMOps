# Alert và runbook CP2

Các điều kiện nằm trong `config/alert_rules.yaml`. Tất cả dùng dấu hiệu ảnh hưởng tới người dùng và gửi tới Slack `#day13-llmops-alerts`. `duration` là khoảng thời gian điều kiện phải liên tục đúng; mẫu tối thiểu tránh báo động khi lượng request quá nhỏ. Cấu hình là đặc tả alert, chưa có bộ gửi Slack chạy tự động trong starter.

## Alert 1: latency

- **Tên:** `user_latency_p95_high`; **severity:** warning; **owner:** on-call LLMOps.
- **Điều kiện:** P95 `response_sent.latency_ms` trong 5 phút > 3000 ms, với ít nhất 5 request. Duy trì 5 phút.
- **SLI/SLO:** SLO `fast_successful_requests` 99,5% trong 28 ngày; mỗi request tốt cần hoàn tất trong 3000 ms.
- **Ảnh hưởng:** Người dùng nhận phản hồi chậm, có thể hết thời gian chờ.
- **Ba bước kiểm tra:** (1) Xem panel latency P95/P99 và TTFT, so với ngưỡng 3000 ms; (2) lấy `correlation_id` từ log `response_sent` chậm; (3) mở trace cùng ID, so thời lượng `retrieval` và `fake-llm` trên waterfall.
- **Giảm tác động:** Nếu retrieval chậm, kiểm tra nguồn tài liệu và giảm timeout/retry; nếu generation chậm, giảm token đầu ra hoặc chuyển model/route ổn định theo cấu hình vận hành. Theo dõi P95 sau thay đổi.

## Alert 2: request failures

- **Tên:** `user_request_failure_rate_high`; **severity:** critical; **owner:** on-call API.
- **Điều kiện:** `request_failed / request_received * 100` trong 5 phút > 2%, với ít nhất 5 request. Duy trì 5 phút.
- **SLI/SLO:** Error rate guardrail tối đa 2%; request lỗi cũng tiêu thụ error budget của SLO chính.
- **Ảnh hưởng:** Người dùng nhận lỗi hoặc không có câu trả lời.
- **Ba bước kiểm tra:** (1) Xem panel error rate và breakdown `error_type`; (2) tìm `request_failed` và `correlation_id` tương ứng trong log; (3) mở trace cùng ID để xác định retrieval hay generation thất bại, kiểm tra `/health` và incident flags.
- **Giảm tác động:** Tắt incident flag nếu đang bật trong lab, rollback thay đổi mới gây lỗi, khôi phục dependency và chạy lại health/load test; chỉ đóng alert khi error rate về dưới 2%.

## Alert 3: quality

- **Tên:** `user_quality_proxy_low`; **severity:** warning; **owner:** on-call AI quality.
- **Điều kiện:** Mean `response_sent.quality_score` trong 15 phút < 0,75, với ít nhất 10 phản hồi. Duy trì 15 phút.
- **SLI/SLO:** Quality proxy guardrail tối thiểu 0,75. Đây là heuristic, không thay thế đánh giá câu trả lời thực tế.
- **Ảnh hưởng:** Câu trả lời kém hữu ích dù API vẫn trả 200.
- **Ba bước kiểm tra:** (1) Xem panel quality và traffic để xác nhận đủ mẫu; (2) lọc log theo `feature`, `model`, `correlation_id` của phản hồi điểm thấp; (3) so trace metadata `prompt_name`, `prompt_label`, `prompt_version` và retrieval success của nhóm bị ảnh hưởng.
- **Giảm tác động:** Nếu chất lượng giảm sau promote prompt, chuyển `production` về version ổn định đã ghi trong evidence; kiểm tra tập tài liệu và chạy lại cùng input baseline/candidate trước khi mở lại candidate.
