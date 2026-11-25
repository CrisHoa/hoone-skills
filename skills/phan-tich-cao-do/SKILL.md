---
name: phan-tich-cao-do
description: >
  Phân tích CAO ĐỘ trong bản vẽ DWG/DXF (bình đồ, mặt cắt, trắc dọc, chi tiết): tìm mọi ghi chú cao độ (CĐ, EL, ▽, ±, số
  thập phân trong khoảng), gán cao độ cho cấu kiện, kiểm tra nhất quán giữa các bản vẽ và với mô hình Revit, xác định hệ cao độ.
  Luôn tuân thủ cao độ ghi trên bản vẽ. Triggers: "cao độ", "cao trình", "elevation", "CĐ", "đáy hố", "đỉnh hố",
  "cao độ thiết kế", "kiểm tra cao độ", "hệ cao độ".
---

# Phân tích cao độ

Tool MCP `revit`: `cad_elev`, `cad_profile`, `cad_xyz`, `cad_dims`, `cad_find`, `cad_render`.

## Nguyên tắc bắt buộc — luôn tuân thủ cao độ
1. **Thứ tự nguồn cao độ** (dùng nguồn cao nhất có): (1) bảng thông số trắc dọc; (2) ghi chú cao độ trên mặt bằng /
   nhãn cấu kiện; (3) cao độ ghi trên mặt cắt chi tiết; (4) suy từ kích thước (đỉnh − chiều sâu ghi). Không bao giờ dùng
   cao độ đo từ hình vẽ hay Z của đường 2D.
2. Hai nguồn khác nhau quá 0.005 m → **không tự chọn**: báo cả hai, nêu nguồn, đề nghị người dùng xác nhận.
3. Cao độ của mỗi cấu kiện phải đủ và hợp lý: đỉnh > đáy cống ≥ đáy hố; độ sâu = đỉnh − đáy hố; cống ra không cao hơn cống
   vào cùng hố (trừ khi bản vẽ ghi bậc nước / bơm).
4. Ghi rõ hệ cao độ nếu bản vẽ có ghi (tìm `cad_find "h. cao ..|h.n d.u|vn.?2000|cao .. gi. .nh"`); không ghi → nói "bản vẽ
   không ghi hệ cao độ", không giả định.
5. Đơn vị: cao độ (m) thường 2–3 chữ số lẻ; kích thước chi tiết (mm). Không trộn.

## Quy trình
1. `cad_elev file zmin zmax` (đặt khoảng theo địa hình, vd 600–700) → mọi cao độ có toạ độ, layer, chuỗi gốc.
   Nhãn nhiều dòng (vd "P-16 | 637.05 | 634.53") cho nhiều giá trị cùng toạ độ — thứ tự dòng thường là đỉnh, đáy cống.
2. Cao độ theo cấu kiện: `cad_xyz` (mặt bằng + trắc dọc) — đã có đối chiếu số ghi mặt bằng ↔ trắc dọc (`ztol`).
3. Kiểm tra trắc dọc: `cad_profile` → `kiem_tra`, `doc_day_cong_tinh`.
4. Mặt cắt chi tiết (hố ga, rãnh): `cad_find "c.t|cao ..|\+\d"` + `cad_dims` để lấy chiều cao từng phần; cao độ từng lớp =
   cao độ chuẩn (từ trắc dọc) ± kích thước, ghi rõ phép tính.
5. Đối chiếu mô hình Revit: `revit_query_elements` (vd `family=HoGa`, `params=[TN_TenHoGa, TN_CaoDoDinh, TN_CaoDoDayHo,
   TN_CaoDoDayCong]`) hoặc `revit_run_python` đo cao độ hình học thật; lập bảng `cấu kiện | bản vẽ | mô hình | lệch | nguồn`.
6. Báo cáo: liệt kê điểm lệch / thiếu trước, sau đó bảng đầy đủ.
