#!/usr/bin/env python3
"""
poly3d_elev.py - Doc, trich xuat va noi suy cao do Z tu Polyline 3D / Spline 3D / Line 3D trong DWG/DXF.
Chi doc (read-only), khong bao gio sua file goc.
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import ezdxf
except ImportError:
    print("Loi: Chua cai ezdxf. Cai bang: python -m pip install ezdxf", file=sys.stderr)
    sys.exit(2)


def find_oda():
    base = Path(r"C:\Program Files\ODA")
    if not base.exists():
        return None
    for p in base.rglob("ODAFileConverter.exe"):
        return str(p)
    return None


def ensure_dxf(file_path: str) -> str:
    p = Path(file_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Khong tim thay file: {p}")
    if p.suffix.lower() == ".dxf":
        return str(p)
    cache_dir = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "cad-doc" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    stat = p.stat()
    key = hashlib.md5(f"{p}|{stat.st_size}|{int(stat.st_mtime)}".encode("utf-8")).hexdigest()[:12]
    out_dxf = cache_dir / f"{p.stem}_{key}.dxf"
    if out_dxf.exists():
        return str(out_dxf)
    oda = find_oda()
    if not oda:
        raise RuntimeError("Khong tim thay ODA File Converter de doc .dwg (hay chuyen sang .dxf hoac cai ODA).")
    tmp_in = cache_dir / f"in_{key}"
    tmp_out = cache_dir / f"out_{key}"
    tmp_in.mkdir(exist_ok=True)
    tmp_out.mkdir(exist_ok=True)
    import shutil
    shutil.copy2(p, tmp_in / p.name)
    subprocess.run([oda, str(tmp_in), str(tmp_out), "ACAD2018", "DXF", "0", "1", p.name],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    produced = tmp_out / (p.stem + ".dxf")
    if not produced.exists():
        raise RuntimeError("ODA File Converter khong tao duoc file DXF.")
    shutil.move(str(produced), str(out_dxf))
    shutil.rmtree(tmp_in, ignore_errors=True)
    shutil.rmtree(tmp_out, ignore_errors=True)
    return str(out_dxf)


def extract_3d_entities(doc, layer_regex=None, scale=1.0):
    msp = doc.modelspace()
    pat = re.compile(layer_regex, re.IGNORECASE) if layer_regex else None
    items = []
    for e in msp:
        layer = e.dxf.layer if e.dxf.hasattr("layer") else "0"
        if pat and not pat.search(layer):
            continue
        etype = e.dxftype()
        pts = []
        kind = None
        if etype == "POLYLINE":
            if e.is_3d_polyline:
                kind = "3DPOLYLINE"
                pts = [(v.dxf.location.x * scale, v.dxf.location.y * scale, v.dxf.location.z * scale) for v in e.vertices]
            elif e.is_2d_polyline:
                z = float(e.dxf.elevation.z) * scale if e.dxf.hasattr("elevation") else 0.0
                kind = "2DPOLYLINE"
                pts = [(v.dxf.location.x * scale, v.dxf.location.y * scale, z) for v in e.vertices]
        elif etype == "LWPOLYLINE":
            z = float(e.dxf.elevation) * scale if e.dxf.hasattr("elevation") else 0.0
            kind = "LWPOLYLINE"
            pts = [(p[0] * scale, p[1] * scale, z) for p in e.get_points("xy")]
        elif etype == "LINE":
            s, t = e.dxf.start, e.dxf.end
            kind = "LINE"
            pts = [(s.x * scale, s.y * scale, s.z * scale), (t.x * scale, t.y * scale, t.z * scale)]
        elif etype == "SPLINE":
            kind = "SPLINE"
            try:
                pts = [(p.x * scale, p.y * scale, p.z * scale) for p in e.flattening(0.05 / max(scale, 1e-9))]
            except Exception:
                pts = [(p[0] * scale, p[1] * scale, p[2] * scale) for p in e.control_points]

        if len(pts) < 2:
            continue
        zs = [p[2] for p in pts]
        zmin, zmax = min(zs), max(zs)
        has_z = (abs(zmin) > 1e-6 or abs(zmax) > 1e-6)
        len2d = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
        len3d = sum(math.sqrt((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2 + (pts[i + 1][2] - pts[i][2]) ** 2) for i in range(len(pts) - 1))
        grades = []
        for i in range(len(pts) - 1):
            d2 = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            if d2 > 1e-6:
                grades.append((pts[i + 1][2] - pts[i][2]) / d2 * 100.0)
        items.append({
            "handle": e.dxf.handle,
            "type": kind,
            "layer": layer,
            "has_z": has_z,
            "vertex_count": len(pts),
            "length_2d": round(len2d, 4),
            "length_3d": round(len3d, 4),
            "z_min": round(zmin, 4),
            "z_max": round(zmax, 4),
            "grade_min_pct": round(min(grades), 3) if grades else 0.0,
            "grade_max_pct": round(max(grades), 3) if grades else 0.0,
            "pts": pts,
        })
    return items


def select_entity(items, handle=None, only_3d=False):
    if handle:
        for it in items:
            if it["handle"].upper() == handle.upper():
                return it
        raise ValueError(f"Khong tim thay doi tuong handle={handle}")
    pool = [it for it in items if (it["has_z"] or not only_3d)]
    if not pool:
        raise ValueError("Khong tim thay doi tuong Polyline/Spline/Line phu hop.")
    pool.sort(key=lambda x: (x["has_z"], x["type"] == "3DPOLYLINE", x["length_2d"]), reverse=True)
    return pool[0]


def build_vertices(pts, start_station=0.0):
    out = []
    s2 = start_station
    s3 = start_station
    for i, (x, y, z) in enumerate(pts):
        grade = 0.0
        az = 0.0
        if i > 0:
            dx = x - pts[i - 1][0]
            dy = y - pts[i - 1][1]
            dz = z - pts[i - 1][2]
            d2 = math.hypot(dx, dy)
            d3 = math.sqrt(dx * dx + dy * dy + dz * dz)
            s2 += d2
            s3 += d3
            if d2 > 1e-9:
                grade = dz / d2 * 100.0
                az = math.degrees(math.atan2(dx, dy)) % 360.0
        elif len(pts) > 1:
            dx, dy, dz = pts[1][0] - x, pts[1][1] - y, pts[1][2] - z
            d2 = math.hypot(dx, dy)
            if d2 > 1e-9:
                grade = dz / d2 * 100.0
                az = math.degrees(math.atan2(dx, dy)) % 360.0
        out.append({
            "index": i,
            "station_2d": round(s2, 4),
            "station_3d": round(s3, 4),
            "x": round(x, 4),
            "y": round(y, 4),
            "z": round(z, 4),
            "azimuth_deg": round(az, 3),
            "grade_pct": round(grade, 3),
        })
    return out


def sample_polyline(pts, step: float, start_station=0.0, keep_vertices=True):
    cum = [0.0]
    for i in range(len(pts) - 1):
        cum.append(cum[-1] + math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
    total = cum[-1]
    stations = set()
    s = 0.0
    while s < total:
        stations.add(round(s, 6))
        s += step
    stations.add(round(total, 6))
    if keep_vertices:
        for c in cum:
            stations.add(round(c, 6))
    sorted_s = sorted(stations)

    out = []
    seg = 0
    for st in sorted_s:
        while seg < len(cum) - 2 and cum[seg + 1] < st - 1e-9:
            seg += 1
        d = cum[seg + 1] - cum[seg]
        t = 0.0 if d < 1e-12 else max(0.0, min(1.0, (st - cum[seg]) / d))
        p0, p1 = pts[seg], pts[seg + 1]
        x = p0[0] + t * (p1[0] - p0[0])
        y = p0[1] + t * (p1[1] - p0[1])
        z = p0[2] + t * (p1[2] - p0[2])
        dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        d2 = math.hypot(dx, dy)
        az = math.degrees(math.atan2(dx, dy)) % 360.0 if d2 > 1e-9 else 0.0
        grade = (dz / d2 * 100.0) if d2 > 1e-9 else 0.0
        out.append({
            "station": round(start_station + st, 4),
            "x": round(x, 4),
            "y": round(y, 4),
            "z": round(z, 4),
            "azimuth_deg": round(az, 3),
            "grade_pct": round(grade, 3),
        })
    return out


def project_point_2d(pts, qx, qy, start_station=0.0):
    best = None
    cum = 0.0
    for i in range(len(pts) - 1):
        x0, y0, z0 = pts[i]
        x1, y1, z1 = pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        seg2 = dx * dx + dy * dy
        seg_len = math.sqrt(seg2)
        if seg2 < 1e-12:
            t = 0.0
        else:
            t = max(0.0, min(1.0, ((qx - x0) * dx + (qy - y0) * dy) / seg2))
        px = x0 + t * dx
        py = y0 + t * dy
        pz = z0 + t * (z1 - z0)
        dist = math.hypot(qx - px, qy - py)
        # signed offset (+ phai tuyen, - trai tuyen)
        cross = dx * (qy - y0) - dy * (qx - x0)
        signed_off = -dist if cross > 0 else dist
        if best is None or dist < best["offset_abs_m"]:
            grade = ((z1 - z0) / seg_len * 100.0) if seg_len > 1e-9 else 0.0
            best = {
                "query_x": round(qx, 4),
                "query_y": round(qy, 4),
                "proj_x": round(px, 4),
                "proj_y": round(py, 4),
                "z": round(pz, 4),
                "station": round(start_station + cum + t * seg_len, 4),
                "offset_abs_m": round(dist, 4),
                "offset_signed_m": round(signed_off, 4),
                "grade_pct": round(grade, 3),
            }
        cum += seg_len
    return best


def main():
    ap = argparse.ArgumentParser(description="Doc & noi suy cao do tu Polyline 3D trong DWG/DXF.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("list", "vertices", "sample", "query"):
        sp = sub.add_parser(name)
        sp.add_argument("file", help="Duong dan file .dwg hoac .dxf")
        sp.add_argument("--layer", help="Regex loc theo layer")
        sp.add_argument("--scale", type=float, default=1.0, help="He so quy doi don vi (vd 0.001 neu mm -> m)")
        sp.add_argument("--json", action="store_true", help="Xuat JSON")
        if name != "list":
            sp.add_argument("--handle", help="Handle cua doi tuong 3D")
            sp.add_argument("--start-station", type=float, default=0.0, help="Ly trinh diem dau (m)")
        if name == "sample":
            sp.add_argument("--step", type=float, default=5.0, help="Buoc rai mau theo ly trinh 2D (m)")
            sp.add_argument("--no-vertices", action="store_true", help="Khong giu lai dinh gay trung gian")
        if name == "query":
            sp.add_argument("--pt", nargs=2, type=float, metavar=("X", "Y"), action="append", help="Toa do diem can noi suy")
            sp.add_argument("--pts-file", help="File JSON danh sach [[x,y], ...] hoac [{name,x,y}, ...]")

    args = ap.parse_args()
    dxf_path = ensure_dxf(args.file)
    doc = ezdxf.readfile(dxf_path)
    items = extract_3d_entities(doc, layer_regex=args.layer, scale=args.scale)

    if args.cmd == "list":
        summary = [{k: v for k, v in it.items() if k != "pts"} for it in items]
        summary.sort(key=lambda x: (x["has_z"], x["type"] == "3DPOLYLINE", x["length_2d"]), reverse=True)
        if args.json:
            print(json.dumps({"file": args.file, "count": len(summary), "entities": summary[:200]}, ensure_ascii=False, indent=2))
        else:
            print(f"File: {args.file} | Tim thay {len(summary)} doi tuong Polyline/Spline/Line")
            for s in summary[:40]:
                tag = "3D" if s["has_z"] else "2D(Z=0)"
                print(f"  [{s['handle']:>6}] {s['type']:<10} {tag:<7} | Layer: {s['layer']:<22} | {s['vertex_count']:>4} dinh | L2D={s['length_2d']:>8.2f}m | Z=[{s['z_min']:.2f}..{s['z_max']:.2f}]")
        return

    ent = select_entity(items, handle=args.handle)
    if args.cmd == "vertices":
        verts = build_vertices(ent["pts"], start_station=args.start_station)
        res = {"handle": ent["handle"], "type": ent["type"], "layer": ent["layer"], "has_z": ent["has_z"], "vertices": verts}
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "sample":
        pts = sample_polyline(ent["pts"], step=args.step, start_station=args.start_station, keep_vertices=not args.no_vertices)
        res = {"handle": ent["handle"], "type": ent["type"], "layer": ent["layer"], "has_z": ent["has_z"], "step": args.step, "count": len(pts), "points": pts}
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "query":
        queries = []
        if args.pt:
            for idx, (x, y) in enumerate(args.pt, 1):
                queries.append((f"P{idx}", x, y))
        if args.pts_file:
            raw = json.loads(Path(args.pts_file).read_text(encoding="utf-8"))
            for idx, row in enumerate(raw, 1):
                if isinstance(row, dict):
                    queries.append((str(row.get("name", f"P{idx}")), float(row["x"]), float(row["y"])))
                else:
                    queries.append((f"P{idx}", float(row[0]), float(row[1])))
        if not queries:
            raise ValueError("Can truyen --pt X Y hoac --pts-file.")
        out = []
        for name, x, y in queries:
            r = project_point_2d(ent["pts"], x, y, start_station=args.start_station)
            r["name"] = name
            out.append(r)
        print(json.dumps({"handle": ent["handle"], "layer": ent["layer"], "has_z": ent["has_z"], "results": out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
