# hoone-skills

Skill cho AI (Claude Code, Antigravity) dùng cùng bộ **MCP - Revit Hoone** (Revit 2025 + đọc bản vẽ AutoCAD).

| Skill | Nội dung |
|---|---|
| `revit-bim-mcp` | Điều khiển Revit qua MCP `revit`, quy trình đối chiếu bản vẽ ↔ mô hình |
| `doc-ban-ve-cad` | Đọc / phân tích bản vẽ DWG, DXF (chỉ đọc, giải mã TCVN3) |
| `doc-ban-ve-pdf` | Đọc / phân tích bản vẽ kỹ thuật & tài liệu PDF (chỉ đọc, trích bảng, xuất ảnh phóng to) |
| `phan-tich-cao-do` | Phân tích cao độ, luôn tuân thủ cao độ bản vẽ |
| `phan-tich-mat-bang` | Mặt bằng / bình đồ → X,Y từng cấu kiện, ghép XYZ |
| `phan-tich-trac-doc` | Trắc dọc: cao độ theo cọc / hố ga, tự nhiên – thiết kế, độ dốc |
| `tao-family-adaptive` | Tạo & rải Adaptive Component Family (.rfa) bám tuyến cong 3D trong Revit |
| `polyline-3d-cao-do` | Đọc, rải mẫu & nội suy cao độ Z từ Polyline 3D / Spline 3D (DWG/DXF) |
| `suy-luan-cao-do-tu-trac-doc` | Ghép mặt bằng tim tuyến 2D + trắc dọc (gồm cong đứng Parabol) → tuyến 3D XYZ |
| `revit-dung-hinh-co-ban` | Dựng hình hàng loạt Level, Grid, Tường, Cột, Dầm, Sàn, Phòng trong Revit |
| `revit-ghi-chu-kich-thuoc` | Tạo đường kích thước (Dimension) & gắn nhãn (Tag tường, phòng, cấu kiện) tự động |
| `revit-to-mau-kiem-tra` | Tô màu kiểm tra theo tham số (Color Splash), cô lập, reset màu, xóa an toàn |
| `revit-thong-ke-khoi-luong` | Bóc tách khối lượng vật liệu (QTO m³/m²), thống kê mô hình & xuất dữ liệu Room |
| `revit-loc-phan-tu-thong-minh` | Bộ lọc phần tử đa điều kiện trong View hiện hành / toàn dự án (AI Filter) |
| `boc-tach-opentakeoff` | Bóc tách khối lượng bản vẽ PDF bằng OpenTakeoff MCP (70 tools) & đối chiếu Revit |

Cài / cập nhật: bộ cài `MCP - Revit Hoone` đọc `DANH SACH SKILL.json` và tải thư mục `skills/` của kho này
(`CAP NHAT SKILL.bat`). `{{RMCP}}`, `{{PY}}` trong SKILL.md được bộ cài thay bằng đường dẫn trên từng máy.

Thêm skill mới: tạo thư mục `skills/<ten-skill>/SKILL.md` → commit → push. Các máy chạy `CAP NHAT SKILL.bat` là có.
