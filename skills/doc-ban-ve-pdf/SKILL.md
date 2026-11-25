---
name: doc-ban-ve-pdf
description: >
  Đọc và phân tích bản vẽ kỹ thuật và tài liệu PDF (bản vẽ thiết kế A0–A4, hồ sơ BIM, thuyết minh, báo cáo,
  bảng khối lượng, bản PDF scan) chỉ đọc, không sửa file gốc: tổng quan số trang/khổ giấy/mục lục, tìm kiếm chữ,
  trích xuất văn bản và bảng biểu, xuất ảnh PNG độ phân giải cao (cả trang hoặc phóng to từng vùng chi tiết) để đọc
  kích thước/cao độ và đối chiếu với mô hình Revit hoặc bản vẽ CAD.
  Triggers: "đọc pdf", "phân tích pdf", "bản vẽ pdf", "hồ sơ pdf", "file pdf", "đọc bản vẽ pdf",
  "trích xuất pdf", "bảng trong pdf", "pdf scan", "read pdf", "analyze pdf".
---

# Đọc bản vẽ & tài liệu PDF (chỉ đọc)

Công cụ: `scripts/pdf_doc.py` (dùng `PyMuPDF / fitz`). Python riêng:

```
PY={{PY}}
T=<thư-mục-skill>/doc-ban-ve-pdf/scripts/pdf_doc.py
"$PY" "$T" <lệnh> <file.pdf> [tùy chọn]
```

Nếu máy chưa cài `pymupdf` trong môi trường `{{PY}}`, cài 1 lần:
`{{PY}} -m pip install pymupdf`

Luôn **chỉ đọc** — không bao giờ chỉnh sửa file PDF gốc. Thêm `--json` để lấy đầu ra JSON.

| Lệnh | Việc |
|---|---|
| `summary f.pdf` | số trang, khổ giấy (A0–A4), tiêu đề, mục lục, phát hiện trang scan/ảnh |
| `find f.pdf "<regex>" [--pages 1-5]` | tìm chữ (không phân biệt hoa thường, hỗ trợ tiếng Việt) → số trang + dòng chứa kết quả |
| `text f.pdf [--pages 1-3,5] [--clip x0 y0 x1 y1]` | trích xuất toàn bộ chữ theo trang hoặc trong 1 vùng cắt (tỷ lệ `0..1`) |
| `tables f.pdf [--pages 1-5]` | trích xuất bảng biểu (thống kê thép, khối lượng, bảng tọa độ, bảng thông số) |
| `render f.pdf --page N --out out.png [--dpi 200] [--clip x0 y0 x1 y1]` | xuất trang PDF hoặc phóng to 1 vùng chi tiết ra ảnh PNG để AI xem trực tiếp |

## Quy trình phân tích bản vẽ kỹ thuật PDF

1. **`summary`** → biết tổng số trang, khổ giấy (A1/A3 bản vẽ hay A4 thuyết minh), trang nào có chữ thật (vector PDF) và trang nào là bản scan (`[SCAN]`).
2. **`find`** tên hình / hạng mục / cấu kiện (vd `"MẶT BẰNG|MẶT CẮT|HỐ GA|CAO ĐỘ|THỐNG KÊ"`) → xác định đúng trang cần đọc.
3. **Với hồ sơ / thuyết minh / bảng biểu**: dùng `text --pages ...` và `tables --pages ...` để trích xuất chính xác số liệu.
4. **Với bản vẽ A0–A3 hoặc bản scan**:
   - Dùng `render --page N --dpi 180` xuất toàn trang ra ảnh PNG → mở ảnh để xác định bố cục các hình (mặt bằng, mặt cắt, khung tên, bảng ghi chú).
   - Phóng to từng vùng chi tiết (kích thước nhỏ, cao độ, ghi chú vật liệu) bằng `--clip x0 y0 x1 y1 --dpi 300` (tọa độ tỷ lệ từ `0.0` đến `1.0`, gốc trên-trái) → mở ảnh phóng to để đọc chính xác từng con số.
5. **Đối chiếu với Revit / CAD**: kết hợp skill `revit-bim-mcp`, `doc-ban-ve-cad`, `phan-tich-cao-do` để lập bảng so sánh (`bản vẽ PDF | mô hình Revit | lệch`), luôn ghi rõ **số trang** và **tên hình/bảng** làm nguồn cho từng con số.

## Nguyên tắc bắt buộc
- **Không đoán số mờ**: nếu chữ/kích thước trên ảnh toàn trang nhỏ hoặc mờ, bắt buộc `render` lại với `--clip` và `--dpi 300` (hoặc `400`) để đọc rõ trước khi kết luận.
- **Ghi rõ nguồn**: mọi kích thước, cao độ, khối lượng trích từ PDF đều kèm `Tên file | Trang N | Tên hình hoặc bảng`.
- **Phân biệt đơn vị**: cao độ thường theo `m`, kích thước chi tiết bản vẽ theo `mm` hoặc `cm` — đọc kỹ khung tên / ghi chú đơn vị trên trang bản vẽ trước khi quy đổi.
- Ảnh PNG xuất tạm để xem lưu vào thư mục tạm (`%TEMP%` hoặc thư mục scratch), không xả rác vào thư mục dự án của người dùng.
