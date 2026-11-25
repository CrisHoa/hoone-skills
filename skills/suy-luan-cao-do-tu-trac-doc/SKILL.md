---
name: suy-luan-cao-do-tu-trac-doc
description: >
  Đọc bảng thông số TRẮC DỌC (lý trình, cao độ thiết kế / tự nhiên / đáy cống, đường cong đứng Parabol) kết hợp
  với MẶT BẰNG TIM TUYẾN 2D (DWG/DXF có Z=0, bao gồm cả đoạn cong tròn bulge) để suy luận, nội suy và gán cao độ Z
  chính xác thành chuỗi tọa độ 3D (E, N, Z) dọc tuyến hoặc tại các điểm dịch ngang (mép đường, rãnh, bó vỉa, hố ga).
  Triggers: "suy luận cao độ", "ghép trắc dọc với mặt bằng", "tim tuyến 2d sang 3d", "dựng 3d từ trắc dọc",
  "gán cao độ từ trắc dọc", "nội suy cao độ theo lý trình", "alignment 2d + profile", "cao độ tim tuyến 2d".
---

# Suy Luận Cao Độ 3D Từ Mặt Bằng Tim Tuyến 2D + Trắc Dọc

Khi bản vẽ mặt bằng chỉ có **tim tuyến 2D (`Z = 0`)** còn cao độ nằm ở **bản vẽ trắc dọc**, dùng quy trình 3 bước sau để suy luận chính xác tọa độ **3D `(E, N, Z)`** (và đưa thẳng vào Revit qua skill `tao-family-adaptive`).

## Công cụ CLI (chỉ đọc, không sửa file gốc)
```bash
PY={{PY}}
T={{RMCP}}/skills/suy-luan-cao-do-tu-trac-doc/scripts/align_2d_profile_3d.py
"$PY" -I "$T" build --plan <mat_bang.dwg|dxf> --profile-json <trac_doc.json> [tùy chọn]
```

## Quy trình chuẩn 4 bước

1. **Bước 1 — Đọc bảng thông số Trắc dọc** (dùng MCP `cad_profile` / `cad_profile_tn_tk` theo skill `phan-tich-trac-doc`):
   - Lấy danh sách các cọc / hố ga theo đúng thứ tự lý trình: `ly_trinh (m)` (hoặc `Km0+120.50` → `120.50`), `cd_thiet_ke` (hoặc `cd_day_cong`), `cd_tu_nhien`, và bán kính đường cong đứng `R` (nếu có PVI cong đứng Parabol).
   - Lưu thành file JSON dạng:
     ```json
     [
       {"station": 0.0, "z_tk": 12.50, "z_tn": 11.80},
       {"station": 45.0, "z_tk": 13.40, "z_tn": 12.10, "r_vert": 1500.0},
       {"station": 100.0, "z_tk": 12.85, "z_tn": 12.60}
     ]
     ```
     *(Hoặc truyền trực tiếp file JSON kết quả xuất từ `cad_profile` — script tự nhận diện cột `ly_trinh`, `cd_thiet_ke`, `cd_dinh`, `cd_tu_nhien`, `cd_day_cong`!)*

2. **Bước 2 — Xác định tim tuyến 2D trên Mặt bằng**:
   - Dùng `cad_layers` / `poly3d_elev.py list <mat_bang.dwg>` để tìm đúng `--layer` hoặc `--handle` của đường tim tuyến 2D (`LWPOLYLINE` có hỗ trợ cung tròn `bulge`, `POLYLINE`, `SPLINE`, `LINE`).
   - Kiểm tra chiều tuyến: điểm đầu polyline 2D phải trùng cọc đầu trắc dọc (`--start-station`). Nếu bị ngược chiều → thêm cờ **`--reverse`**.

3. **Bước 3 — Chạy suy luận & đối chiếu chiều dài**:
   ```bash
   "$PY" -I "$T" build \
     --plan mat_bang.dwg --layer "TIM|ALIGN|CNTR" \
     --profile-json trac_doc.json \
     --start-station 0.0 \
     --step 2.0 \
     --offset 0.0 --cross-slope -2.0 \
     --out tuyen_3d.json
   ```
   - **Kiểm tra đối soát tự động**: Script so sánh tổng chiều dài hình học 2D của tim tuyến với khoảng lý trình trắc dọc (`station_end - station_start`). Nếu lệch **> 0.5 m** → phát cảnh báo (có thể do sai tỷ lệ bản vẽ, thiếu đoạn tuyến hoặc ngược chiều), **không tự ý bỏ qua**.
   - **Đường cong đứng Parabol**: Khi điểm PVI có `r_vert` (bán kính cong đứng $R$, m), script tự tính chiều dài cong $L = R \cdot |i_2 - i_1|$ và hiệu chỉnh parabol $\Delta z = \pm \frac{x^2}{2R}$ thay vì nội suy thẳng gãy khúc.
   - **Dịch ngang sang mép đường / rãnh / hố ga**: Truyền `--offset <m>` (`+` bên phải tuyến, `-` bên trái tuyến) và `--cross-slope <%>` (vd `-2.0` cho mái dốc ngang 2%) để suy ra tọa độ 3D chính xác ở mép công trình:
     $$Z_{\text{mép}} = Z_{\text{tim}} + |\text{offset}| \cdot \frac{\text{cross\_slope}}{100}$$

4. **Bước 4 — Đưa vào Revit (Adaptive Component / Đường 3D)**:
   - Đọc `tuyen_3d.json` bằng `revit_run_python` (xem skill `tao-family-adaptive`) để rải Family Adaptive hoặc dựng `ModelCurve` 3D đúng tọa độ VN2000 và cao độ thiết kế.

## Nguyên tắc kiểm soát sai số
- **Luôn ghi rõ nguồn cao độ**: số lấy trực tiếp tại cọc trắc dọc ghi `"nguon": "bang_trac_doc"`, điểm nằm giữa 2 cọc ghi rõ `"nguon": "noi_suy_tuyen_tinh"` hoặc `"noi_suy_parabol_R=..."`.
- **Cảnh báo vượt phạm vi**: Nếu điểm cần hỏi nằm ngoài khoảng `[station_min, station_max]` của trắc dọc → báo `"ngoai_pham_vi_trac_doc"`, tuyệt đối không tự ngoại suy bừa.
- **Độ chính xác**: Giữ 3–4 chữ số thập phân (m); khi đối chiếu với mô hình Revit, sai số cho phép **≤ 0.005 m**.
