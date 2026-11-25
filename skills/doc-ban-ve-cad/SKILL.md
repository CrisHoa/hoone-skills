---
name: doc-ban-ve-cad
description: >
  Đọc và phân tích bản vẽ AutoCAD / Civil 3D (DWG, DXF) chỉ đọc, không sửa file gốc: tổng quan, layer,
  chữ (tự giải mã TCVN3 .VnTime sang Unicode), kích thước, hình học trong một khung, block, xuất ảnh PNG
  một vùng để nhìn. Dùng khi cần đọc kích thước / ghi chú / mặt cắt từ bản vẽ thiết kế (hố ga, cống,
  rãnh, kết cấu, bình đồ, trắc dọc) để dựng mô hình BIM hoặc kiểm tra khối lượng.
  Triggers: "đọc bản vẽ", "phân tích bản vẽ", "bản vẽ dwg", "file dxf", "lấy kích thước", "mặt cắt",
  "read drawing", "analyze dwg", "dxf", "cad drawing".
---

# Đọc bản vẽ AutoCAD (DWG/DXF)

Công cụ: `scripts/cad_doc.py` (ezdxf 1.4, matplotlib). Python riêng:

```
PY={{PY}}
T={{RMCP}}/tools/cad_doc.py   (ban duy nhat, MCP "revit" cung dung file nay)
"$PY" -I "$T" <lệnh> <file.dwg|dxf> [tùy chọn]
```

Luôn **chỉ đọc**. DWG được chuyển sang DXF vào `%LOCALAPPDATA%\cad-doc\cache` bằng ODA File Converter 27.10 (dự phòng: accoreconsole AutoCAD 2025),
lần sau đọc lại từ cache; file gốc không đổi. Thêm `--json` để lấy JSON.

| Lệnh | Việc |
|---|---|
| `summary f` | phiên bản, đơn vị, phạm vi, số đối tượng theo loại, layer nhiều nhất, block, layout |
| `layers f` | layer + số đối tượng |
| `find f "<regex>"` | tìm chữ (đã giải mã TCVN3, không phân biệt hoa thường) → toạ độ. Dùng để định vị tên hình: `"m.t c.t|chi ti.t|m.t b.ng"` |
| `text f [--bbox x0 y0 x1 y1] [--layer L] [--min-h H]` | mọi TEXT/MTEXT/ATTRIB, sắp từ trên xuống |
| `dims f [--bbox ...]` | kích thước: giá trị đo thật + chữ ghi đè (nếu có) + dimstyle |
| `region f --bbox ... [--layer L] [--limit N]` | toạ độ LINE/POLYLINE/CIRCLE/ARC/INSERT/HATCH trong khung |
| `blocks f` | block được chèn + số lần + tag thuộc tính |
| `render f --out a.png [--bbox ...] [--width 1600]` | ảnh PNG nền trắng nét đen của cả bản vẽ hoặc một khung → mở ảnh ra xem |
| `convert f.dwg` | chỉ chuyển DWG → DXF, in đường dẫn |
| `elev f [--zmin --zmax]` | mọi ghi chú cao độ + toạ độ (skill `phan-tich-cao-do`) |
| `plan f [--label --symbol --pipe-layer]` | mặt bằng: X,Y + góc từng cấu kiện (skill `phan-tich-mat-bang`) |
| `profile f [--slope-tol]` | trắc dọc: bảng cao độ theo cọc/hố ga + kiểm tra (skill `phan-tich-trac-doc`) |
| `xyz f --profile-file td.dwg` | XYZ từng cấu kiện = mặt bằng + trắc dọc, đối chiếu cao độ |

`--layout TEN` để đọc paper space (mặc định Model).

## Quy trình phân tích một bản vẽ chi tiết

1. `summary` → biết đơn vị, phạm vi, có bao nhiêu chữ / kích thước, layer nào chứa kết cấu, kích thước, cốt thép.
2. `find` tên các hình (MẶT BẰNG, MẶT CẮT A-A, CHI TIẾT ...) → lấy toạ độ tiêu đề; khung của mỗi hình thường
   nằm ngay dưới/trên tiêu đề. Ước lượng `--bbox`, rồi `render --bbox` để **nhìn** và chỉnh khung cho đúng.
3. Trong từng khung: `dims` (số đo thật, tin hơn chữ ghi đè), `text` (ghi chú, vật liệu, mác bê tông, thép),
   `region --layer <layer kết cấu>` (đường bao chính xác, mặt vát, độ dốc).
4. Quy đổi về kích thước thật: hình vẽ thường theo tỷ lệ — so số đo `dims` với khoảng cách hình học trong
   `region` để biết hệ số (dimstyle kiểu `TL10`, `TL20`, `1-30` gợi ý tỷ lệ). Cao độ trên trắc dọc đọc từ chữ.
5. Đối chiếu ít nhất 2 hình (mặt bằng + mặt cắt) trước khi kết luận; ghi rõ con số lấy từ hình nào.
6. Báo cáo: bảng kích thước có nguồn (tên hình, dim/ chữ), các điểm bản vẽ không ghi / mâu thuẫn.

## Lưu ý
- Chữ tiếng Việt font `.VnTime/.VnArial` (TCVN3) được giải mã tự động; chuỗi đã là Unicode giữ nguyên.
  Vài chuỗi lỗi sẵn trong file gốc (ví dụ `THéP GóC`) — đọc theo ngữ cảnh.
- Bản vẽ Civil 3D: đối tượng AECC xuất ra DXF dưới dạng proxy/block; nhãn trắc dọc là TEXT/MTEXT đọc được bằng `text`/`find`.
- File lớn: luôn lọc `--bbox`/`--layer`; `region` mặc định tối đa 500 đối tượng.
- Nếu đọc DWG báo lỗi: mở file trong AutoCAD, `DXFOUT` thủ công rồi đọc file .dxf. (accoreconsole hiện crash do plugin HOONE tạo Ribbon ở chế độ console.)
