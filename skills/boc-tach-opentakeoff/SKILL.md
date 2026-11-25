---
name: boc-tach-opentakeoff
description: >
  Bóc tách khối lượng (Quantity Takeoff / QTO) trực tiếp từ bản vẽ PDF / ảnh mặt bằng bằng MCP server "opentakeoff"
  (70 công cụ chuẩn OpenTakeoff: đo diện tích phòng, chiều dài tường/ống, bề mặt, đếm thiết bị, quét ký hiệu, lập bảng dự toán,
  xuất PDF đánh dấu kiểm chứng & DXF) và đối chiếu chéo với mô hình Revit BIM.
  Triggers: "opentakeoff", "takeoff", "bóc tách bản vẽ pdf", "đo diện tích từ pdf", "đếm thiết bị pdf",
  "xuất pdf đánh dấu", "marked pdf", "dự toán từ bản vẽ", "measure polygon", "quantity takeoff".
---

# Bóc Tách Khối Lượng Bản Vẽ PDF Bằng MCP `opentakeoff` (70 Tools)

MCP Server **`opentakeoff`** (`npx -y opentakeoff-mcp`, tự động đăng ký cùng bộ `MCP - Revit Hoone`) cung cấp đúng bộ máy hình học & kiểm soát tỷ lệ chuẩn của OpenTakeoff.

## 5 Nguyên Tắc Bắt Buộc Khi Bóc Tách (An Toàn Dự Toán)
1. **Cổng tỷ lệ là bắt buộc (Scale Gate)**: Công cụ đo từ chối đo khi chưa đặt tỷ lệ. Luôn đọc ghi chú tỷ lệ trên bản vẽ rồi gọi `set_scale` tường minh (`set_scale { use_detected: true }` hoặc hiệu chuẩn theo 1 kích thước biết trước). Luôn báo rõ `scale_confirmed: false` để kỹ sư xác nhận khi bàn giao.
2. **Đo trên mặt trong tường (Wall-Face Tracing)**: Dùng `get_sheet_vectors` đọc nét tường thật, vẽ đa giác theo mặt trong tường bằng `measure_polygon` (băng qua cửa theo tim tường), rồi **bắt buộc** gọi `view_sheet` nhìn ảnh kiểm chứng trước khi sang phòng tiếp theo.
3. **Mọi đề xuất của AI là nét đứt (Proposal)**: Kết quả AI tạo ra nằm ở trạng thái đề xuất (`AGENT`) để kỹ sư kiểm tra và bấm chấp nhận (`APPROVED`) trên OpenTakeoff Canvas — không tự ý giả định là đã duyệt.
4. **"Không chắc chắn" là một câu trả lời hợp lệ (Withheld)**: Nếu bản vẽ mờ, thiếu kích thước hoặc ký hiệu trùng lặp, dừng lại báo tọa độ & lý do thay vì bịa số.
5. **Sản phẩm bàn giao luôn kèm PDF đánh dấu**: Luôn xuất `export_marked_pdf` (bản vẽ có tô màu + bảng tổng hợp chú giải) cùng `export_report` / `export_estimate`, không chỉ trả JSON thô.

## Bản Đồ 70 Công Cụ MCP `opentakeoff` Theo Giai Đoạn

| Giai đoạn | Các tool chính |
|---|---|
| **1. Mở & Định hướng** | `load_plan`, `sheet_info`, `sheet_context`, `get_sheet_vectors`, `read_sheet_text`, `find_text`, `view_sheet` |
| **2. Đặt tỷ lệ** | `set_scale` |
| **3. Đo & Đếm** | `measure_polygon` (diện tích), `cut_out` (trừ lỗ mở), `measure_line` (chiều dài), `measure_surface` (diện tích tường), `place_count` / `count_marks` (đếm thiết bị) |
| **4. Quét hàng loạt & Suy diễn** | `symbol_sweep`, `sweep_schedule_row`, `derive_base` (len chân tường), `derive_transitions` (nẹp chuyển tiếp), `apply_rules` |
| **5. Đọc bộ bản vẽ & Bảng thống kê** | `sheet_graph`, `resolve_tag`, `find_schedule` |
| **6. Chỉnh sửa & Kiểm tra trùng** | `list_shapes`, `edit_shape`, `edit_condition`, `edit_materials`, `duplicate_condition`, `split_condition`, `delete_shape`, `undo_last`, `scope_duplicates`, `scope_merge` |
| **7. Đề xuất duyệt & Ghi chú / RFI** | `propose_takeoff`, `annotate`, `mark_verdict`, `create_rfi`, `list_rfis`, `resolve_rfi` |
| **8. Áp đơn giá & Dự toán** | `set_pricing`, `set_estimate_settings`, `estimate_summary`, `export_estimate`, `export_proposal` *(đơn giá phải do kỹ sư cung cấp, AI không tự bịa giá)* |
| **9. Xuất bàn giao** | `takeoff_summary`, `export_takeoff`, `export_report`, `export_marked_pdf`, `export_dxf`, `import_takeoff` |

## Quy Trình Chuẩn 6 Bước (Kết Hợp Đối Chiếu Revit BIM)
1. Gọi `load_plan` mở file bản vẽ PDF → `sheet_info` + `read_sheet_text` tìm tỷ lệ và bảng vật liệu (`find_schedule`).
2. Gọi `set_scale` đặt tỷ lệ chuẩn cho từng tờ bản vẽ.
3. Dùng `get_sheet_vectors` + `measure_polygon` / `measure_line` / `place_count` để đo từng hạng mục.
4. Gọi `view_sheet` kiểm tra trực quan đường bao đã vẽ (nếu lệch nét tường → sửa bằng `edit_shape`).
5. Gọi `takeoff_summary` + `export_marked_pdf` + `export_report` để bàn giao.
6. *(Khi có mô hình Revit đang mở)* Đối chiếu trực tiếp kết quả `takeoff_summary` với khối lượng mô hình từ skill **`revit-thong-ke-khoi-luong`**, lập bảng `Hạng mục | Bản vẽ PDF (OpenTakeoff) | Mô hình Revit | Chênh lệch (%)` để phát hiện thiếu/thừa cấu kiện.
