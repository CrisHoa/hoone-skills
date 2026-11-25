---
name: phan-tich-mat-bang
description: >
  Phân tích bản vẽ MẶT BẰNG / BÌNH ĐỒ (DWG/DXF) để lấy toạ độ X,Y (E,N VN2000) và góc xoay của từng cấu kiện
  (hố ga, cửa thu, cống, rãnh...), tuyến ống nối giữa các cấu kiện, rồi ghép với trắc dọc thành XYZ từng cấu kiện.
  Luôn tuân thủ toạ độ và cao độ bản vẽ. Triggers: "mặt bằng", "bình đồ", "toạ độ hố ga", "vị trí cấu kiện",
  "xyz", "E N", "VN2000", "định vị", "plan".
---

# Phân tích mặt bằng → XYZ từng cấu kiện

Tool MCP `revit`: `cad_plan`, `cad_xyz`, `cad_summary`, `cad_find`, `cad_render`, `cad_region`.
Script: `{{PY}} -I {{RMCP}}/tools/cad_doc.py plan|xyz <file> --json`

## Nguyên tắc bắt buộc
1. **X,Y lấy từ đối tượng hình học của cấu kiện** (block cấu kiện, đầu tuyến ống), **không** lấy vị trí chữ nhãn.
   Mỗi cấu kiện ghi `nguon_xy` (block nào / đầu tuyến ống) và `cach_chu` (nhãn cách cấu kiện bao xa).
2. Bản vẽ đặt đúng hệ VN2000 (toạ độ ~ 400 000 / 1 300 000, đơn vị m) → X = E, Y = N. Nếu toạ độ nhỏ (bản vẽ cục bộ) →
   báo người dùng, phải có điểm khống chế / bảng toạ độ để chuyển, không tự đoán.
3. **Z chỉ lấy từ trắc dọc hoặc ghi chú cao độ** (skill `phan-tich-trac-doc`, `phan-tich-cao-do`); không lấy Z của đối tượng
   2D (thường = 0).
4. Mỗi cấu kiện trong báo cáo phải có đủ: tên, X, Y, góc xoay (nếu có), cao độ đỉnh, đáy cống (vào/ra), đáy hố,
   nguồn từng số. Thiếu → ghi "không có trên bản vẽ".
5. Cảnh báo (`canh_bao`) không được bỏ qua: xem `cad_render --bbox` quanh cấu kiện để xác nhận trước khi dùng số.

## Quy trình
1. `cad_summary` → đơn vị, phạm vi toạ độ, layer (tìm layer cấu kiện kiểu `C-STRM-STRC`, tim ống `C-STRM-CNTR`).
2. `cad_plan file` (mặc định nhận tên dạng T-1, P-12, HGT5, HG3...; khác → truyền `label` regex; block cấu kiện khác →
   `symbol`; layer tim ống khác → `pipe_layer`). Kết quả: `x, y, goc_xoay, nguon_vi_tri, cach_chu, so_ghi_kem, canh_bao`.
   - Nhãn Civil 3D thường kèm cao độ dưới tên (`so_ghi_kem` = [đỉnh, đáy cống]) → dùng để đối chiếu, không thay trắc dọc.
3. `cad_xyz file profile_file=<trắc dọc>` → XYZ từng cấu kiện + đối chiếu cao độ mặt bằng ↔ trắc dọc + danh sách cấu kiện
   có trên bản vẽ này mà không có trên bản vẽ kia.
4. Báo cáo bảng: `tên | E | N | góc | đỉnh | đáy cống | đáy hố | nguồn XY | nguồn Z | cảnh báo`.
5. So với mô hình Revit (nếu đang mở): `revit_query_elements` family hố ga, params `TN_TenHoGa, TN_CaoDoDinh, TN_CaoDoDayHo`;
   vị trí phần tử (`revit_get_element` → `point_m` là toạ độ nội bộ; toạ độ chung = nội bộ + gốc `revit_info.shared_origin_m`).
   Lập bảng lệch; lệch > 0.05 m XY hoặc > 0.005 m Z → báo.
