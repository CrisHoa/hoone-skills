---
name: polyline-3d-cao-do
description: >
  Đọc, trích xuất và nội suy cao độ Z từ đối tượng Polyline 3D (3D POLYLINE, SPLINE 3D, LINE 3D, 3DFACE, Civil 3D Feature Line)
  trong bản vẽ DWG/DXF (chỉ đọc, không sửa file gốc): liệt kê các tuyến 3D theo layer, xuất danh sách đỉnh XYZ + lý trình + độ dốc,
  rải mẫu đều theo bước lý trình (--step) kèm vector tiếp tuyến để đưa vào Adaptive Component trong Revit, và nội suy cao độ Z
  tại bất kỳ điểm (X, Y) nào trên mặt bằng.
  Triggers: "polyline 3d", "3d polyline", "lấy cao độ từ polyline", "đường 3d", "feature line", "nội suy cao độ 3d",
  "xuất xyz từ polyline", "rải điểm 3d", "tim tuyến 3d".
---

# Đọc & Lấy Cao Độ Từ Polyline 3D (DWG / DXF)

Công cụ chỉ đọc (không sửa file gốc), tự động chuyển `.dwg` → `.dxf` qua ODA File Converter (dùng chung cache `%LOCALAPPDATA%\cad-doc\cache`):

```bash
PY={{PY}}
T={{RMCP}}/skills/polyline-3d-cao-do/scripts/poly3d_elev.py
"$PY" -I "$T" <lệnh> <file.dwg|dxf> [tùy chọn]
```

## Các lệnh hỗ trợ

| Lệnh | Mục đích | Ví dụ |
|---|---|---|
| `list <file> [--layer L]` | Liệt kê tất cả đối tượng 3D (3D Polyline, Spline 3D, Line 3D, LWPolyline có elevation ≠ 0): handle, layer, số đỉnh, chiều dài 2D/3D, `Z_min`, `Z_max`, độ dốc min/max | `list tuyen.dwg --layer TIM --json` |
| `vertices <file> --handle H` | Xuất toàn bộ đỉnh `(STT, E, N, Z, ly_trinh_2d, ly_trinh_3d, doc_%)` của 1 đường 3D | `vertices tuyen.dwg --handle 1A4F --json` |
| `sample <file> --handle H --step 5.0` | Rải mẫu đều theo bước lý trình 2D (m) — giữ nguyên mọi đỉnh gãy + chèn điểm chia đều, trả về `E, N, Z, station, azimuth_deg, grade_pct` sẵn sàng nạp vào Revit Adaptive Component | `sample tuyen.dwg --handle 1A4F --step 2.0 --json` |
| `query <file> --handle H --pt X Y` | Chiếu vuông góc điểm `(X, Y)` lên Polyline 3D → nội suy tuyến tính chính xác cao độ `Z`, lý trình `station`, độ lệch ngang `offset_m` | `query tuyen.dwg --handle 1A4F --pt 451230.5 1320110.2` |

*(Có thể dùng `--layer <regex>` thay cho `--handle` nếu muốn lấy đường 3D dài nhất trên layer đó, hoặc `--pts-file points.json` để nội suy hàng loạt nhiều điểm cùng lúc.)*

## Nguyên tắc bắt buộc
1. **Kiểm tra đơn vị bản vẽ trước**: Nếu tọa độ `X, Y` cỡ 400 000 / 1 300 000 và `Z` cỡ vài mét đến vài trăm mét → đơn vị là **mét (VN2000)**. Nếu `Z` cỡ hàng chục nghìn → kiểm tra xem bản vẽ đang để đơn vị **mm** hay không (`--scale 0.001` để đổi mm → m), **không tự đoán**.
2. **Phân biệt Polyline 2D (Z=0) với Polyline 3D thật**: Nếu lệnh `list` báo toàn bộ đối tượng có `Z_min == Z_max == 0` → bản vẽ mặt bằng chỉ là **2D phẳng**, phải chuyển sang skill `suy-luan-cao-do-tu-trac-doc` để ghép với trắc dọc, **không** dùng `Z=0`.
3. **Báo rõ nguồn & sai số chiếu ngang**: Khi nội suy điểm `(X, Y)` bằng `query`, luôn báo kèm `offset_m` (khoảng cách từ điểm hỏi tới tim đường 3D). Nếu `offset_m > 0.5 m` mà chưa có độ dốc ngang, phải cảnh báo người dùng.
4. **Kết nối thẳng sang Revit**: Đầu ra `--json` của `sample` có sẵn mảng `points: [{station, x, y, z, azimuth_deg, grade_pct}]`, truyền thẳng vào `revit_run_python` (skill `tao-family-adaptive`) để rải đốt Adaptive Component bám đúng tuyến 3D.
