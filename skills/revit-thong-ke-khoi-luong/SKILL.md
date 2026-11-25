---
name: revit-thong-ke-khoi-luong
description: >
  Bóc tách khối lượng vật liệu (QTO: m3, m2, m dài), phân tích thống kê độ phức tạp mô hình (đếm phần tử theo Category,
  cảnh báo family nặng), liệt kê toàn bộ Family Types sẵn có và xuất dữ liệu Phòng (Room) từ Revit qua revit_run_python
  (tham khảo get_material_quantities, analyze_model_statistics, export_room_data, get_available_family_types).
  Triggers: "bóc khối lượng", "thống kê vật liệu", "QTO", "material takeoff", "thống kê mô hình", "đếm phần tử",
  "xuất danh sách phòng", "export room", "danh sách family", "khối lượng bê tông".
---

# Bóc Tách Khối Lượng Vật Liệu (QTO) & Thống Kê Mô Hình Revit

## Hệ số quy đổi chuẩn từ đơn vị nội bộ Revit API (feet)
- **Chiều dài (m):** `val_ft * 0.3048`
- **Diện tích (m²):** `val_ft2 * 0.09290304` (`0.3048 ** 2`)
- **Thể tích (m³):** `val_ft3 * 0.028316846592` (`0.3048 ** 3`)

## Mẫu lệnh chuẩn (`revit_run_python`)

### 1. Bóc tách khối lượng vật liệu (Material QTO) theo Vật liệu & Category
```python
from Autodesk.Revit.DB import FilteredElementCollector
FT2_TO_M2 = 0.09290304
FT3_TO_M3 = 0.028316846592

summary = {}
for e in FilteredElementCollector(doc).WhereElementIsNotElementType():
    if e.Category is None: continue
    mids = e.GetMaterialIds(False)
    if not mids: continue
    cat = e.Category.Name
    for mid in mids:
        mat = doc.GetElement(mid)
        mname = mat.Name if mat else "Unknown"
        vol_m3 = e.GetMaterialVolume(mid) * FT3_TO_M3
        area_m2 = e.GetMaterialArea(mid, False) * FT2_TO_M2
        if vol_m3 <= 1e-6 and area_m2 <= 1e-6: continue
        key = (cat, mname)
        row = summary.setdefault(key, {"category": cat, "material": mname, "volume_m3": 0.0, "area_m2": 0.0, "count": 0})
        row["volume_m3"] += vol_m3
        row["area_m2"] += area_m2
        row["count"] += 1

rows = sorted(summary.values(), key=lambda x: x["volume_m3"], reverse=True)
for r in rows:
    r["volume_m3"] = round(r["volume_m3"], 3)
    r["area_m2"] = round(r["area_m2"], 2)
OUT = {"total_groups": len(rows), "materials": rows[:100]}
```

### 2. Phân tích thống kê mô hình (Model Statistics)
```python
from Autodesk.Revit.DB import FilteredElementCollector, View, Family
cats = {}
total = 0
for e in FilteredElementCollector(doc).WhereElementIsNotElementType():
    if e.Category is None: continue
    c = e.Category.Name
    cats[c] = cats.get(c, 0) + 1
    total += 1
top_cats = sorted([{"category": k, "count": v} for k, v in cats.items()], key=lambda x: x["count"], reverse=True)
OUT = {
    "title": doc.Title,
    "total_instances": total,
    "total_families": FilteredElementCollector(doc).OfClass(Family).GetElementCount(),
    "total_views": FilteredElementCollector(doc).OfClass(View).GetElementCount(),
    "top_categories": top_cats[:30]
}
```

### 3. Xuất dữ liệu Phòng (Rooms) & Liệt kê Family Types sẵn có
```python
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, FamilySymbol
FT2_TO_M2 = 0.09290304
rooms = []
for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms):
    if r.Area <= 0: continue
    rooms.append({
        "number": r.Number,
        "name": r.get_Parameter(BuiltInParameter.ROOM_NAME).AsString(),
        "level": r.Level.Name if r.Level else "",
        "area_m2": round(r.Area * FT2_TO_M2, 2),
        "perimeter_m": round(r.Perimeter * 0.3048, 2)
    })
OUT = {"room_count": len(rooms), "rooms": rooms}
```

## Quy chuẩn báo cáo
- Luôn tách rõ đơn vị (`m³`, `m²`, `m`, `cái`), ghi tổng cộng cuối bảng, và ghi rõ nếu có phần tử chưa gán vật liệu (Material = `<By Category>`).
