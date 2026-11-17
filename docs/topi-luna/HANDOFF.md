# Handoff — Topi analysis v2 (Luna ≈ Opus), 2026-11-17

Nhánh nghiên cứu, chưa nối vào `pipeline.py`. Đọc theo thứ tự: `01-opus-method.md` → `02-luna-instructions.md` → `03-eval.md`.

## Trạng thái
- Luna v2 cùng band với Opus 70–72% (production v1 61%, Opus–Opus 96%), 6 buổi golden 3–8. Lỗ hổng buổi 3–4: recall 6/7 toán, 5/5 kỹ năng học; độ tin cậy lệch vì Luna tách kỹ năng.
- r3–r4 (sửa homework_checked + criticism_person): 74% và 80%; hành vi 6 vẫn yếu (2–3/6).
- r5–r8 (quy tắc đặt tên kỹ năng + sửa hành vi 6 hai bước): 78%, 76%, 78%, 82% so với Opus A (r8 so với Opus B 85%). Hành vi 6 thực ra bị **đếm thừa** self_correction (học sinh lặp lại lời sửa của gia sư); đã sửa bằng `_guard_self_corrections` + prompt; r7–r8 sửa thêm việc gán thiếu error_pointed. Lỗ hổng buổi 3–4 (r5–r6): recall toán 7/7, nhưng độ tin cậy chỉ khớp 2/7 (vẫn tách M3, L4 M1). **Chưa đạt ngưỡng nối pipeline.** Chi tiết: `03-eval.md`.
- Ngưỡng để nối vào pipeline: ≥ 80% band, độ tin cậy lỗ hổng toán khớp ≥ 5/7.

## Dữ liệu (ngoài repo — có trích dẫn buổi học của trẻ vị thành niên, không commit)
- Transcript + nhãn Opus coding v2.1 (run A2, B2) của 10 buổi golden: `C:\Users\lequo\AppData\Local\Temp\claude\ee31f2a9d98464c0\ed3519be-259c-4da8-a8a6-0aeaa55ede66\scratchpad\coding-v2\` (`transcripts/`, `runA2/`, `runB2/`). Nếu mất: lấy transcript bằng connector `toptutor` → `get_transcript`; nhãn Opus phải chạy lại theo `toptutor-main/60-output/01-prompts/lesson-coding-v2.md`.
- Bảng lỗ hổng Opus buổi 3–4: `toptutor-main/40-processes/07-gap-analyser/runs/2026-11-17_golden-lessons-3-4.md`.
- Thư mục chấm của phiên này (có r1–r4, luna_old): `C:\Users\lequo\AppData\Local\Temp\claude\d974ff8ec255865d\bf0f3863-1d4c-491b-ba5d-c808440024f7\scratchpad\eval\data\`. Dựng lại: tạo `transcripts/`, `opusA/` (= runA2), `opusB/` (= runB2) cho 6 buổi `c1698fb7 b8f9fb8c 3d497118 24aedf8f 514fe1df fc8fa23d`. Không dùng buổi 1–2 (blind) và 9–10 (nguồn few-shot).

## Lệnh (chạy từ thư mục tutora-ai có `.env` chứa `OPENAI_API_KEY`; Settings cần đủ biến của `.env`)
- Chấm lại từ file đã lưu: `python tools/topi_luna_eval.py <data>`
- Chạy thêm 2 lần mới: `python tools/topi_luna_eval.py <data> --run --runs 2 --start 5`
- Xem lỗ hổng buổi 3–4 để so tay với bảng Opus: đọc `<data>/luna_v2_rK/<id>.json` → `gaps`, đổi `seg` sang giây bằng `segments[seg].start` của transcript.
- Test: `python -m pytest -q tests/test_topi_analysis.py`

## Việc tiếp
1. (Đã xong r5–r10; dữ liệu trong cùng thư mục chấm.) r9–r10 gộp lỗ hổng theo `error_pattern` (model ghi kiểu lỗi, code gộp): band 85%/80%, độ tin cậy toán 3/7 và 5/7 — r10 đạt cả hai ngưỡng, r9 chưa. Tiếp: cho lượt attempts dùng lại đúng chữ của kiểu lỗi đã gặp; câu "lỗi này con còn lặp lại" nâng độ tin cậy; hoặc Khanh chấm tay r10. Lần chạy mới dùng `--start 11`.
2. Nếu đạt ngưỡng: nối v2 vào `pipeline.py` sau một setting, sửa `topi-api-contract.md` trước; nhánh/PR riêng.
3. Cho plan và tips dùng đầu ra v2 (trích dẫn Sai/Đúng từ `attempts`; tips theo band thấp nhất; xưng "bạn"/"con" theo audit S4).
4. Không push lên main, không deploy, không ghi DB production. Tài liệu cho Michael viết tiếng Anh; không ghi tên học sinh (D3).
