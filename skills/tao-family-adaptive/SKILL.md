---
name: tao-family-adaptive
description: >
  Tạo mới, chỉnh sửa và rải Adaptive Component Family (Generic Model Adaptive .rfa) trong Revit 2020–2027 qua MCP
  revit_run_python: tạo điểm thích ứng (Adaptive Points 2/3/4/N điểm), khung tham chiếu vuông góc tuyến, mặt cắt tham số,
  khối Loft / SweptBlend bám tuyến cong 3D (rãnh thoát nước, cống hộp, tường chắn, bó vỉa, dầm cầu, hầm, mặt đường),
  và rải hàng loạt theo tọa độ XYZ (VN2000 → hệ nội bộ Revit).
  Triggers: "adaptive", "family adaptive", "adaptive component", "tạo family thích ứng", "rải theo tuyến 3d",
  "loft dọc tuyến", "rãnh bám tuyến", "dầm cầu adaptive", "tường chắn adaptive", "bó vỉa 3d".
---

# Tạo & Rải Family Adaptive Component trong Revit (MCP `revit`)

Dùng tool MCP `revit_run_python` để tạo file `.rfa` từ template `Metric Generic Model Adaptive.rft` (tái lập được 100%, không dựng tay), nạp vào dự án và rải theo danh sách điểm 3D `(E, N, Z)`.

## Nguyên tắc bắt buộc
1. **Đơn vị nội bộ Revit API luôn là feet (`1 m = 1 / 0.3048 ft`)**. Mọi kích thước mm/m từ bản vẽ phải quy đổi chuẩn trước khi tạo hình học.
2. **Hệ tọa độ VN2000 → Nội bộ Revit**:
   - Đọc gốc tọa độ chung từ `revit_info` (`shared_origin_m`: `E0, N0, Z0, angle_rad`).
   - Công thức chuyển 1 điểm thiết kế `(E, N, Z)` (m) sang tọa độ nội bộ `(x, y, z)` (ft):
     ```python
     import math
     FT = 1.0 / 0.3048
     dE, dN, dZ = E - E0, N - N0, Z - Z0
     ca, sa = math.cos(-angle_rad), math.sin(-angle_rad)
     x_ft = (dE * ca - dN * sa) * FT
     y_ft = (dE * sa + dN * ca) * FT
     z_ft = (dZ) * FT
     ```
3. **Chống xoắn (Anti-Twist) trên đường cong 3D**:
   - Đặt mặt phẳng vẽ mặt cắt (`Profile`) trên **Reference Plane vuông góc với đường nối 2 điểm thích ứng** (dùng `ReferencePoint.GetCoordinateSystem()` hoặc gán `SetHostedOnReference` với trục `Z` luôn hướng thẳng đứng lên trời `(0, 0, 1)`).
   - Với công trình có độ dốc ngang / siêu cao $i_n$: xoay mặt cắt quanh trục tiếp tuyến tuyến một góc $\arctan(i_n)$ bằng tham số `GocSieuCao` (Angle).
4. **Không tự đoán cao độ**: Tọa độ `XYZ` đặt điểm thích ứng phải lấy từ `polyline-3d-cao-do` hoặc `suy-luan-cao-do-tu-trac-doc` (có nguồn rõ ràng).

## 3 Mẫu Family Adaptive Phổ Biến

| Mẫu | Số điểm Adaptive | Ứng dụng hạ tầng BIM |
|---|---|---|
| **2 điểm (2-Pt Segment)** | `P1` (đầu đốt), `P2` (cuối đốt) | Đốt rãnh thoát nước, đốt cống hộp, bó vỉa, hộ lan, tường chắn, đốt dầm cầu lắp ghép |
| **3 điểm (3-Pt Arc/Curve)** | `P1` (đầu), `P2` (giữa), `P3` (cuối) | Đoạn cong trơn (Spline/Arc 3D) khi bán kính cong nhỏ, dầm cong, hầm cong |
| **4 điểm (4-Pt Panel/Slab)** | `P1, P2` (mép trái), `P3, P4` (mép phải) | Bản mặt cầu, lớp kết cấu áo đường (BTN, CPĐD), mái ta-luy gia cố thay đổi bề rộng |

## Quy trình tạo Family Adaptive (.rfa) bằng `revit_run_python`

### Bước 1 — Tìm template `Metric Generic Model Adaptive.rft`
```python
import os, glob
def find_adaptive_rft(app):
    # Uu tien thu muc FamilyTemplatePath cua phien Revit dang mo
    roots = [app.FamilyTemplatePath, r"C:\ProgramData\Autodesk"]
    for r in roots:
        if not r or not os.path.isdir(r): continue
        hits = glob.glob(os.path.join(r, "**", "*Generic Model Adaptive*.rft"), recursive=True)
        if hits: return hits[0]
    raise FileNotFoundError("Khong tim thay Metric Generic Model Adaptive.rft")
```

### Bước 2 — Tạo Adaptive Points + Reference Line + Mặt cắt + Loft Form
```python
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

def create_2pt_adaptive_loft(app, rft_path, save_rfa_path, profile_pts_mm):
    """
    profile_pts_mm: danh sach [(u_mm, v_mm), ...] dinh mat cat khep kin
    (u = ngang tim tuyen, v = cao do so voi tim).
    """
    MM = 1.0 / 304.8
    fdoc = app.NewFamilyDocument(rft_path)
    t = Transaction(fdoc, "Create Adaptive Loft")
    t.Start()
    try:
        # 1. Tao 2 Adaptive Points: P1(0,0,0), P2(10m,0,0)
        p1 = fdoc.FamilyCreate.NewReferencePoint(XYZ(0, 0, 0))
        p2 = fdoc.FamilyCreate.NewReferencePoint(XYZ(10000 * MM, 0, 0))
        AdaptiveComponentFamilyUtils.MakeAdaptivePoint(fdoc, p1.Id, AdaptivePointType.PlacementPoint)
        AdaptiveComponentFamilyUtils.MakeAdaptivePoint(fdoc, p2.Id, AdaptivePointType.PlacementPoint)
        AdaptiveComponentFamilyUtils.SetPlacementNumber(fdoc, p1.Id, 1)
        AdaptiveComponentFamilyUtils.SetPlacementNumber(fdoc, p2.Id, 2)

        # 2. Noi 2 diem bang CurveByPoints (Reference Line)
        arr_line = ReferencePointArray()
        arr_line.Append(p1); arr_line.Append(p2)
        path_curve = fdoc.FamilyCreate.NewCurveByPoints(arr_line)
        path_curve.IsReferenceLine = True

        # 3. Tao 2 mat cat tai P1 va P2 tren mat phang vuong goc tiep tuyen (YZ plane cua diem)
        profiles = ReferenceArrayArray()
        for host_pt in (p1, p2):
            origin = host_pt.Position
            # He truc dia phuong: X doc tuyen, Y ngang (u), Z dung (v)
            ref_arr = ReferenceArray()
            n = len(profile_pts_mm)
            for i in range(n):
                u1, v1 = profile_pts_mm[i]
                u2, v2 = profile_pts_mm[(i + 1) % n]
                a = XYZ(origin.X, origin.Y + u1 * MM, origin.Z + v1 * MM)
                b = XYZ(origin.X, origin.Y + u2 * MM, origin.Z + v2 * MM)
                rp_a = fdoc.FamilyCreate.NewReferencePoint(a)
                rp_b = fdoc.FamilyCreate.NewReferencePoint(b)
                rpa = ReferencePointArray(); rpa.Append(rp_a); rpa.Append(rp_b)
                seg = fdoc.FamilyCreate.NewCurveByPoints(rpa)
                ref_arr.Append(seg.GeometryCurve.Reference)
            profiles.Append(ref_arr)

        # 4. Tao khoi Loft (Solid)
        form = fdoc.FamilyCreate.NewLoftForm(True, profiles)
        t.Commit()
    except Exception:
        t.RollBack()
        raise

    opt = SaveAsOptions(); opt.OverwriteExistingFile = True
    fdoc.SaveAs(save_rfa_path, opt)
    fdoc.Close(False)
    return save_rfa_path
```
*(Ghi chú: Để mặt cắt bám chặt và tự xoay khi điểm `P1, P2` di chuyển tự do trong không gian 3D, tạo **Nested Profile Family** hoặc gắn `PointOnEdge` ở `NormalizedCurveParameter = 0.0` và `1.0` trên `path_curve`, vẽ `ModelCurve` trên `SketchPlane` của mặt phẳng `XY/YZ` của `PointOnEdge` đó, rồi gọi `NewLoftForm(True, profiles)` — đảm bảo không bao giờ bị biến dạng khi đặt trên đoạn dốc/cong!)*

### Bước 3 — Nạp vào dự án & Rải hàng loạt theo danh sách XYZ 3D
```python
def place_adaptive_segments(doc, family_symbol, pts_xyz_ft):
    """pts_xyz_ft: danh sach [(x_ft, y_ft, z_ft), ...] doc theo tuyen 3D."""
    created_ids = []
    t = Transaction(doc, "Place Adaptive Along 3D Polyline")
    t.Start()
    try:
        if not family_symbol.IsActive:
            family_symbol.Activate()
            doc.Regenerate()
        for i in range(len(pts_xyz_ft) - 1):
            inst = AdaptiveComponentInstanceUtils.CreateAdaptiveComponentInstance(doc, family_symbol)
            ref_ids = AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(inst)
            p1 = doc.GetElement(ref_ids[0])
            p2 = doc.GetElement(ref_ids[1])
            p1.Position = XYZ(*pts_xyz_ft[i])
            p2.Position = XYZ(*pts_xyz_ft[i + 1])
            created_ids.append(inst.Id)
        t.Commit()
    except Exception:
        t.RollBack()
        raise
    return created_ids
```

## Kiểm tra chất lượng bắt buộc sau khi rải
1. Gọi `revit_export_image` ở cả view **3D** và **Mặt bằng / Mặt cắt** để kiểm tra trực quan: không bị xoắn, không bị hở khe giữa các đốt, đúng hướng dốc.
2. Kiểm tra lại cao độ thực tế của điểm đầu/cuối phần tử (`revit_run_python` đọc `BoundingBox` hoặc `ReferencePoint.Position.Z * 0.3048 + Z0`) so với bảng cao độ trắc dọc — sai số phải **≤ 0.005 m**.
3. Ghi rõ nguồn tọa độ XYZ, tên file `.rfa`, số lượng đốt đã rải và tổng chiều dài 3D trong báo cáo cho người dùng.
