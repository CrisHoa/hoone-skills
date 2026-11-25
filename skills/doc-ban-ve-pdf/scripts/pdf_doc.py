#!/usr/bin/env python3
"""
pdf_doc.py - Cong cu doc va phan tich file PDF (ban ve ky thuat, ho so BIM, bao cao).
Chi doc (read-only), khong bao gio sua file PDF goc.
Yeu cau: pymupdf (pip install pymupdf)
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pymupdf as fitz  # PyMuPDF
except ImportError:
    print(
        "Loi: Chua cai thu vien PyMuPDF (fitz).\n"
        "Cai nhanh bang lenh: python -m pip install pymupdf",
        file=sys.stderr,
    )
    sys.exit(2)


PT_TO_MM = 25.4 / 72.0

PAPER_SIZES_MM = [
    ("A0", 841, 1189),
    ("A1", 594, 841),
    ("A2", 420, 594),
    ("A3", 297, 420),
    ("A4", 210, 297),
]


def detect_paper_size(w_mm: float, h_mm: float) -> str:
    short_s, long_s = sorted([w_mm, h_mm])
    orient = "ngang" if w_mm >= h_mm else "doc"
    for name, s, l in PAPER_SIZES_MM:
        if abs(short_s - s) <= 15 and abs(long_s - l) <= 20:
            return f"{name} ({orient})"
    return f"{w_mm:.0f}x{h_mm:.0f}mm ({orient})"


def parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a_s, b_s = part.split("-", 1)
            a = max(1, int(a_s))
            b = min(total, int(b_s))
            pages.extend(range(a, b + 1))
        else:
            p = int(part)
            if 1 <= p <= total:
                pages.append(p)
    return sorted(set(pages))


def cmd_summary(doc: fitz.Document, args: argparse.Namespace) -> dict:
    meta = doc.metadata or {}
    toc = doc.get_toc(simple=True)
    pages_info = []
    scan_pages = 0
    for i, page in enumerate(doc, start=1):
        r = page.rect
        w_mm = round(r.width * PT_TO_MM, 1)
        h_mm = round(r.height * PT_TO_MM, 1)
        txt = page.get_text("text").strip()
        img_count = len(page.get_images(full=False))
        is_scan = len(txt) < 20 and img_count > 0
        if is_scan:
            scan_pages += 1
        pages_info.append(
            {
                "trang": i,
                "rong_mm": w_mm,
                "cao_mm": h_mm,
                "kho_giay": detect_paper_size(w_mm, h_mm),
                "so_ky_tu": len(txt),
                "so_anh": img_count,
                "dang_scan": is_scan,
            }
        )
    data = {
        "file": str(Path(args.file).resolve()),
        "so_trang": len(doc),
        "so_trang_scan": scan_pages,
        "tieu_de": meta.get("title", ""),
        "tac_gia": meta.get("author", ""),
        "phan_mem_tao": meta.get("creator", "") or meta.get("producer", ""),
        "muc_luc": [{"cap": lvl, "tieu_de": t, "trang": p} for lvl, t, p in toc[:50]],
        "trang": pages_info,
    }
    if not args.json:
        print(f"File: {data['file']}")
        print(f"So trang: {data['so_trang']} (trang scan/anh: {data['so_trang_scan']})")
        if data["tieu_de"]:
            print(f"Tieu de: {data['tieu_de']}")
        if data["phan_mem_tao"]:
            print(f"Phan mem tao: {data['phan_mem_tao']}")
        if data["muc_luc"]:
            print(f"Muc luc ({len(toc)} muc, hien toi da 20):")
            for m in data["muc_luc"][:20]:
                print(f"  {'  ' * (m['cap'] - 1)}- Tr.{m['trang']}: {m['tieu_de']}")
        print("Chi tiet trang (toi da 30 trang dau):")
        for p in pages_info[:30]:
            flag = " [SCAN]" if p["dang_scan"] else ""
            print(
                f"  Tr.{p['trang']:>3}: {p['kho_giay']:<14} | {p['so_ky_tu']:>6} ky tu | {p['so_anh']} anh{flag}"
            )
    return data


def cmd_find(doc: fitz.Document, args: argparse.Namespace) -> dict:
    pattern = re.compile(args.regex, re.IGNORECASE)
    pages = parse_pages(args.pages, len(doc))
    hits = []
    for pno in pages:
        page = doc[pno - 1]
        for line in page.get_text("text").splitlines():
            s = line.strip()
            if s and pattern.search(s):
                hits.append({"trang": pno, "dong": s})
                if len(hits) >= args.limit:
                    break
        if len(hits) >= args.limit:
            break
    data = {"regex": args.regex, "so_ket_qua": len(hits), "ket_qua": hits}
    if not args.json:
        print(f"Tim '{args.regex}': {len(hits)} ket qua")
        for h in hits:
            print(f"  [Tr.{h['trang']}] {h['dong']}")
    return data


def cmd_text(doc: fitz.Document, args: argparse.Namespace) -> dict:
    pages = parse_pages(args.pages, len(doc))
    out_pages = []
    for pno in pages:
        page = doc[pno - 1]
        clip = None
        if args.clip:
            x0, y0, x1, y1 = args.clip
            r = page.rect
            clip = fitz.Rect(r.width * x0, r.height * y0, r.width * x1, r.height * y1)
        txt = page.get_text("text", clip=clip)
        out_pages.append({"trang": pno, "noi_dung": txt})
        if not args.json:
            print(f"=== TRANG {pno} ===")
            print(txt.rstrip())
    return {"trang": out_pages}


def cmd_tables(doc: fitz.Document, args: argparse.Namespace) -> dict:
    pages = parse_pages(args.pages, len(doc))
    all_tables = []
    for pno in pages:
        page = doc[pno - 1]
        finder = page.find_tables()
        for idx, tbl in enumerate(finder.tables, start=1):
            rows = tbl.extract()
            all_tables.append(
                {
                    "trang": pno,
                    "bang": idx,
                    "so_dong": len(rows),
                    "du_lieu": rows,
                }
            )
            if not args.json:
                print(f"=== TRANG {pno} - BANG {idx} ({len(rows)} dong) ===")
                for row in rows:
                    cells = [(c or "").replace("\n", " ").strip() for c in row]
                    print(" | ".join(cells))
    return {"so_bang": len(all_tables), "bang": all_tables}


def cmd_render(doc: fitz.Document, args: argparse.Namespace) -> dict:
    pno = args.page
    if pno < 1 or pno > len(doc):
        raise ValueError(f"Trang {pno} ngoai pham vi 1..{len(doc)}")
    page = doc[pno - 1]
    clip = None
    if args.clip:
        x0, y0, x1, y1 = args.clip
        r = page.rect
        clip = fitz.Rect(r.width * x0, r.height * y0, r.width * x1, r.height * y1)
    zoom = args.dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(out_path))
    data = {
        "trang": pno,
        "dpi": args.dpi,
        "clip": args.clip,
        "width_px": pix.width,
        "height_px": pix.height,
        "out": str(out_path),
    }
    if not args.json:
        print(f"Da xuat trang {pno} -> {out_path} ({pix.width}x{pix.height} px, {args.dpi} DPI)")
    return data


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Doc va phan tich file PDF (chi doc).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sum = sub.add_parser("summary", help="Tong quan PDF: so trang, kho giay, muc luc, trang scan")
    p_sum.add_argument("file")
    p_sum.add_argument("--json", action="store_true")

    p_find = sub.add_parser("find", help="Tim chu theo regex trong PDF")
    p_find.add_argument("file")
    p_find.add_argument("regex")
    p_find.add_argument("--pages", default=None, help="Vi du: 1-5,8,10-12")
    p_find.add_argument("--limit", type=int, default=100)
    p_find.add_argument("--json", action="store_true")

    p_txt = sub.add_parser("text", help="Trich xuat chu theo trang hoac vung clip")
    p_txt.add_argument("file")
    p_txt.add_argument("--pages", default=None, help="Vi du: 1-3,5")
    p_txt.add_argument("--clip", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"), help="Ty le 0..1")
    p_txt.add_argument("--json", action="store_true")

    p_tbl = sub.add_parser("tables", help="Trich xuat bang bieu trong PDF")
    p_tbl.add_argument("file")
    p_tbl.add_argument("--pages", default=None, help="Vi du: 1-3,5")
    p_tbl.add_argument("--json", action="store_true")

    p_ren = sub.add_parser("render", help="Xuat trang hoac vung cat PDF ra anh PNG")
    p_ren.add_argument("file")
    p_ren.add_argument("--page", type=int, default=1)
    p_ren.add_argument("--out", required=True)
    p_ren.add_argument("--dpi", type=int, default=200)
    p_ren.add_argument("--clip", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"), help="Ty le 0..1")
    p_ren.add_argument("--json", action="store_true")

    args = parser.parse_args()
    pdf_path = Path(args.file)
    if not pdf_path.exists():
        print(f"Loi: Khong tim thay file '{args.file}'", file=sys.stderr)
        sys.exit(1)

    with fitz.open(str(pdf_path)) as doc:
        handlers = {
            "summary": cmd_summary,
            "find": cmd_find,
            "text": cmd_text,
            "tables": cmd_tables,
            "render": cmd_render,
        }
        result = handlers[args.cmd](doc, args)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
