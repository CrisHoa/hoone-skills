---
name: revit-ghi-chu-kich-thuoc
description: >
  Tự động tạo đường kích thước (Dimension) và gắn nhãn hàng loạt (Tag tường, Tag phòng, Tag cấu kiện BIM/hố ga/cống)
  trong view hiện hành của Revit qua revit_run_python (tham khảo create_dimensions, tag_all_walls, tag_all_rooms từ
  mcp-servers-for-revit). Chống gắn trùng tag trên phần tử đã có nhãn.
  Triggers: "ghi kích thước", "tạo dim", "dimension", "tag tường", "tag phòng", "gắn nhãn", "tag all", "ghi chú bản vẽ",
  "create dimensions", "tag walls", "tag rooms".
---

# Tự Động Ghi Kích Thước (Dimension) & Gắn Nhãn (Tag) Trong Revit

## Nguyên tắc bắt buộc
1. **Chỉ chạy trên View hỗ trợ 2D Annotation** (`FloorPlan`, `CeilingPlan`, `Section`, `Elevation`, `Detail`). Không tạo Dimension/Tag trên view 3D chưa khóa (`IsLocked == False`).
2. **Chống gắn trùng Tag**: Trước khi gắn tag hàng loạt, thu thập tập `TaggedLocalElementId` của mọi `IndependentTag` / `RoomTag` đã có trong view để bỏ qua phần tử đã có nhãn.
3. **Kiểm tra trực quan**: Sau khi ghi dim/tag, gọi `revit_export_image` trên view hiện hành để kiểm tra chồng chữ.

## Mẫu lệnh chuẩn (`revit_run_python`)

### 1. Tạo đường kích thước cho Lưới trục (Grid Dimension)
```python
from Autodesk.Revit.DB import FilteredElementCollector, Grid, ReferenceArray, Reference, Line, XYZ, Transaction
view = doc.ActiveView
grids = [g for g in FilteredElementCollector(doc, view.Id).OfClass(Grid)]
# Gom cac truc thang dung (song song Y) sap theo X
v_grids = sorted([g for g in grids if abs(g.Curve.Direction.Y) > 0.9], key=lambda g: g.Curve.GetEndPoint(0).X)
if len(v_grids) >= 2:
    refs = ReferenceArray()
    for g in v_grids: refs.Append(Reference(g))
    y_dim = max(g.Curve.GetEndPoint(1).Y for g in v_grids) + 3.0
    dim_line = Line.CreateBound(XYZ(v_grids[0].Curve.GetEndPoint(0).X, y_dim, 0), XYZ(v_grids[-1].Curve.GetEndPoint(0).X, y_dim, 0))
    t = Transaction(doc, "Hoone: Dim Luoi Truc")
    t.Start()
    doc.Create.NewDimension(view, dim_line, refs)
    t.Commit()
```

### 2. Gắn Tag hàng loạt cho Tường / Cấu kiện (bỏ qua phần tử đã có Tag)
```python
from Autodesk.Revit.DB import (FilteredElementCollector, Wall, IndependentTag, Reference,
                               TagMode, TagOrientation, LocationCurve, Transaction)
view = doc.ActiveView
tagged = set()
for tg in FilteredElementCollector(doc, view.Id).OfClass(IndependentTag):
    try:
        for tid in tg.GetTaggedLocalElementIds(): tagged.add(tid)
    except Exception: pass

walls = [w for w in FilteredElementCollector(doc, view.Id).OfClass(Wall) if w.Id not in tagged]
count = 0
t = Transaction(doc, "Hoone: Tag All Walls")
t.Start()
for w in walls:
    if isinstance(w.Location, LocationCurve):
        pt = w.Location.Curve.Evaluate(0.5, True)
        IndependentTag.Create(doc, view.Id, Reference(w), False, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, pt)
        count += 1
t.Commit()
OUT = {"tagged_walls": count, "skipped_already_tagged": len(tagged)}
```

### 3. Gắn RoomTag hàng loạt cho tất cả Phòng trong View
```python
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, LinkElementId, UV, Transaction
from Autodesk.Revit.DB.Architecture import RoomTag
view = doc.ActiveView
tagged_rooms = {rt.Room.Id for rt in FilteredElementCollector(doc, view.Id).OfClass(RoomTag) if rt.Room}
rooms = [r for r in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Rooms) if r.Area > 0 and r.Id not in tagged_rooms]
t = Transaction(doc, "Hoone: Tag All Rooms")
t.Start()
for r in rooms:
    pt = r.Location.Point
    doc.Create.NewRoomTag(LinkElementId(r.Id), UV(pt.X, pt.Y), view.Id)
t.Commit()
OUT = {"tagged_rooms": len(rooms)}
```
