# hoone-skills

Skill cho AI (Claude Code, Antigravity) dùng cùng bộ **MCP - Revit Hoone** (Revit 2025 + đọc bản vẽ AutoCAD).

| Skill | Nội dung |
|---|---|
| `revit-bim-mcp` | Điều khiển Revit qua MCP `revit`, quy trình đối chiếu bản vẽ ↔ mô hình |
| `doc-ban-ve-cad` | Đọc / phân tích bản vẽ DWG, DXF (chỉ đọc, giải mã TCVN3) |
| `phan-tich-cao-do` | Phân tích cao độ, luôn tuân thủ cao độ bản vẽ |
| `phan-tich-mat-bang` | Mặt bằng / bình đồ → X,Y từng cấu kiện, ghép XYZ |
| `phan-tich-trac-doc` | Trắc dọc: cao độ theo cọc / hố ga, tự nhiên – thiết kế, độ dốc |

Cài / cập nhật: bộ cài `MCP - Revit Hoone` đọc `DANH SACH SKILL.json` và tải thư mục `skills/` của kho này
(`CAP NHAT SKILL.bat`). `{{RMCP}}`, `{{PY}}` trong SKILL.md được bộ cài thay bằng đường dẫn trên từng máy.

Thêm skill mới: tạo thư mục `skills/<ten-skill>/SKILL.md` → commit → push. Các máy chạy `CAP NHAT SKILL.bat` là có.
