#!/usr/bin/env python3
"""
align_2d_profile_3d.py - Ghep tim tuyen 2D (DWG/DXF, ho tro cung tron bulge) voi bang thong so Trac doc
(co ho tro duong cong dung Parabol) de suy luan cao do Z thanh chuoi toa do 3D (E, N, Z).
Chi doc (read-only), khong bao gio sua file ban ve goc.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
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
        raise RuntimeError("Khong tim thay ODA File Converter de doc .dwg.")
    tmp_in = cache_dir / f"in_{key}"
    tmp_out = cache_dir / f"out_{key}"
    tmp_in.mkdir(exist_ok=True)
    tmp_out.mkdir(exist_ok=True)
    shutil.copy2(p, tmp_in / p.name)
    subprocess.run([oda, str(tmp_in), str(tmp_out), "ACAD2018", "DXF", "0", "1", p.name],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    produced = tmp_out / (p.stem + ".dxf")
    if not produced.exists():
        raise RuntimeError("ODA File Converter khong tao duoc DXF.")
    shutil.move(str(produced), str(out_dxf))
    shutil.rmtree(tmp_in, ignore_errors=True)
    shutil.rmtree(tmp_out, ignore_errors=True)
    return str(out_dxf)


def parse_station(val) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().upper().replace(",", "")
    m = re.match(r"^(?:KM)?\s*(\d+)\s*\+\s*([0-9.]+)$", s)
    if m:
        return int(m.group(1)) * 1000.0 + float(m.group(2))
    return float(s)


def flatten_lwpolyline_2d(entity, scale=1.0, arc_step=0.5):
    """Chuyen LWPOLYLINE (ke ca cung tron bulge) thanh chuoi diem 2D min."""
    raw = list(entity.get_points("xyb"))
    if len(raw) < 2:
        return []
    pts = []
    for i in range(len(raw) - 1):
        x0, y0, b = raw[i]
        x1, y1, _ = raw[i + 1]
        x0, y0, x1, y1 = x0 * scale, y0 * scale, x1 * scale, y1 * scale
        if i == 0:
            pts.append((x0, y0))
        if abs(b) < 1e-6:
            pts.append((x1, y1))
        else:
            # Cung tron tu bulge
            chord = math.hypot(x1 - x0, y1 - y0)
            if chord < 1e-9:
                continue
            theta = 4.0 * math.atan(b)
            r = chord / (2.0 * math.sin(abs(theta) / 2.0))
            arc_len = abs(theta) * r
            n_seg = max(2, int(math.ceil(arc_len / max(arc_step, 0.1))))
            # Tam cung tron
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            dx, dy = (x1 - x0) / chord, (y1 - y0) / chord
            nx, ny = -dy, dx
            h = r * math.cos(abs(theta) / 2.0)
            sign = 1.0 if b > 0 else -1.0
            if abs(theta) > math.pi:
                sign = -sign
            cx, cy = mx + sign * nx * h, my + sign * ny * h
            a0 = math.atan2(y0 - cy, x0 - cx)
            for k in range(1, n_seg + 1):
                a = a0 + theta * (k / n_seg)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def extract_alignment_2d(dxf_path: str, handle=None, layer_regex=None, scale=1.0, reverse=False):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    pat = re.compile(layer_regex, re.IGNORECASE) if layer_regex else None
    cands = []
    for e in msp:
        layer = e.dxf.layer if e.dxf.hasattr("layer") else "0"
        if handle and e.dxf.handle.upper() != handle.upper():
            continue
        if not handle and pat and not pat.search(layer):
            continue
        et = e.dxftype()
        pts = []
        if et == "LWPOLYLINE":
            pts = flatten_lwpolyline_2d(e, scale=scale)
        elif et == "POLYLINE":
            pts = [(v.dxf.location.x * scale, v.dxf.location.y * scale) for v in e.vertices]
        elif et == "LINE":
            pts = [(e.dxf.start.x * scale, e.dxf.start.y * scale), (e.dxf.end.x * scale, e.dxf.end.y * scale)]
        elif et == "SPLINE":
            pts = [(p.x * scale, p.y * scale) for p in e.flattening(0.25 / max(scale, 1e-9))]
        if len(pts) < 2:
            continue
        length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
        cands.append({"handle": e.dxf.handle, "type": et, "layer": layer, "length": length, "pts": pts})
    if not cands:
        raise ValueError("Khong tim thay tim tuyen 2D phu hop trong ban ve mat bang.")
    cands.sort(key=lambda x: x["length"], reverse=True)
    chosen = cands[0]
    if reverse:
        chosen["pts"] = list(reversed(chosen["pts"]))
    return chosen


def load_profile_points(profile_json_path: str, z_field="auto"):
    raw = json.loads(Path(profile_json_path).read_text(encoding="utf-8"))
    rows = raw
    # Ho tro truc tiep dinh dang JSON tu cad_profile / cad_profile_tn_tk
    if isinstance(raw, dict):
        if "bang" in raw and isinstance(raw["bang"], list) and raw["bang"]:
            rows = raw["bang"][0].get("cot", raw["bang"][0].get("diem", []))
        elif "points" in raw:
            rows = raw["points"]
        elif "cot" in raw:
            rows = raw["cot"]
    pts = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        st_raw = r.get("station", r.get("ly_trinh", r.get("km")))
        if st_raw is None:
            continue
        st = parse_station(st_raw)
        if z_field == "auto":
            z_tk = r.get("z_tk", r.get("cd_thiet_ke", r.get("cd_dinh", r.get("z"))))
        else:
            z_tk = r.get(z_field)
        z_tn = r.get("z_tn", r.get("cd_tu_nhien"))
        r_vert = r.get("r_vert", r.get("R", r.get("r_cong_dung")))
        if z_tk is None and z_tn is None:
            continue
        pts.append({
            "station": st,
            "z_tk": float(z_tk) if z_tk is not None else None,
            "z_tn": float(z_tn) if z_tn is not None else None,
            "r_vert": float(r_vert) if r_vert is not None and float(r_vert) > 0 else None,
        })
    pts.sort(key=lambda x: x["station"])
    if len(pts) < 2:
        raise ValueError("Bang trac doc phai co it nhat 2 coc/diem co ly trinh va cao do.")
    return pts


def eval_profile_z(pvis, station: float, key="z_tk"):
    """Noi suy cao do tai ly trinh, ho tro duong cong dung Parabol neu PVI co r_vert."""
    valid = [p for p in pvis if p.get(key) is not None]
    if len(valid) < 2:
        return None, "thieu_so_lieu", 0.0
    if station < valid[0]["station"] - 1e-6 or station > valid[-1]["station"] + 1e-6:
        return None, "ngoai_pham_vi_trac_doc", 0.0

    # Kiem tra khop truc tiep coc
    for p in valid:
        if abs(p["station"] - station) < 1e-4 and not p.get("r_vert"):
            return p[key], "bang_trac_doc", 0.0

    # Tim doan chua station + tinh hieu chinh cong dung parabol o cac PVI trong
    # Tinh cao do duong tiep tuyen (duong gay khuc)
    seg = 0
    for i in range(len(valid) - 1):
        if valid[i]["station"] - 1e-6 <= station <= valid[i + 1]["station"] + 1e-6:
            seg = i
            break
    p0, p1 = valid[seg], valid[seg + 1]
    ds = p1["station"] - p0["station"]
    g_seg = (p1[key] - p0[key]) / ds if ds > 1e-9 else 0.0
    z_lin = p0[key] + g_seg * (station - p0["station"])
    src = "noi_suy_tuyen_tinh"
    grade_here = g_seg

    # Kiem tra duong cong dung tai PVI (chi ap dung cho key == z_tk)
    if key == "z_tk":
        for i in range(1, len(valid) - 1):
            r = valid[i].get("r_vert")
            if not r:
                continue
            s_pvi = valid[i]["station"]
            g1 = (valid[i][key] - valid[i - 1][key]) / max(s_pvi - valid[i - 1]["station"], 1e-9)
            g2 = (valid[i + 1][key] - valid[i][key]) / max(valid[i + 1]["station"] - s_pvi, 1e-9)
            dg = g2 - g1
            L = r * abs(dg)
            bvc = s_pvi - L / 2.0
            evc = s_pvi + L / 2.0
            if bvc <= station <= evc and L > 1e-6:
                x = station - bvc
                z_bvc = valid[i][key] - g1 * (L / 2.0)
                z_par = z_bvc + g1 * x + (dg / (2.0 * L)) * (x * x)
                grade_here = g1 + (dg / L) * x
                return z_par, f"noi_suy_parabol_R={r:g}", grade_here * 100.0

    return z_lin, src, grade_here * 100.0


def eval_alignment_xy(pts_2d, cum, rel_station: float):
    seg = 0
    while seg < len(cum) - 2 and cum[seg + 1] < rel_station - 1e-9:
        seg += 1
    d = cum[seg + 1] - cum[seg]
    t = 0.0 if d < 1e-12 else max(0.0, min(1.0, (rel_station - cum[seg]) / d))
    x0, y0 = pts_2d[seg]
    x1, y1 = pts_2d[seg + 1]
    x = x0 + t * (x1 - x0)
    y = y0 + t * (y1 - y0)
    dx, dy = x1 - x0, y1 - y0
    d2 = math.hypot(dx, dy)
    tx, ty = (dx / d2, dy / d2) if d2 > 1e-9 else (1.0, 0.0)
    # Vector phap tuyen ben phai tuyen: (ty, -tx)
    az = math.degrees(math.atan2(tx, ty)) % 360.0
    return x, y, tx, ty, az


def main():
    ap = argparse.ArgumentParser(description="Suy luan cao do 3D tu mat bang tim tuyen 2D + bang trac doc.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("build")
    sp.add_argument("--plan", required=True, help="File mat bang .dwg hoac .dxf chua tim tuyen 2D")
    sp.add_argument("--profile-json", required=True, help="File JSON bang thong so trac doc")
    sp.add_argument("--handle", help="Handle cua tim tuyen 2D")
    sp.add_argument("--layer", help="Regex layer tim tuyen 2D")
    sp.add_argument("--scale", type=float, default=1.0, help="He so quy doi mat bang (vd 0.001 neu mm -> m)")
    sp.add_argument("--reverse", action="store_true", help="Dao nguoc chieu tim tuyen 2D")
    sp.add_argument("--start-station", type=float, default=None, help="Ly trinh diem dau tim tuyen (mac dinh = coc dau trac doc)")
    sp.add_argument("--step", type=float, default=5.0, help="Buoc rai diem 3D (m)")
    sp.add_argument("--offset", type=float, default=0.0, help="Dich ngang khoi tim (+ phai, - trai, m)")
    sp.add_argument("--cross-slope", type=float, default=0.0, help="Do doc ngang % (vd -2.0)")
    sp.add_argument("--z-field", default="auto", help="Ten truong cao do trong JSON (mac dinh auto)")
    sp.add_argument("--out", help="File JSON xuat ket qua")

    args = ap.parse_args()
    dxf_path = ensure_dxf(args.plan)
    align = extract_alignment_2d(dxf_path, handle=args.handle, layer_regex=args.layer, scale=args.scale, reverse=args.reverse)
    pvis = load_profile_points(args.profile_json, z_field=args.z_field)

    pts2d = align["pts"]
    cum = [0.0]
    for i in range(len(pts2d) - 1):
        cum.append(cum[-1] + math.hypot(pts2d[i + 1][0] - pts2d[i][0], pts2d[i + 1][1] - pts2d[i][1]))
    len_2d = cum[-1]

    start_st = args.start_station if args.start_station is not None else pvis[0]["station"]
    prof_span = pvis[-1]["station"] - pvis[0]["station"]
    len_diff = abs(len_2d - prof_span)
    warnings = []
    if len_diff > 0.5:
        warnings.append(
            f"Lech chieu dai giua tim tuyen 2D ({len_2d:.2f} m) va trac doc ({prof_span:.2f} m) = {len_diff:.2f} m. Kiem tra ty le ban ve hoac diem dau/cuoi."
        )

    # Tap ly trinh can tinh: buoc deu + tat ca coc trong trac doc
    rel_stations = set()
    s = 0.0
    while s < len_2d:
        rel_stations.add(round(s, 6))
        s += args.step
    rel_stations.add(round(len_2d, 6))
    for p in pvis:
        r = p["station"] - start_st
        if 0.0 <= r <= len_2d:
            rel_stations.add(round(r, 6))

    dz_off = abs(args.offset) * (args.cross_slope / 100.0)
    points = []
    for rel in sorted(rel_stations):
        st = start_st + rel
        x, y, tx, ty, az = eval_alignment_xy(pts2d, cum, rel)
        # Dich ngang theo phap tuyen ben phai (ty, -tx)
        ox = x + args.offset * ty
        oy = y - args.offset * tx
        z_tk, src_tk, grade_tk = eval_profile_z(pvis, st, "z_tk")
        z_tn, _, _ = eval_profile_z(pvis, st, "z_tn")
        points.append({
            "station": round(st, 4),
            "x": round(ox, 4),
            "y": round(oy, 4),
            "z_tk": round(z_tk + dz_off, 4) if z_tk is not None else None,
            "z_tn": round(z_tn, 4) if z_tn is not None else None,
            "azimuth_deg": round(az, 3),
            "grade_pct": round(grade_tk, 3),
            "source": src_tk,
        })

    result = {
        "alignment": {"handle": align["handle"], "type": align["type"], "layer": align["layer"], "length_2d_m": round(len_2d, 4)},
        "profile_span_m": round(prof_span, 4),
        "length_diff_m": round(len_diff, 4),
        "offset_m": args.offset,
        "cross_slope_pct": args.cross_slope,
        "warnings": warnings,
        "count": len(points),
        "points": points,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Da xuat {len(points)} diem 3D -> {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
