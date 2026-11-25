---
name: phan-tich-trac-doc
description: >
  Phân tích bản vẽ TRẮC DỌC (cống, rãnh, đường, ống) từ DWG/DXF: đọc bảng thông số theo từng cọc / hố ga
  (tên, lý trình, khoảng cách, cao độ đỉnh, thiết kế, tự nhiên, đáy cống, đáy hố, độ dốc, đường kính), tính độ sâu,
  kiểm tra độ dốc ghi so với cao độ, xuất cao độ Z cho từng cấu kiện. Luôn tuân thủ cao độ ghi trên bản vẽ.
  Triggers: "trắc dọc", "cao độ đáy cống", "độ dốc cống", "lý trình", "MSS", "profile", "đọc trắc dọc", "kiểm tra cao độ".
---

# Phân tích trắc dọc

Tool MCP `revit` (không cần mở Revit): `cad_profile`, `cad_profile_tn_tk`, `cad_find`, `cad_render`, `cad_text`, `cad_xyz`.
Không có MCP thì chạy script:
`{{PY}} -I {{RMCP}}/tools/cad_doc.py profile <file> --json`

## Nguyên tắc bắt buộc — tuân thủ cao độ
1. **Cao độ lấy từ BẢNG THÔNG SỐ của trắc dọc** (số ghi), không đo từ hình vẽ đường đỏ/đường đen, không tự nội suy.
   Chỉ nội suy khi bản vẽ không ghi, và phải ghi rõ "nội suy giữa A và B".
2. Mỗi cấu kiện phải có đủ cao độ bản vẽ cho: đỉnh (hoặc thiết kế), đáy cống vào/ra, đáy hố. Thiếu → báo thiếu, không đoán.
3. Giữ nguyên số lẻ như bản vẽ (thường 2 chữ số, m). Không làm tròn lại.
4. Hố ga có 2 cao độ đáy cống (vào ≠ ra) → giữ cả hai (danh sách theo thứ tự trái→phải = vào→ra theo chiều trắc dọc).
5. Mọi con số trong báo cáo kèm nguồn: tên file, tên bảng (vị trí `bang_x, bang_y`), tên dòng, tên cột.

## Quy trình
1. `cad_profile file` → danh sách bảng (mỗi tuyến/đoạn một bảng). Mỗi bảng: `dong` (nhãn dòng nhận được), `cot` (từng cọc / hố ga),
   `kiem_tra` (lỗi nhất quán), `doc_day_cong_tinh` (độ dốc tính lại), `mss`.
2. Kiểm tra `dong` đã nhận đúng các dòng cần thiết. Nếu thiếu dòng hoặc gộp cột sai → `cad_find` tên dòng, `cad_render --bbox`
   bảng để nhìn, rồi gọi lại với `bbox` chỉ bảng đó, chỉnh `tol` (gộp cột) / `span` (chiều dài bảng).
3. Đọc `kiem_tra` và `doc_day_cong_tinh`:
   - `đáy cống ≥ đỉnh`, `đáy hố > đáy cống` → lỗi bản vẽ hoặc đọc sai cột → xem ảnh để xác nhận.
   - `lech_doc_%` lớn: độ dốc ghi không khớp chênh cao đáy cống / khoảng cách ghi. Có thể do hố ga có bậc rơi, cống ra
     không cùng đáy, khoảng cách tính từ mép hố → nêu rõ, không tự sửa số.
4. Xuất kết quả: bảng `tên | lý trình | đỉnh | đáy cống vào | đáy cống ra | đáy hố | độ sâu | độ dốc ghi | độ dốc tính | ghi chú`.
5. Khi cần XYZ đầy đủ → kết hợp mặt bằng bằng `cad_xyz` (xem skill `phan-tich-mat-bang`).

## Lưu ý
- Nhãn dòng nhận diện tự động: tên/số hiệu, lý trình, khoảng cách/cự ly, độ dốc, cao độ đỉnh/nắp, cao độ thiết kế/mặt đường,
  cao độ tự nhiên, cao độ đáy cống/ống, cao độ đáy hố/giếng, độ sâu. Chữ TCVN3 được giải mã trước khi nhận.
- Cột khoảng cách / độ dốc nằm giữa 2 cọc → là cột riêng, được dùng để kiểm tra độ dốc của đoạn đó.
- `MSS` (mức so sánh) chỉ để đọc hình, không thay cho số trong bảng.

## Cao độ tự nhiên và cao độ thiết kế (phân tích riêng)
`cad_profile_tn_tk file` (script: lệnh `tntk`) → mỗi bảng trắc dọc: danh sách cọc / hố ga với `cd_tu_nhien`, `cd_thiet_ke`,
`chenh_tk_tn` (thiết kế − tự nhiên, + là đắp, − là đào), `dao_dap`, điểm `thieu` số liệu; `tong_hop` min/max từng loại và
số điểm đào/đắp; `nguon_thiet_ke` ghi rõ dòng nào được dùng.
- Trắc dọc cống không có dòng "cao độ thiết kế" → dùng "cao độ đỉnh hố ga" làm cao độ thiết kế và GHI RÕ điều đó.
- Bảng trắc ngang (có dòng "khoảng cách mia") bị bỏ qua, `all=true` để lấy.
- Báo cáo luôn tách hai cột tự nhiên / thiết kế, không gộp; điểm chỉ có một trong hai thì ghi thiếu, không tự điền.
