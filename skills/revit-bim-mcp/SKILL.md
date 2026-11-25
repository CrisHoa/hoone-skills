---
name: revit-bim-mcp
description: >
  Điều khiển Revit 2025 và đọc bản vẽ AutoCAD qua MCP server "revit" (RevitMCP): tra cứu phần tử, gán tham số,
  mở view, xuất ảnh, chạy script Python/Dynamo trong Revit, và đọc DWG/DXF (cad_*) để dựng hoặc kiểm tra mô hình BIM
  theo bản vẽ. Dùng cho dự án thoát nước "THOAT NUOC_BIM" (hố ga, cống, gối, rãnh dẫn nước) và mọi mô hình Revit đang mở.
  Triggers: "revit", "mô hình bim", "hố ga", "cống", "family", "dynamo", "khối lượng", "đọc bản vẽ", "dwg", "dxf",
  "đối chiếu bản vẽ", "kiểm tra mô hình".
---

# Revit + bản vẽ qua MCP "revit"

Server: `node {{RMCP}}/server/index.js` (khai báo `mcpServers.revit`). Revit phải đang mở và tab
**AI MCP → Đang bật** (xanh). Nếu tool báo "Không kết nối được Revit" → nhắc người dùng mở Revit / bấm bật.

## Tool Revit (chạy trong luồng Revit API)
| Tool | Khi nào dùng |
|---|---|
| `revit_info` | đầu phiên: dự án, view hiện hành, đơn vị (mm), gốc toạ độ chung VN2000, Python sẵn sàng chưa |
| `revit_query_elements` | tìm phần tử: `family` (vd `HoGa_D1000`), `category` (`OST_GenericModel`), lọc `param`/`value`, trả `params` |
| `revit_get_element` | toàn bộ tham số + vị trí 1 phần tử |
| `revit_set_parameter` | gán tham số nhiều phần tử; số đo nhập theo đơn vị hiển thị (mm) |
| `revit_list_views`, `revit_activate_view`, `revit_zoom_to`, `revit_select` | điều hướng cho người dùng xem |
| `revit_export_image` | ảnh PNG một view để tự kiểm tra |
| `revit_save` | lưu dự án sau khi sửa (hỏi người dùng trước nếu thay đổi lớn) |
| `revit_post_command` | lệnh Revit dựng sẵn (vd `ExitRevit` — bị chặn khi chưa lưu) |
| `revit_run_python` | code hoặc file Python (CPython3 Dynamo). Có `doc`, `uidoc`, `uiapp`, `IN`; trả `OUT` + stdout. Python 3.9 tự khởi động lần gọi đầu, không cần mở Dynamo |

Chuỗi script của dự án thoát nước: `revit_run_python` với
`file = C:/Users/Admin/Desktop/Family Cong/BIM/script/chay_chuoi.py`, `input = ["<bước>,<bước>"]`.
Các bước: `hoga, locong, ranh, naplai, rai, gan, valo, trich, kt, luu, mc, anh, zoom, toado, doiranh, anhranh`
(xem `BUOC` trong chay_chuoi.py). Kết quả ghi ở `BIM/data/_log_chuoi.txt`. Quy tắc mô hình: `BIM/BIM_SPEC.md`.

## Tool đọc bản vẽ (cục bộ, không cần Revit, chỉ đọc)
Phân tích chuyên sâu: skill `phan-tich-mat-bang` (`cad_plan`, `cad_xyz`), `phan-tich-trac-doc` (`cad_profile`), `phan-tich-cao-do` (`cad_elev`) — luôn tuân thủ cao độ, XYZ từng cấu kiện có nguồn.
`cad_summary` → `cad_find` (định vị tên hình) → `cad_render` với `bbox` (nhìn ảnh, chỉnh khung) →
`cad_dims` / `cad_text` / `cad_region` trong khung → `cad_blocks`, `cad_layers` khi cần.
DWG tự chuyển DXF bằng ODA File Converter; chữ TCVN3 tự giải mã.

## Quy trình đối chiếu bản vẽ ↔ mô hình
1. Đọc bản vẽ: kích thước từ `cad_dims` (số đo thật), ghi chú vật liệu từ `cad_text`; đối chiếu ít nhất mặt bằng + một mặt cắt.
2. Đọc mô hình: `revit_query_elements` lấy tham số family tương ứng; hoặc `revit_run_python` đo hình học.
3. Lập bảng so sánh (bản vẽ | mô hình | lệch), ghi rõ nguồn từng số.
4. Sửa: ưu tiên sửa script tạo family / script rải rồi chạy lại qua `chay_chuoi.py`, không sửa tay từng phần tử
   (mô hình phải tái lập được). Sau đó `revit_export_image` để kiểm tra, rồi `revit_save`.

## An toàn
- Không xoá hàng loạt / lưu đè khi chưa nói với người dùng. Bước `naplai` xoá family và instance — chỉ chạy khi cần nạp lại family.
- Tool `cad_*` không bao giờ sửa file bản vẽ.
- Luôn điều khiển Revit bằng tool MCP (không click chuột / không bấm Dynamo). Việc chạy lâu: `revit_run_python` với `timeout_s` lớn.
