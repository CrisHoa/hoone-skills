---
name: revit-loc-phan-tu-thong-minh
description: >
  Bộ lọc phần tử đa điều kiện thông minh trong Revit qua revit_run_python (tham khảo ai_element_filter,
  get_current_view_elements, get_current_view_info từ mcp-servers-for-revit): lọc theo View hiện hành hoặc toàn dự án,
  kết hợp Category + Family + Type + Level + vùng không gian 3D (BoundingBox) + so sánh tham số (>, <, ==, contains, trống),
  trả về danh sách ID để chọn, zoom, gán tham số hoặc tô màu kiểm lỗi.
  Triggers: "lọc phần tử", "tìm phần tử", "ai filter", "lọc theo điều kiện", "phần tử trong view", "lọc theo tầng",
  "lọc theo cao độ", "tìm cấu kiện thiếu tham số", "current view elements".
---

# Bộ Lọc Phần Tử Thông Minh Đa Điều Kiện Trong Revit

Dùng khi `revit_query_elements` (chỉ lọc 1 tham số bằng chính xác) chưa đủ — cần lọc theo **View hiện hành**, **khoảng giá trị số (`>`, `<`, `min..max`)**, **tham số bị bỏ trống**, hoặc **vùng không gian 3D (BoundingBox)**.

## Mẫu lệnh chuẩn (`revit_run_python`)

### 1. Lọc đa điều kiện (View hiện hành / Toàn dự án + Tham số số/chuỗi + Level)
```python
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilyInstance

# Cau hinh loc (chinh theo yeu cau nguoi dung)
only_active_view = True
cat = BuiltInCategory.OST_GenericModel   # None = tat ca category
family_contains = ""                     # vd "HoGa"
level_name = ""                          # vd "Level 1"
param_name = "TN_CaoDoDayHo"             # Ten tham so can loc (de trong neu khong loc)
op = "missing"                           # "eq" | "contains" | "gt" | "lt" | "missing"
target_val = None                        # Gia tri so sanh

col = FilteredElementCollector(doc, doc.ActiveView.Id) if only_active_view else FilteredElementCollector(doc)
if cat is not None: col = col.OfCategory(cat)
els = col.WhereElementIsNotElementType()

hits = []
for e in els:
    if family_contains:
        fam = e.Symbol.FamilyName if isinstance(e, FamilyInstance) else e.Name
        if family_contains.lower() not in (fam or "").lower(): continue
    if level_name:
        lv = doc.GetElement(e.LevelId) if e.LevelId else None
        if not lv or level_name.lower() not in lv.Name.lower(): continue
    val_str = None
    if param_name:
        pr = e.LookupParameter(param_name)
        val_str = (pr.AsValueString() or pr.AsString()) if pr else None
        if op == "missing" and val_str not in (None, ""): continue
        elif op == "eq" and str(val_str) != str(target_val): continue
        elif op == "contains" and (val_str is None or str(target_val).lower() not in val_str.lower()): continue
        elif op in ("gt", "lt"):
            try:
                num = float(str(val_str).split()[0].replace(",", "."))
                if op == "gt" and not (num > float(target_val)): continue
                if op == "lt" and not (num < float(target_val)): continue
            except Exception: continue
    eid = getattr(e.Id, "Value", None)
    if eid is None: eid = e.Id.IntegerValue
    hits.append({"id": eid, "name": e.Name, "category": e.Category.Name if e.Category else "", "value": val_str})

OUT = {"view": doc.ActiveView.Name, "matched_count": len(hits), "ids": [h["id"] for h in hits], "sample": hits[:50]}
```

## Kết hợp chuỗi công việc (Workflow)
1. **Lọc** bằng skill này để lấy mảng `ids`.
2. Gọi `revit_zoom_to(ids=...)` để đưa màn hình Revit tới ngay nhóm đối tượng lỗi/cần xem.
3. Kết hợp `revit-to-mau-kiem-tra` để tô đỏ nhóm phần tử thiếu tham số hoặc vượt ngưỡng thiết kế.
