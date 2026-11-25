---
name: revit-dung-hinh-co-ban
description: >
  Dựng hình hàng loạt cấu kiện cơ bản trong Revit 2020–2027 qua revit_run_python (tham khảo bộ lệnh mcp-servers-for-revit):
  tạo hệ Level (cao độ tầng), Grid (lưới trục), cấu kiện dạng tuyến (Wall, Beam, Pipe), cấu kiện dạng điểm (Column, Door,
  Window, FamilyInstance), cấu kiện dạng mặt (Floor, Ceiling, Roof), hệ dầm kết cấu (BeamSystem) và Room.
  Triggers: "tạo lưới trục", "tạo level", "tạo tầng", "dựng tường", "dựng sàn", "dựng cột", "dựng dầm", "tạo phòng",
  "create grid", "create level", "create wall", "create floor", "create room", "beam system", "dựng hình revit".
---

# Dựng Hình Cấu Kiện Cơ Bản Trong Revit (MCP `revit_run_python`)

Quy chuẩn dựng hình tái lập được bằng script Python trong Revit API (`doc`, `uidoc`, `uiapp` có sẵn trong `revit_run_python`).

## Nguyên tắc bắt buộc
1. **Quy đổi đơn vị**: Revit API dùng **feet** (`MM = 1.0 / 304.8`, `M = 1.0 / 0.3048`). Luôn quy đổi từ mm/m sang feet trước khi tạo `XYZ`.
2. **Transaction an toàn**: Mọi thao tác tạo phần tử bọc trong `Transaction(doc, "...")`; kiểm tra & kích hoạt `FamilySymbol.Activate()` trước khi đặt `FamilyInstance`.
3. **Tương thích Revit 2020–2027**:
   - Tạo sàn (`Floor`): Revit 2022–2027 dùng `Floor.Create(doc, [CurveLoop], floorTypeId, levelId)`.
   - Lấy ID: ưu tiên `el.Id.Value` (Revit 2024+) fallback `el.Id.IntegerValue` (Revit 2020–2023).
4. **Kiểm tra sau khi dựng**: Gọi `revit_export_image` để kiểm tra hình học thực tế.

## Mẫu lệnh chuẩn cho từng nhóm cấu kiện

### 1. Tạo Level (Cao độ tầng) & Grid (Lưới trục)
```python
from Autodesk.Revit.DB import Level, Grid, Line, XYZ, Transaction
M = 1.0 / 0.3048
t = Transaction(doc, "Hoone: Tao Level & Grid")
t.Start()
# Level: danh sach [(ten, cao_do_m), ...]
for name, elev_m in [("T1", 0.0), ("T2", 3.6), ("Mai", 7.2)]:
    lv = Level.Create(doc, elev_m * M)
    lv.Name = name
# Grid doc truc X (truc 1,2,3...) va truc Y (truc A,B,C...)
for name, x_m in [("1", 0), ("2", 6), ("3", 12)]:
    g = Grid.Create(doc, Line.CreateBound(XYZ(x_m * M, -3 * M, 0), XYZ(x_m * M, 15 * M, 0)))
    g.Name = name
t.Commit()
```

### 2. Cấu kiện dạng tuyến (Wall / Beam)
```python
from Autodesk.Revit.DB import Wall, Line, XYZ, FilteredElementCollector, Level, WallType, Transaction
M = 1.0 / 0.3048
lv = FilteredElementCollector(doc).OfClass(Level).FirstElement()
wt = FilteredElementCollector(doc).OfClass(WallType).FirstElement()
t = Transaction(doc, "Hoone: Dung Tuong")
t.Start()
line = Line.CreateBound(XYZ(0, 0, 0), XYZ(6 * M, 0, 0))
w = Wall.Create(doc, line, wt.Id, lv.Id, 3.6 * M, 0.0, False, False)
t.Commit()
```

### 3. Cấu kiện dạng điểm (Cột / Cửa / Hố ga / Thiết bị — `FamilyInstance`)
```python
from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, XYZ, Level, Transaction
from Autodesk.Revit.DB.Structure import StructuralType
M = 1.0 / 0.3048
sym = next(s for s in FilteredElementCollector(doc).OfClass(FamilySymbol) if "Column" in s.FamilyName or "Cot" in s.FamilyName)
lv = FilteredElementCollector(doc).OfClass(Level).FirstElement()
t = Transaction(doc, "Hoone: Dat FamilyInstance")
t.Start()
if not sym.IsActive:
    sym.Activate(); doc.Regenerate()
inst = doc.Create.NewFamilyInstance(XYZ(6 * M, 0, 0), sym, lv, StructuralType.Column)
t.Commit()
```

### 4. Cấu kiện dạng mặt (Floor) & Room
```python
from Autodesk.Revit.DB import Floor, FloorType, CurveLoop, Line, XYZ, UV, FilteredElementCollector, Level, Transaction
M = 1.0 / 0.3048
lv = FilteredElementCollector(doc).OfClass(Level).FirstElement()
ft = FilteredElementCollector(doc).OfClass(FloorType).FirstElement()
pts = [XYZ(0,0,0), XYZ(12*M,0,0), XYZ(12*M,8*M,0), XYZ(0,8*M,0)]
loop = CurveLoop()
for i in range(4): loop.Append(Line.CreateBound(pts[i], pts[(i+1)%4]))
t = Transaction(doc, "Hoone: Tao San & Room")
t.Start()
Floor.Create(doc, [loop], ft.Id, lv.Id)
room = doc.Create.NewRoom(lv, UV(3 * M, 3 * M))
room.Name = "Phong ky thuat"
t.Commit()
```
