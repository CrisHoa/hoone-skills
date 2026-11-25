---
name: revit-to-mau-kiem-tra
description: >
  Tô màu trực quan cấu kiện theo giá trị tham số (Color Splash) và thao tác hiển thị (ẩn, cô lập, tô màu kiểm lỗi,
  reset màu, xóa an toàn) trong view hiện hành của Revit qua revit_run_python (tham khảo color_elements, operate_element,
  delete_element từ mcp-servers-for-revit). Dùng khi kiểm tra mác bê tông, đường kính cống, sai lệch cao độ, phân khu.
  Triggers: "tô màu", "color splash", "tô màu theo tham số", "highlight", "cô lập", "isolate", "ẩn phần tử",
  "reset màu", "xóa phần tử", "color elements", "kiểm tra trực quan".
---

# Tô Màu Kiểm Tra (Color Splash) & Thao Tác Hiển Thị Trong Revit

## Nguyên tắc an toàn
1. **Tô màu chỉ ảnh hưởng View hiện hành** (`view.SetElementOverrides`) — không làm hỏng vật liệu thật của mô hình. Luôn cung cấp cách **Reset màu** về mặc định (`OverrideGraphicSettings()`).
2. **Xóa phần tử (`doc.Delete`)**: Bắt buộc liệt kê số lượng & danh sách ID cần xóa và **hỏi xác nhận người dùng trước khi xóa hàng loạt**.
3. Sau khi tô màu, gọi `revit_export_image` kèm bảng chú giải **Giá trị tham số → Màu RGB → Số lượng phần tử**.

## Mẫu lệnh chuẩn (`revit_run_python`)

### 1. Color Splash — Tô màu phần tử theo giá trị của 1 tham số bất kỳ
```python
from Autodesk.Revit.DB import (FilteredElementCollector, BuiltInCategory, FillPatternElement,
                               OverrideGraphicSettings, Color, Transaction)
import colorsys

view = doc.ActiveView
cat = BuiltInCategory.OST_GenericModel   # Doi thanh OST_Walls, OST_PipeCurves, ...
param_name = "Comments"                  # Hoac TN_DuongKinh, Type Name, Level...

solid = next(fp for fp in FilteredElementCollector(doc).OfClass(FillPatternElement) if fp.GetFillPattern().IsSolidFill)
els = list(FilteredElementCollector(doc, view.Id).OfCategory(cat).WhereElementIsNotElementType())

groups = {}
for e in els:
    pr = e.LookupParameter(param_name)
    val = (pr.AsValueString() or pr.AsString() or "<Trống>") if pr else "<Không có tham số>"
    groups.setdefault(val, []).append(e.Id)

legend = []
t = Transaction(doc, "Hoone: Color Splash " + param_name)
t.Start()
keys = sorted(groups.keys())
for idx, k in enumerate(keys):
    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb((idx * 0.61803398875) % 1.0, 0.72, 0.90)]
    ogs = OverrideGraphicSettings()
    ogs.SetSurfaceForegroundPatternId(solid.Id)
    ogs.SetSurfaceForegroundPatternColor(Color(r, g, b))
    ogs.SetCutForegroundPatternId(solid.Id)
    ogs.SetCutForegroundPatternColor(Color(r, g, b))
    for eid in groups[k]:
        view.SetElementOverrides(eid, ogs)
    legend.append({"value": k, "count": len(groups[k]), "rgb": [r, g, b]})
t.Commit()
OUT = {"total": len(els), "groups": legend}
```

### 2. Reset toàn bộ tô màu trong View hiện hành
```python
from Autodesk.Revit.DB import FilteredElementCollector, OverrideGraphicSettings, Transaction
view = doc.ActiveView
clean = OverrideGraphicSettings()
els = list(FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType())
t = Transaction(doc, "Hoone: Reset Colors")
t.Start()
for e in els: view.SetElementOverrides(e.Id, clean)
t.Commit()
OUT = {"reset_count": len(els)}
```

### 3. Cô lập tạm thời (Temporary Isolate) một danh sách phần tử để kiểm tra
```python
from Autodesk.Revit.DB import ElementId, Transaction
from System.Collections.Generic import List
view = doc.ActiveView
ids = List[ElementId]([ElementId(int(x)) for x in IN]) # Revit 2024+: ElementId(long(x))
t = Transaction(doc, "Hoone: Isolate Elements")
t.Start()
view.IsolateElementsTemporary(ids)
t.Commit()
```
