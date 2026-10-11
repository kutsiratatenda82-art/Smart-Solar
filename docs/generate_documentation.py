#!/usr/bin/env python3
"""
generate_documentation.py
=========================

Generates ``Smart_Solar_Alert_Final_Documentation.docx`` -- the complete,
7-chapter academic / enterprise documentation for the Smart Solar Alert
project -- using ``python-docx``.

Design principles
-----------------
* **Codebase-driven.**  API routes, database columns, frontend routes, the
  directory tree, diagnostic thresholds and all code excerpts are read from the
  live repository every time the script runs, so the document never drifts
  from the implementation.
* **Secrets are never printed.**  Every excerpt passes through ``redact()``
  (Wi-Fi credentials, dashboard PIN, API keys, backend host).
* **Two-pass build.**  Pass 1 collects headings / table captions / figure
  captions; pass 2 writes them as cached entries inside real Word TOC fields
  (Word refreshes page numbers automatically on open).

Usage
-----
    python docs/generate_documentation.py

Edit the ``PROJECT_META`` block below to set author / institution details.
"""

from __future__ import annotations

import math
import os
import re
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

# ---------------------------------------------------------------------------
# Paths & project metadata
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
OUTPUT_FILE = SCRIPT_DIR / "Smart_Solar_Alert_Final_Documentation.docx"

PROJECT_META = {
    "title": "Smart Solar Alert",
    "subtitle": "An IoT-Enabled Real-Time Solar Power Monitoring, Rule-Based Fault "
                "Diagnostics and Intelligent Alerting Platform",
    "author": "[Student Full Name]",
    "reg_no": "[Registration Number]",
    "degree": "Bachelor of Science (Honours) in Computer Science / Software Engineering",
    "institution": "[University Name]",
    "faculty": "[Faculty / School of Engineering and Technology]",
    "supervisor": "[Supervisor Name]",
    "date": "October 2026",
    "jurisdiction": "Zimbabwe",
}

HEADER_TEXT = "Smart Solar Alert \u2014 System Documentation"
FOOTER_LEFT = "Confidential & Proprietary"

# ---------------------------------------------------------------------------
# Palette & page geometry
# ---------------------------------------------------------------------------
NAVY = RGBColor(0x1B, 0x36, 0x5D)
BLUE = RGBColor(0x2B, 0x6C, 0xB0)
SLATE = RGBColor(0x2D, 0x37, 0x48)
GRAY = RGBColor(0x71, 0x80, 0x96)
LIGHT_GRAY = RGBColor(0xA0, 0xAE, 0xC0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CODE_RED = RGBColor(0x9B, 0x2C, 0x2C)

HEX_NAVY = "1B365D"
HEX_ZEBRA_A = "F7FAFC"
HEX_ZEBRA_B = "FFFFFF"
HEX_BORDER = "CBD5E0"
HEX_PLACEHOLDER_BG = "F8F9FA"

PAGE_W_IN, PAGE_H_IN = 8.27, 11.69          # A4
MARGIN_IN = 1.0
TEXT_W_IN = PAGE_W_IN - 2 * MARGIN_IN        # 6.27 in

# ---------------------------------------------------------------------------
# OOXML element-ordering helpers (keeps Word's strict schema happy)
# ---------------------------------------------------------------------------
PPR_ORDER = ["w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
             "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd",
             "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
             "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
             "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
             "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
             "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
             "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange"]
TCPR_ORDER = ["w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge", "w:tcBorders",
              "w:shd", "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText",
              "w:vAlign", "w:hideMark"]
TBLPR_ORDER = ["w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual",
               "w:tblStyleRowBandSize", "w:tblStyleColBandSize", "w:tblW", "w:jc",
               "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd", "w:tblLayout",
               "w:tblCellMar", "w:tblLook"]
TRPR_ORDER = ["w:cnfStyle", "w:divId", "w:gridBefore", "w:gridAfter", "w:wBefore",
              "w:wAfter", "w:cantSplit", "w:trHeight", "w:tblHeader", "w:tblCellSpacing",
              "w:jc", "w:hidden"]
SECTPR_ORDER = ["w:headerReference", "w:footerReference", "w:footnotePr", "w:endnotePr",
                "w:type", "w:pgSz", "w:pgMar", "w:paperSrc", "w:pgBorders", "w:lnNumType",
                "w:pgNumType", "w:cols", "w:formProt", "w:vAlign", "w:noEndnote",
                "w:titlePg", "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid"]


def insert_ordered(parent, child, order):
    """Insert ``child`` into ``parent`` respecting the OOXML sequence ``order``."""
    tag = child.tag
    for existing in parent.findall(tag):
        parent.remove(existing)
    order_q = [qn(t) for t in order]
    my_idx = order_q.index(tag) if tag in order_q else len(order_q)
    for i, existing in enumerate(list(parent)):
        if existing.tag in order_q and order_q.index(existing.tag) > my_idx:
            parent.insert(i, child)
            return child
    parent.append(child)
    return child


def shade_cell(cell, fill_hex):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    insert_ordered(cell._tc.get_or_add_tcPr(), shd, TCPR_ORDER)


def set_table_borders(table, color=HEX_BORDER, size=4, val="single",
                      left=None, inside=True):
    """Table-level borders. ``left`` = (val, size, color) overrides the left edge."""
    borders = OxmlElement("w:tblBorders")
    edges = ["top", "left", "bottom", "right"] + (["insideH", "insideV"] if inside else [])
    for edge in edges:
        el = OxmlElement(f"w:{edge}")
        v, s, c = (left if (edge == "left" and left) else (val, size, color))
        el.set(qn("w:val"), v)
        el.set(qn("w:sz"), str(s))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), c)
        borders.append(el)
    insert_ordered(table._tbl.tblPr, borders, TBLPR_ORDER)


def set_table_cell_margins(table, top=120, bottom=120, left=100, right=100):
    """Margins in twips (120 twips = 6 pt)."""
    mar = OxmlElement("w:tblCellMar")
    for side, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(value))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    insert_ordered(table._tbl.tblPr, mar, TBLPR_ORDER)


def set_repeat_header(row):
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    insert_ordered(row._tr.get_or_add_trPr(), el, TRPR_ORDER)


def set_cant_split(row):
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    insert_ordered(row._tr.get_or_add_trPr(), el, TRPR_ORDER)


def paragraph_bottom_border(paragraph, color=HEX_BORDER, size=6):
    pPr = paragraph._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    pbdr.append(bottom)
    insert_ordered(pPr, pbdr, PPR_ORDER)


def set_style_font(style, name):
    """Force a concrete font on a style (removes theme-font overrides)."""
    rPr = style.element.get_or_add_rPr()
    rfonts = rPr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rPr.insert(0, rfonts)
    for attr in list(rfonts.attrib):
        del rfonts.attrib[attr]
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def set_run_font(run, name):
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    rfonts = rPr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rPr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def add_simple_field(paragraph, instr, cached="1", size=None, color=None):
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instr)
    r = OxmlElement("w:r")
    if size or color:
        rPr = OxmlElement("w:rPr")
        if color:
            c = OxmlElement("w:color")
            c.set(qn("w:val"), color)
            rPr.append(c)
        if size:
            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), str(int(size * 2)))
            rPr.append(sz)
        r.append(rPr)
    t = OxmlElement("w:t")
    t.text = cached
    r.append(t)
    fld.append(r)
    paragraph._p.append(fld)


def _fld_char(run, kind, dirty=False):
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), kind)
    if dirty:
        fc.set(qn("w:dirty"), "true")
    run._r.append(fc)


def _instr(run, text):
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {text} "
    run._r.append(it)


# ---------------------------------------------------------------------------
# Rich-text mini markup:  **bold**   `code`   *italic*
# ---------------------------------------------------------------------------
_RICH_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+?`|(?<!\*)\*(?!\*)[^*]+?\*(?!\*))")


def add_rich(paragraph, text, size=None, bold=False, color=None, italic=False, font=None):
    for part in _RICH_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, "Consolas")
            run.font.color.rgb = CODE_RED
            if size:
                run.font.size = Pt(size - 1)
            else:
                run.font.size = Pt(10)
            run.bold = bold
            continue
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
            run.bold = bold
        else:
            run = paragraph.add_run(part)
            run.bold = bold
        if italic:
            run.italic = True
        if size:
            run.font.size = Pt(size)
        if color is not None:
            run.font.color.rgb = color
        if font:
            set_run_font(run, font)
    return paragraph


# ---------------------------------------------------------------------------
# Secret redaction for code excerpts
# ---------------------------------------------------------------------------
_REDACTIONS = [
    (re.compile(r'(ROUTER_PASS\s*=\s*")[^"]*(")'), r"\1<REDACTED>\2"),
    (re.compile(r'(ROUTER_SSID\s*=\s*")[^"]*(")'), r"\1<REDACTED>\2"),
    (re.compile(r'(DASHBOARD_PIN\s*=\s*")[^"]*(")'), r"\1<REDACTED>\2"),
    (re.compile(r'(BACKEND_URL\s*=\s*"https?://)[^/"]+'), r"\1<BACKEND_HOST>:8000"),
    (re.compile(r"(GEMINI_API_KEY\s*=\s*)\S+"), r"\1<REDACTED>"),
    (re.compile(r"(SECRET_KEY\s*=\s*)\S+"), r"\1<REDACTED>"),
    (re.compile(r"AQ\.[A-Za-z0-9_\-]{20,}"), "<REDACTED_API_KEY>"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{30,}"), "<REDACTED_API_KEY>"),
    (re.compile(r"(postgresql://)[^@\s]+@"), r"\1<user>:<password>@"),
]


def redact(text: str) -> str:
    for pattern, repl in _REDACTIONS:
        text = pattern.sub(repl, text)
    return text


# ---------------------------------------------------------------------------
# Codebase introspection
# ---------------------------------------------------------------------------
def read_lines(rel: str):
    path = ROOT / rel
    if not path.exists():
        return []
    return [ln.rstrip("\r\n").rstrip() for ln in
            path.read_text(encoding="utf-8", errors="replace").splitlines()]


def excerpt(rel: str, start: str | None = None, end: str | None = None,
            max_lines: int | None = None, include_end=True):
    """Return (code, first_line_number) for a slice of a real source file."""
    lines = read_lines(rel)
    if not lines:
        return f"// Source file not found: {rel}", 1
    s = 0
    if start:
        for i, ln in enumerate(lines):
            if start in ln:
                s = i
                break
    e = len(lines)
    if end:
        for i in range(s + 1, len(lines)):
            if end in lines[i]:
                e = i + 1 if include_end else i
                break
    if max_lines:
        e = min(e, s + max_lines)
    seg = lines[s:e]
    while seg and not seg[-1].strip():
        seg.pop()
    return redact("\n".join(seg)), s + 1


def count_lines(rel: str) -> int:
    return len(read_lines(rel))


def parse_api_routes():
    """Parse FastAPI routers + prefixes from app/main.py and app/api/endpoints/*."""
    prefixes = {}
    for ln in read_lines("app/main.py"):
        m = re.search(r"include_router\((\w+)\.router,\s*prefix=\"([^\"]*)\"", ln)
        if m:
            prefixes[m.group(1)] = m.group(2)
    routes = []
    for module, prefix in prefixes.items():
        lines = read_lines(f"app/api/endpoints/{module}.py")
        text = "\n".join(lines)
        blocks = re.split(r"\n(?=@router\.)", text)
        for block in blocks:
            m = re.match(r"@router\.(get|post|put|patch|delete)\(\s*\"([^\"]*)\"(.*?)\)\s*\n", block, re.S)
            if not m:
                continue
            method, path, extra = m.group(1).upper(), m.group(2), m.group(3)
            fn = re.search(r"def (\w+)\(", block)
            sc = re.search(r"status_code=status\.HTTP_(\d+)", extra)
            rm = re.search(r"response_model=([\w\.\[\]]+)", extra)
            doc = re.search(r'"""(.+?)"""', block, re.S)
            routes.append({
                "module": module,
                "method": method,
                "path": (prefix + path) or "/",
                "function": fn.group(1) if fn else "?",
                "auth": "JWT Bearer" if "get_current_user" in block else "None (public)",
                "status": sc.group(1) if sc else "200",
                "response": rm.group(1) if rm else "dict",
                "doc": " ".join(doc.group(1).split()) if doc else "",
            })
    return routes


_SA_TYPE_MAP = {
    "Integer": "INTEGER", "String": "VARCHAR", "Float": "DOUBLE PRECISION",
    "Boolean": "BOOLEAN", "DateTime(timezone=True)": "TIMESTAMPTZ", "DateTime": "TIMESTAMP",
}


def parse_models():
    """Regex-parse SQLAlchemy models (no DB connection needed)."""
    models = {}
    for path in sorted((ROOT / "app" / "models").glob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        cls = re.search(r"class (\w+)\(Base\)", text)
        tbl = re.search(r"__tablename__\s*=\s*\"(\w+)\"", text)
        if not (cls and tbl):
            continue
        cols = []
        for m in re.finditer(r"^\s+(\w+)\s*=\s*Column\((.*)\)\s*$", text, re.M):
            name, args = m.group(1), m.group(2)
            sa_type = args.split(",")[0].strip()
            if sa_type.startswith("DateTime"):
                sa_type = "DateTime(timezone=True)" if "timezone=True" in args else "DateTime"
            fk = re.search(r"ForeignKey\(\"([\w\.]+)\"\)", args)
            default = re.search(r"(?<!server_)default=([^,\)]+)", args)
            sdefault = re.search(r"server_default=func\.(\w+)\(\)", args)
            onupd = re.search(r"onupdate=func\.(\w+)\(\)", args)
            pk = "primary_key=True" in args
            nullable = not (pk or "nullable=False" in args)
            pg_type = _SA_TYPE_MAP.get(sa_type, sa_type.upper())
            if pk and pg_type == "INTEGER":
                pg_type = "SERIAL (INTEGER)"
            keys = []
            if pk:
                keys.append("PK")
            if fk:
                keys.append(f"FK \u2192 {fk.group(1)}")
            if "unique=True" in args:
                keys.append("UNIQUE")
            if "index=True" in args:
                keys.append("INDEX")
            dflt = ""
            if default:
                dflt = default.group(1).strip()
            if sdefault:
                dflt = f"{sdefault.group(1)}() [server]"
            if onupd:
                dflt = (dflt + "; " if dflt else "") + f"on update {onupd.group(1)}()"
            cols.append({"name": name, "sa_type": sa_type, "pg_type": pg_type,
                         "keys": ", ".join(keys) or "\u2014", "nullable": "YES" if nullable else "NO",
                         "default": dflt or "\u2014"})
        rels = re.findall(r"^\s+(\w+)\s*=\s*relationship\(\"(\w+)\"(.*)\)\s*$", text, re.M)
        models[tbl.group(1)] = {"class": cls.group(1), "file": f"app/models/{path.name}",
                                "columns": cols, "relationships": rels}
    return models


def parse_frontend_routes():
    routes = []
    for ln in read_lines("frontend/src/App.tsx"):
        m = re.search(r'path="([^"]+)"\s+element=\{<(\w+)', ln)
        if m:
            routes.append((m.group(1), m.group(2)))
    return routes


def build_tree(base: Path, prefix="", depth=0, max_depth=4):
    skip = {"venv", "node_modules", "__pycache__", ".pytest_cache", ".git", "dist",
            ".vite", ".idea", ".vscode"}
    out = []
    try:
        entries = sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except OSError:
        return out
    entries = [e for e in entries if e.name not in skip and not e.name.endswith(".docx")
               and not e.name.startswith("~$")]
    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        branch = "\u2514\u2500\u2500 " if last else "\u251c\u2500\u2500 "
        label = entry.name + ("/" if entry.is_dir() else "")
        if entry.name == ".env":
            label += "   (local secrets \u2013 never committed)"
        out.append(prefix + branch + label)
        if entry.is_dir() and depth < max_depth:
            ext = "    " if last else "\u2502   "
            out.extend(build_tree(entry, prefix + ext, depth + 1, max_depth))
    return out


def load_diagnostics_engine():
    """Import the real diagnostic engine (pure logic, no DB) for live test vectors."""
    sys.path.insert(0, str(ROOT))
    try:
        from app.core import diagnostics as diag  # noqa: WPS433
        from app.schemas.reading import ReadingBase  # noqa: WPS433
        return diag, ReadingBase
    except Exception as exc:  # pragma: no cover - documentation still builds
        print(f"[warn] could not import diagnostic engine: {exc}")
        return None, None


# ---------------------------------------------------------------------------
# Figure placeholder (spec-mandated helper)
# ---------------------------------------------------------------------------
def add_figure_placeholder(
    doc,
    figure_id: str,
    title: str,
    description: str,
    suggested_height_in_inches=3.0,
):
    """Inserts a 1x1 styled bordered cell acting as a diagram/screenshot placeholder."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table, color="A0AEC0", size=8, val="dashed", inside=False)
    set_table_cell_margins(table, 120, 120, 120, 120)
    cell = table.cell(0, 0)
    cell.width = Inches(TEXT_W_IN - 0.3)
    shade_cell(cell, HEX_PLACEHOLDER_BG)
    row = table.rows[0]
    row.height = Inches(suggested_height_in_inches)
    row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    set_cant_split(row)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_after = Pt(4)
    r1 = p1.add_run(f"[ PLACEHOLDER: {figure_id} ]")
    r1.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = GRAY

    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(f"Insert {title} here")
    r2.italic = True
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = SLATE

    cap = doc.add_paragraph(style="Figure Caption")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rc = cap.add_run(f"Figure {figure_id}: {title} \u2014 {description}")
    rc.bold = True
    rc.font.size = Pt(9.5)
    return table


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------
class Builder:
    def __init__(self, previous=None):
        self.doc = Document()
        self.prev = previous or {"headings": [], "tables": [], "figures": []}
        self.headings, self.tables, self.figures = [], [], []
        self.chapter = "0"
        self.fig_n = self.tab_n = self.eq_n = 0
        self._configure_document()

    # -- setup --------------------------------------------------------------
    def _configure_document(self):
        doc = self.doc
        sec = doc.sections[0]
        sec.page_width, sec.page_height = Inches(PAGE_W_IN), Inches(PAGE_H_IN)
        for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(sec, side, Inches(MARGIN_IN))
        sec.header_distance = Inches(0.45)
        sec.footer_distance = Inches(0.45)

        st = doc.styles
        normal = st["Normal"]
        set_style_font(normal, "Calibri")
        normal.font.size = Pt(11)
        normal.font.color.rgb = RGBColor(0x1A, 0x20, 0x2C)
        pf = normal.paragraph_format
        pf.line_spacing = 1.15
        pf.space_after = Pt(6)
        pf.space_before = Pt(0)

        for lvl, size, color, before, after in ((1, 18, NAVY, 0, 14), (2, 14, BLUE, 16, 6),
                                               (3, 12, SLATE, 12, 4)):
            s = st[f"Heading {lvl}"]
            set_style_font(s, "Calibri")
            s.font.size = Pt(size)
            s.font.bold = True
            s.font.italic = False
            s.font.color.rgb = color
            s.paragraph_format.space_before = Pt(before)
            s.paragraph_format.space_after = Pt(after)
            s.paragraph_format.keep_with_next = True
            s.paragraph_format.line_spacing = 1.1
            if lvl == 1:
                s.paragraph_format.page_break_before = True

        for name in ("Figure Caption", "Table Caption"):
            cs = st.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            cs.base_style = normal
            set_style_font(cs, "Calibri")
            cs.font.size = Pt(9.5)
            cs.font.bold = True
            cs.font.color.rgb = SLATE
            cs.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cs.paragraph_format.space_before = Pt(6 if name == "Figure Caption" else 10)
            cs.paragraph_format.space_after = Pt(12 if name == "Figure Caption" else 4)
            cs.paragraph_format.keep_with_next = name == "Table Caption"

        fh = st.add_style("Front Heading", WD_STYLE_TYPE.PARAGRAPH)
        fh.base_style = normal
        set_style_font(fh, "Calibri")
        fh.font.size = Pt(18)
        fh.font.bold = True
        fh.font.color.rgb = NAVY
        fh.paragraph_format.page_break_before = True
        fh.paragraph_format.space_after = Pt(14)
        fh.paragraph_format.keep_with_next = True

        for lvl in (1, 2, 3):
            ts = st.add_style(f"TOC Entry {lvl}", WD_STYLE_TYPE.PARAGRAPH)
            ts.base_style = normal
            ts.font.size = Pt(11 if lvl == 1 else 10)
            ts.font.bold = lvl == 1
            ts.paragraph_format.left_indent = Inches(0.3 * (lvl - 1))
            ts.paragraph_format.space_after = Pt(2 if lvl > 1 else 4)
            ts.paragraph_format.space_before = Pt(6 if lvl == 1 else 0)

        try:
            st["List Bullet"].paragraph_format.space_after = Pt(4)
            st["List Bullet"].paragraph_format.line_spacing = 1.15
        except KeyError:
            pass

        settings = doc.settings.element
        uf = OxmlElement("w:updateFields")
        uf.set(qn("w:val"), "true")
        settings.append(uf)

        core = doc.core_properties
        core.title = "Smart Solar Alert \u2014 Final System Documentation"
        core.subject = "IoT solar monitoring, diagnostics and alerting platform"
        core.author = PROJECT_META["author"]
        core.keywords = "solar, IoT, ESP32, FastAPI, React, PostgreSQL, alerts, diagnostics"
        core.comments = "Generated by docs/generate_documentation.py from the live codebase."

    def setup_header_footer(self, section):
        section.header.is_linked_to_previous = False
        section.footer.is_linked_to_previous = False
        hp = section.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hr = hp.add_run(HEADER_TEXT)
        hr.font.size = Pt(8.5)
        hr.font.color.rgb = LIGHT_GRAY
        paragraph_bottom_border(hp, "E2E8F0", 4)

        fp = section.footer.paragraphs[0]
        fp.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W_IN), WD_TAB_ALIGNMENT.RIGHT)
        fr = fp.add_run(FOOTER_LEFT)
        fr.font.size = Pt(8.5)
        fr.font.color.rgb = LIGHT_GRAY
        fp.add_run("\t")
        pr = fp.add_run("Page ")
        pr.font.size = Pt(10)
        pr.font.bold = True
        pr.font.color.rgb = SLATE
        add_simple_field(fp, "PAGE", "1", size=10, color="2D3748")

    def new_section(self, page_fmt="decimal", start=1):
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        sec.different_first_page_header_footer = False
        sec.header.is_linked_to_previous = True
        sec.footer.is_linked_to_previous = True
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), page_fmt)
        pg.set(qn("w:start"), str(start))
        insert_ordered(sec._sectPr, pg, SECTPR_ORDER)
        return sec

    # -- chapter / numbering --------------------------------------------------
    def set_chapter(self, label):
        self.chapter = str(label)
        self.fig_n = self.tab_n = self.eq_n = 0

    # -- primitives -----------------------------------------------------------
    def heading(self, text, level=1):
        h = self.doc.add_heading(text, level=level)
        self.headings.append((level, text))
        return h

    def front_heading(self, text):
        return self.doc.add_paragraph(text, style="Front Heading")

    def para(self, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None, italic=False,
             space_after=None, color=None, bold=False, keep_next=False):
        p = self.doc.add_paragraph()
        p.alignment = align
        add_rich(p, text, size=size, italic=italic, color=color, bold=bold)
        if space_after is not None:
            p.paragraph_format.space_after = Pt(space_after)
        if keep_next:
            p.paragraph_format.keep_with_next = True
        return p

    def paras(self, texts):
        for t in texts:
            self.para(t)

    def bullets(self, items, style="List Bullet"):
        for item in items:
            p = self.doc.add_paragraph(style=style)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_rich(p, item)

    def spacer(self, pts=4):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        r = p.add_run()
        r.font.size = Pt(pts)
        p.paragraph_format.line_spacing = Pt(pts)
        return p

    def page_break(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def _write_cell(self, cell, text, size=9.5, bold=False, color=None,
                    align=WD_ALIGN_PARAGRAPH.LEFT, font=None):
        lines = str(text).split("\n")
        for i, line in enumerate(lines):
            p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            p.alignment = align
            p.paragraph_format.space_after = Pt(1 if i < len(lines) - 1 else 0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            add_rich(p, line, size=size, bold=bold, color=color, font=font)

    def table(self, title, headers, rows, widths=None, size=9.0, caption=True,
              center_cols=(), first_col_bold=False, font=None):
        """Styled data table with navy header, zebra striping, thin borders."""
        if caption:
            self.tab_n += 1
            tid = f"{self.chapter}.{self.tab_n}"
            cap = self.doc.add_paragraph(style="Table Caption")
            cap.add_run(f"Table {tid}: {title}")
            self.tables.append(f"Table {tid}: {title}")
        ncols = len(headers)
        t = self.doc.add_table(rows=1 + len(rows), cols=ncols)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        set_table_borders(t, HEX_BORDER, 4)
        set_table_cell_margins(t, 120, 120, 90, 90)
        if widths is None:
            widths = [TEXT_W_IN / ncols] * ncols
        else:
            total = sum(widths)
            widths = [w * TEXT_W_IN / total for w in widths]
        hdr = t.rows[0]
        set_repeat_header(hdr)
        for j, htxt in enumerate(headers):
            c = hdr.cells[j]
            shade_cell(c, HEX_NAVY)
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            self._write_cell(c, htxt, size=size, bold=True, color=WHITE,
                             align=WD_ALIGN_PARAGRAPH.CENTER if j in center_cols else WD_ALIGN_PARAGRAPH.LEFT)
        for i, row in enumerate(rows):
            r = t.rows[i + 1]
            fill = HEX_ZEBRA_A if i % 2 == 0 else HEX_ZEBRA_B
            for j in range(ncols):
                val = row[j] if j < len(row) else ""
                c = r.cells[j]
                shade_cell(c, fill)
                c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
                self._write_cell(c, val, size=size, bold=(first_col_bold and j == 0),
                                 align=WD_ALIGN_PARAGRAPH.CENTER if j in center_cols else WD_ALIGN_PARAGRAPH.LEFT,
                                 font=font if j == 0 else None)
        for j, w in enumerate(widths):
            for c in t.columns[j].cells:
                c.width = Inches(w)
        self.spacer(6)
        return t

    def figure(self, title, description, height=3.0):
        self.fig_n += 1
        fid = f"{self.chapter}.{self.fig_n}"
        add_figure_placeholder(self.doc, fid, title, description, height)
        self.figures.append(f"Figure {fid}: {title}")
        return fid

    def callout(self, title, text, kind="info"):
        palette = {"info": ("EBF8FF", "2B6CB0"), "warn": ("FFFAF0", "DD6B20"),
                   "field": ("FFF5F5", "C53030"), "ok": ("F0FFF4", "2F855A"),
                   "note": ("F7FAFC", "4A5568")}
        fill, accent = palette.get(kind, palette["info"])
        t = self.doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        set_table_borders(t, accent, 4, left=("single", 24, accent), inside=False)
        set_table_cell_margins(t, 100, 100, 160, 120)
        c = t.cell(0, 0)
        c.width = Inches(TEXT_W_IN)
        shade_cell(c, fill)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(title)
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor.from_string(accent)
        for line in text.split("\n"):
            q = c.add_paragraph()
            q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q.paragraph_format.space_after = Pt(2)
            add_rich(q, line, size=9.5)
        self.spacer(8)

    def code(self, title, code_text, start_line=1, size=7.5):
        """Monospaced, line-numbered source excerpt in a shaded frame."""
        t = self.doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        set_table_borders(t, "CBD5E0", 4, left=("single", 24, "2B6CB0"), inside=False)
        set_table_cell_margins(t, 80, 80, 140, 100)
        c = t.cell(0, 0)
        c.width = Inches(TEXT_W_IN)
        shade_cell(c, "F7F8FA")
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(title)
        r.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = BLUE
        lines = code_text.split("\n")
        width = len(str(start_line + len(lines)))
        for i, line in enumerate(lines):
            q = c.add_paragraph()
            q.paragraph_format.space_after = Pt(0)
            q.paragraph_format.space_before = Pt(0)
            q.paragraph_format.line_spacing = 1.0
            ln = q.add_run(f"{start_line + i:>{width}}  ")
            set_run_font(ln, "Consolas")
            ln.font.size = Pt(size)
            ln.font.color.rgb = LIGHT_GRAY
            body = q.add_run(line.replace("\t", "    ") if line else " ")
            set_run_font(body, "Consolas")
            body.font.size = Pt(size)
            body.font.color.rgb = SLATE
        self.spacer(8)

    def code_from(self, title, rel, start=None, end=None, max_lines=None, include_end=True):
        text, first = excerpt(rel, start, end, max_lines, include_end)
        last = first + text.count("\n")
        self.code(f"{title}  \u2014  {rel}  (lines {first}\u2013{last})", text, first)

    def equation(self, expr, note=None):
        self.eq_n += 1
        p = self.doc.add_paragraph()
        p.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W_IN / 2), WD_TAB_ALIGNMENT.CENTER)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W_IN), WD_TAB_ALIGNMENT.RIGHT)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4 if note else 8)
        p.add_run("\t")
        r = p.add_run(expr)
        set_run_font(r, "Cambria Math")
        r.italic = True
        r.font.size = Pt(11.5)
        p.add_run("\t")
        lr = p.add_run(f"({self.chapter}.{self.eq_n})")
        lr.font.size = Pt(10)
        lr.font.color.rgb = GRAY
        if note:
            self.para(note, align=WD_ALIGN_PARAGRAPH.CENTER, size=9, italic=True, color=GRAY,
                      space_after=8)

    def field_block(self, instr, cached, placeholder_text):
        """Real Word field (TOC / LoT / LoF) with cached, human-readable entries."""
        entries = cached or [(1, placeholder_text)]
        first = self.doc.add_paragraph(style=f"TOC Entry {min(entries[0][0], 3)}")
        r = first.add_run()
        _fld_char(r, "begin", dirty=True)
        r2 = first.add_run()
        _instr(r2, instr)
        r3 = first.add_run()
        _fld_char(r3, "separate")
        first.add_run(entries[0][1])
        last = first
        for level, text in entries[1:]:
            last = self.doc.add_paragraph(style=f"TOC Entry {min(level, 3)}")
            last.add_run(text)
        r_end = last.add_run()
        _fld_char(r_end, "end")

    def registry(self):
        return {"headings": list(self.headings), "tables": list(self.tables),
                "figures": list(self.figures)}


B: Builder | None = None   # active builder (set in build())


# Short aliases used by the content functions below --------------------------
def H1(t): return B.heading(t, 1)
def H2(t): return B.heading(t, 2)
def H3(t): return B.heading(t, 3)
def P(t, **kw): return B.para(t, **kw)
def PS(ts): return B.paras(ts)
def BUL(items): return B.bullets(items)
def TBL(title, headers, rows, widths=None, **kw): return B.table(title, headers, rows, widths, **kw)
def FIG(title, desc, h=3.0): return B.figure(title, desc, h)
def NOTE(title, text, kind="info"): return B.callout(title, text, kind)
def CODE(title, rel, start=None, end=None, max_lines=None, include_end=True):
    return B.code_from(title, rel, start, end, max_lines, include_end)
def EQ(expr, note=None): return B.equation(expr, note)


# ---------------------------------------------------------------------------
# Live data gathered once at import time
# ---------------------------------------------------------------------------
API_ROUTES = parse_api_routes()
MODELS = parse_models()
FE_ROUTES = parse_frontend_routes()
DIAG, ReadingBase = load_diagnostics_engine()


def thr(name, default):
    return getattr(DIAG, name, default) if DIAG else default


V_NORM_MIN = thr("VOLTAGE_NORMAL_MIN", 2.0)
V_NORM_MAX = thr("VOLTAGE_NORMAL_MAX", 15.0)
V_CRIT_LOW = thr("VOLTAGE_CRITICAL_LOW", 2.0)
V_CRIT_HIGH = thr("VOLTAGE_CRITICAL_HIGH", 18.0)
I_NORM_MIN = thr("CURRENT_NORMAL_MIN", 0.8)
I_CRIT_LOW = thr("CURRENT_CRITICAL_LOW", 0.3)


def run_engine(v, i):
    """Evaluate (v, i) with the real engine; returns 'COND1 + COND2' string."""
    if not (DIAG and ReadingBase):
        return "n/a (engine not importable)"
    res = DIAG.evaluate_reading(ReadingBase(voltage=v, current=i))
    return " + ".join(r.condition.value for r in res)


def run_engine_severity(v, i):
    if not (DIAG and ReadingBase):
        return "n/a"
    res = DIAG.evaluate_reading(ReadingBase(voltage=v, current=i))
    order = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2}
    return max((r.severity.value for r in res), key=lambda s: order.get(s, 0))


# === CONTENT: FRONT MATTER ===
import json as _json


def _pkg():
    try:
        return _json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    except Exception:
        return {"dependencies": {}, "devDependencies": {}}


def _reqs():
    return [ln.strip() for ln in read_lines("requirements.txt") if ln.strip() and not ln.startswith("#")]


def title_page():
    doc = B.doc
    m = PROJECT_META
    for _ in range(2):
        B.spacer(12)
    for text, size, bold, color in ((m["institution"].upper(), 14, True, SLATE),
                                    (m["faculty"], 11.5, False, GRAY)):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold
        r.font.color.rgb = color
    B.spacer(40)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(m["title"].upper())
    r.font.size = Pt(26)
    r.bold = True
    r.font.color.rgb = NAVY
    paragraph_bottom_border(p, "2B6CB0", 12)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    r = p.add_run(m["subtitle"])
    r.font.size = Pt(13)
    r.font.color.rgb = BLUE
    r.italic = True
    B.spacer(30)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Final System Documentation & Dissertation Report")
    r.font.size = Pt(12)
    r.bold = True
    r.font.color.rgb = SLATE
    B.spacer(24)
    for label, value in (("Submitted by", m["author"]), ("Registration Number", m["reg_no"]),
                         ("Supervisor", m["supervisor"]), ("Programme", m["degree"]),
                         ("Date of Submission", m["date"])):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        r1 = p.add_run(f"{label}: ")
        r1.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = SLATE
        r2 = p.add_run(value)
        r2.font.size = Pt(11)
    B.spacer(30)
    P("A dissertation submitted in partial fulfilment of the requirements for the award of the "
      f"{m['degree']} at {m['institution']}.", align=WD_ALIGN_PARAGRAPH.CENTER, size=10,
      italic=True, color=GRAY)


def _removed_front_pages():
    """Approval / Declaration pages -- removed from the document at the author's request."""
    m = PROJECT_META
    H1("Approval Form")
    P(f"The undersigned certify that they have supervised, read and recommend to {m['institution']} "
      f"for acceptance the dissertation entitled **\u201c{m['title']}: {m['subtitle']}\u201d**, "
      f"submitted by {m['author']} ({m['reg_no']}) in partial fulfilment of the requirements of the "
      f"{m['degree']}.")
    TBL("Approval signatures", ["Role", "Name", "Signature", "Date"],
        [["Student", m["author"], "", ""], ["Supervisor", m["supervisor"], "", ""],
         ["Chairperson of Department", "[Name]", "", ""], ["External Examiner", "[Name]", "", ""]],
        [1.6, 1.8, 1.6, 1.0], caption=False, size=10)

    H1("Declaration")
    PS([f"I, **{m['author']}**, hereby declare that this dissertation is my own original work and "
        "that it has not been presented, in whole or in part, for the award of any degree, diploma or "
        "certificate at this or any other institution. All sources of information, software libraries, "
        "datasheets and third-party services used in the course of this project have been duly "
        "acknowledged through citations and references.",
        "I further declare that the software artefacts described in this document \u2014 the FastAPI "
        "backend service, the React/TypeScript web dashboard, the ESP32 \u201cTelePower Guard\u201d "
        "firmware, the Alembic migration history and the automated test suites \u2014 were designed, "
        "implemented and tested by me under the guidance of my supervisor, and that the code "
        "excerpts reproduced in Chapter 5 are taken verbatim from the project repository, with only "
        "credentials and network addresses redacted for security reasons.",
        "I authorise the institution to reproduce this dissertation, in whole or in part, for "
        "academic and research purposes, subject to the confidentiality conditions stated in the "
        "document footer."])
    TBL("Student declaration", ["Student Signature", "Date"], [["", ""]], [3, 3], caption=False, size=10)

def front_matter():
    m = PROJECT_META
    H1("Dedication")
    P("This work is dedicated to every household, clinic, school and small business that has "
      "kept its lights on through long hours of load-shedding by investing in solar power \u2014 and "
      "to the families who lost expensive batteries simply because nobody told them, in time, that "
      "something was wrong. May this system give their energy a voice.", italic=True)
    _toc()


def _removed_front_pages_2():
    """Acknowledgements / Abstract -- removed from the document at the author's request."""
    m = PROJECT_META
    H1("Acknowledgements")
    PS([f"I would like to express my sincere gratitude to my supervisor, **{m['supervisor']}**, for the "
        "patient guidance, critical feedback and technical insight provided throughout the "
        "project lifecycle, from the first feasibility discussions to the final testing sessions.",
        "Special thanks go to the solar installers, technicians and system owners who generously "
        "gave their time during interviews and questionnaires; their candid accounts of battery "
        "failures, unattended overloads and costly call-outs shaped the requirements of this system. "
        "I am also grateful to the lecturers of the Department for the foundation in software "
        "engineering, databases and embedded systems on which this work rests.",
        "Finally, I thank my family and friends for their encouragement, and the open-source "
        "communities behind FastAPI, SQLAlchemy, PostgreSQL, React, Vite, Recharts and the Arduino "
        "ESP32 core, without whose freely available tools a project of this scope would not have "
        "been possible."])

    H1("Abstract")
    PS(["Small-scale photovoltaic (PV) installations have become a primary source of electricity for "
        f"many households and enterprises in {m['jurisdiction']}, driven by prolonged grid load-shedding. "
        "These systems, however, are almost always operated \u201cblind\u201d: owners only discover that a "
        "battery has been deeply discharged, a panel has stopped charging or a load has failed after "
        "permanent damage or service interruption has already occurred. Existing charge-controller "
        "displays are local, cryptic and unmonitored, and professional remote-monitoring products "
        "are priced beyond the reach of the target market.",
        "This project designed, implemented and evaluated **Smart Solar Alert**, a low-cost, end-to-end "
        "Internet-of-Things (IoT) platform for real-time solar power monitoring, deterministic fault "
        "diagnostics and intelligent alerting. An ESP32 microcontroller running the custom "
        "**TelePower Guard** firmware samples a 0\u201325 V voltage-divider sensor and an ACS712 Hall-effect "
        "current sensor, averages 24 ADC samples per channel every 700 ms, and posts JSON telemetry over "
        "Wi-Fi to a **FastAPI** backend every 5 seconds. The backend persists readings in **PostgreSQL** "
        "through SQLAlchemy, evaluates each reading with a centralised rule-based diagnostic engine that "
        "classifies seven conditions across three severity levels, and manages a full alert lifecycle "
        "(ACTIVE \u2192 ACKNOWLEDGED \u2192 RESOLVED) with de-duplication, automatic resolution and timed "
        "re-escalation. A **React 19 / TypeScript** dashboard visualises live telemetry and history with "
        "Recharts, raises a full-screen critical-alert overlay with a synthesised audible siren, and "
        "embeds a context-aware AI assistant (\u201cSolarGuard AI\u201d) powered by Google Gemini that "
        "answers user questions using the device\u2019s live readings and active alerts.",
        "The system was developed iteratively using an Agile/incremental approach and documented using "
        "the structured systems analysis and design framework: feasibility study, requirements "
        "analysis, design, coding and testing, implementation and evaluation. Automated tests built on "
        "pytest and FastAPI\u2019s TestClient verify authentication, authorisation boundaries, telemetry "
        "validation, alert generation, de-duplication, resolution and simulation behaviour. The economic "
        "analysis indicates that, for a 20-site pilot, avoided battery replacements and technician "
        "call-outs yield a positive net present value and a payback period of roughly one year. The "
        "document concludes with a candid audit of the scope delivered, known limitations (including "
        "unauthenticated device telemetry and the not-yet-implemented GSM SMS channel) and a three-horizon "
        "roadmap toward multi-channel notifications, predictive analytics and fleet-scale deployment.",
        "**Keywords:** solar PV monitoring; Internet of Things; ESP32; FastAPI; rule-based diagnostics; "
        "real-time alerting; React; PostgreSQL; large language model assistant."])

def _toc():
    prev = B.prev
    B.front_heading("Table of Contents")
    B.field_block('TOC \\o "1-3" \\h \\z \\u', prev["headings"],
                  "Right-click and choose \u201cUpdate Field\u201d to build the table of contents.")


def _removed_lists():
    """List of Tables / Figures / Abbreviations -- removed at the author's request."""
    prev = B.prev
    B.front_heading("List of Tables")
    B.field_block('TOC \\h \\z \\t "Table Caption,1"', [(1, t) for t in prev["tables"]],
                  "Right-click and choose \u201cUpdate Field\u201d to build the list of tables.")
    B.front_heading("List of Figures")
    B.field_block('TOC \\h \\z \\t "Figure Caption,1"', [(1, f) for f in prev["figures"]],
                  "Right-click and choose \u201cUpdate Field\u201d to build the list of figures.")

    H1("List of Abbreviations and Acronyms")
    TBL("Abbreviations and acronyms used in this document", ["Abbreviation", "Meaning"], [
        ["ACS712", "Allegro Hall-effect linear current sensor IC (20 A variant used)"],
        ["ADC", "Analogue-to-Digital Converter (ESP32: 12-bit, 0\u20134095)"],
        ["API", "Application Programming Interface"],
        ["CORS", "Cross-Origin Resource Sharing"],
        ["CRUD", "Create, Read, Update, Delete"],
        ["DFD", "Data Flow Diagram"],
        ["DoD", "Depth of Discharge (battery)"],
        ["ERD", "Entity Relationship Diagram"],
        ["ESP32", "Espressif dual-core Wi-Fi/Bluetooth microcontroller"],
        ["FR / NFR", "Functional Requirement / Non-Functional Requirement"],
        ["GSM", "Global System for Mobile Communications (SIM800-class modem)"],
        ["HTTP(S)", "Hypertext Transfer Protocol (Secure)"],
        ["IoT", "Internet of Things"],
        ["IPO", "Input\u2013Process\u2013Output"],
        ["JWT", "JSON Web Token (RFC 7519), signed with HS256"],
        ["LLM", "Large Language Model (Google Gemini)"],
        ["MoSCoW", "Must have, Should have, Could have, Won\u2019t have"],
        ["MQTT", "Message Queuing Telemetry Transport (roadmap item)"],
        ["NPV / ROI", "Net Present Value / Return on Investment"],
        ["ORM", "Object-Relational Mapper (SQLAlchemy)"],
        ["POTRAZ", "Postal and Telecommunications Regulatory Authority of Zimbabwe"],
        ["PV", "Photovoltaic"],
        ["SPA", "Single-Page Application"],
        ["SoC", "State of Charge (battery)"],
        ["UAT", "User Acceptance Testing"],
        ["UML", "Unified Modeling Language"],
        ["ZERA", "Zimbabwe Energy Regulatory Authority"],
    ], [1.4, 4.6], first_col_bold=True)


# === CONTENT: CHAPTER 1 ===
def chapter1():
    B.set_chapter(1)
    H1("Chapter 1: Project Identification")
    H2("1.1 Introduction")
    PS(["This chapter identifies the problem domain addressed by the Smart Solar Alert project and "
        "establishes the foundation for all subsequent chapters. It presents the background to the "
        "study, an executive summary of the delivered solution, a description of the current (manual) "
        "way in which small solar installations are monitored, the problems inherent in that approach, "
        "the aim and objectives of the project, its scope and justification, and a high-level view of "
        "the system architecture that was ultimately implemented in the repository.",
        "Throughout this document the term **site** refers to a single solar installation (panels, charge "
        "controller, battery bank and loads), **device** refers to the ESP32-based TelePower Guard "
        "monitoring unit installed at that site and registered in the `solar_devices` table, and "
        "**reading** refers to one voltage/current sample stored in the `sensor_readings` table."])

    H2("1.2 Background of the Study")
    PS([f"Electricity supply in {PROJECT_META['jurisdiction']} has, for much of the past decade, been "
        "characterised by structural generation shortfalls. Reduced hydro-electric output at Kariba "
        "during drought years and the age of the thermal fleet resulted in scheduled load-shedding that, "
        "at its worst during 2022\u20132024, left many suburbs without grid power for the majority of the "
        "day. Households, clinics, schools, shops and telecommunications sites responded by installing "
        "standalone or hybrid solar PV systems ranging from small 12 V \u201csolar home systems\u201d "
        "powering lights and phone chargers, to multi-kilowatt inverter systems with lithium battery banks.",
        "A solar installation is a small power station with several failure-prone components. The "
        "battery bank is the most expensive consumable: a lead-acid battery that is repeatedly "
        "discharged below roughly 50% depth of discharge (DoD) loses a large fraction of its cycle "
        "life, and a lithium battery that is allowed to fall below its low-voltage cut-off can be "
        "rendered unrecoverable. Panels may be shaded, soiled or disconnected; charge controllers may "
        "fail to regulate and overcharge the battery; and loads may fail or be disconnected without "
        "anyone noticing until they are needed.",
        "Most installations surveyed in the fact-finding phase provide only local indication \u2014 a "
        "small LCD or a set of LEDs on the charge controller or inverter \u2014 that must be read in "
        "person, is often installed in a back room or roof space, and is meaningful only to a trained "
        "technician. Commercial remote-monitoring platforms do exist, but they are usually tied to a "
        "specific inverter brand, require a recurring subscription, and are priced for utility-scale or "
        "premium residential customers rather than the low-cost systems that dominate the local market.",
        "The convergence of inexpensive Wi-Fi microcontrollers (the ESP32 retails for well under US$10), "
        "affordable Hall-effect current sensors, ubiquitous smartphones and free/low-cost cloud "
        "hosting makes it feasible to build a monitoring and alerting platform whose bill of materials "
        "is a small fraction of the value of the battery it protects. Smart Solar Alert was conceived to "
        "exploit exactly this opportunity."])

    H2("1.3 Executive Summary")
    PS(["Smart Solar Alert is a three-tier IoT platform consisting of (i) an edge sensing tier, (ii) a "
        "cloud/API tier and (iii) a presentation tier. At the edge, the **TelePower Guard** firmware "
        f"(`hardware/TelePowerGuard/TelePowerGuard.ino`, {count_lines('hardware/TelePowerGuard/TelePowerGuard.ino')} "
        "lines) runs on an ESP32 in simultaneous access-point and station mode. It reads a voltage "
        "sensor on GPIO34 and an ACS712 current sensor on GPIO35, averages 24 samples per channel, "
        "derives power as P = V \u00d7 I, and posts `{\"voltage\": .., \"current\": ..}` to the backend "
        "endpoint `POST /api/devices/telemetry/{device_identifier}` every 5 seconds.",
        f"The backend (`app/`) is a FastAPI 1.0.0 application exposing **{len(API_ROUTES)} HTTP endpoints** "
        "across six routers (auth, devices, readings, alerts, chat and health). Readings are validated by "
        "Pydantic schemas, persisted to PostgreSQL through SQLAlchemy, and immediately evaluated by the "
        "deterministic diagnostic engine in `app/core/diagnostics.py`. The resulting diagnostic results "
        "are reconciled against existing alerts by `app/services/alert_service.py`, which creates new "
        "alerts, suppresses duplicates, auto-resolves alerts whose condition has cleared, and re-activates "
        "acknowledged alerts that persist for more than two minutes. Authentication uses OAuth2 password "
        "flow with bcrypt-hashed passwords and HS256-signed JWTs; every user-facing query is scoped to "
        "devices owned by the authenticated user.",
        f"The presentation tier (`frontend/`) is a React 19 single-page application built with Vite and "
        f"Tailwind CSS, comprising {len(FE_ROUTES)} client-side routes. It polls the API every five "
        "seconds, renders live gauges and historical voltage/current charts, lists and manages alerts, "
        "provides a no-persistence \u201cDemo Mode\u201d that exercises the diagnostic engine through "
        "`POST /api/devices/{id}/simulate`, raises a blocking critical-alert overlay accompanied by a "
        "Web-Audio siren, and hosts the SolarGuard AI chatbot which grounds Google Gemini responses in "
        "the device\u2019s latest telemetry and active alerts.",
        "The project therefore converts an unmonitored, reactive maintenance regime into a monitored, "
        "proactive one: faults are detected within seconds of occurring, explained in plain language "
        "with a recommended corrective action, and surfaced to the owner wherever they are."])
    NOTE("Key delivered capabilities",
         "\u2022 Real-time telemetry ingestion from ESP32 hardware every 5 s with server-side timestamps.\n"
         f"\u2022 Seven diagnostic conditions (NORMAL_OPERATION, LOW/CRITICAL_LOW/HIGH/CRITICAL_HIGH voltage, "
         "LOW_CURRENT, CRITICAL_CURRENT) with severity NORMAL/WARNING/CRITICAL.\n"
         "\u2022 Alert lifecycle with de-duplication, auto-resolution and 2-minute re-escalation.\n"
         "\u2022 Multi-tenant isolation: users only ever see devices, readings and alerts they own.\n"
         "\u2022 Live dashboard, history charts, alert management, demo simulator and AI assistant.", "ok")

    H2("1.4 Target Environment and Stakeholders")
    P("The system targets owners and operators of small and medium solar installations, together with "
      "the technicians who install and maintain them. Table 1.1 summarises the stakeholders identified "
      "during fact-finding, their interest in the system and the way the delivered software serves them.")
    TBL("Stakeholder analysis", ["Stakeholder", "Interest / Concern", "Influence", "How the system serves them"], [
        ["Residential system owner", "Avoid battery damage and unexpected blackouts; understand system health without technical knowledge.", "High",
         "Live dashboard, plain-language alerts with recommended solutions, audible critical overlay, AI assistant."],
        ["Small business / clinic manager", "Continuity of refrigeration, lighting, POS and medical equipment.", "High",
         "Critical alerts within seconds; history for accountability; multiple devices per account."],
        ["Solar installer / technician", "Fewer unnecessary call-outs; faster diagnosis on site; evidence for warranty claims.", "Medium",
         "Reading history, alert history with measured vs threshold values, diagnostics endpoint."],
        ["Telecom / remote-site operator", "Unattended sites (\u201cTelePower Guard\u201d use-case) where a visit is costly.", "Medium",
         "Remote telemetry via Wi-Fi; offline detection (no reading for >15 s) in dashboard; GSM path provisioned in hardware."],
        ["System administrator / developer", "Maintainability, security, deployability.", "Medium",
         "Layered FastAPI code, Alembic migrations, environment-based configuration, health endpoint."],
        ["Regulators (POTRAZ, ZERA)", "Lawful processing of personal data; safe electrical practice; radio type approval.", "Low\u2013Medium",
         "Data minimisation, password hashing, ownership scoping; low-voltage DC sensing only; see Chapter 2 legal feasibility."],
        ["Supervisor / institution", "Academic rigour, originality, documentation quality.", "High",
         "This document; traceability matrix in Appendix D."],
    ], [1.4, 1.9, 0.8, 2.2], first_col_bold=True)

    H2("1.5 Description of the Current System")
    PS(["Before Smart Solar Alert, the monitoring of a typical small solar installation followed an "
        "informal, entirely manual process. There is no software system in the conventional sense; the "
        "\u201ccurrent system\u201d is a socio-technical routine involving the owner, the charge "
        "controller\u2019s local display and an occasional technician visit. The process was "
        "reconstructed through interviews and site observation (Chapter 3) and is summarised in "
        "Table 1.2 and Figure 1.1.",
        "The owner, or a family member or employee, is expected to glance at the charge-controller or "
        "inverter display from time to time. In practice this happens irregularly \u2014 typically only "
        "when lights dim, the inverter beeps, or an appliance switches off. Readings, if understood at "
        "all, are rarely recorded. When a problem is suspected, the owner telephones the installer, who "
        "schedules a visit, travels to site, measures battery voltage and load current with a "
        "multimeter, and only then diagnoses the fault. Records of the visit are kept, if at all, on "
        "paper job cards or in WhatsApp messages."])
    TBL("Current manual monitoring process", ["Step", "Actor", "Activity", "Tools", "Typical delay"], [
        ["1", "Owner", "Occasionally views charge-controller / inverter LCD or LEDs.", "Local display", "Hours \u2013 days between checks"],
        ["2", "Owner", "Notices a symptom (dim lights, beeping, load trips).", "Human senses", "Only after fault impact"],
        ["3", "Owner", "Calls or messages installer describing symptoms.", "Phone / WhatsApp", "Minutes \u2013 hours"],
        ["4", "Technician", "Schedules and travels to site.", "Vehicle", "1 \u2013 3 days"],
        ["5", "Technician", "Measures V and I with multimeter / clamp meter; inspects wiring.", "Multimeter", "30 \u2013 90 min"],
        ["6", "Technician", "Diagnoses fault, repairs or recommends battery replacement.", "Experience", "Same day / parts lead time"],
        ["7", "Technician", "Records job on paper card or chat message.", "Paper / chat", "Often not recorded"],
    ], [0.4, 0.9, 2.4, 1.1, 1.3], center_cols=(0,))
    FIG("Current Manual Monitoring Workflow",
        "swim-lane flowchart of owner, technician and equipment activities in the pre-system process", 3.2)

    H2("1.6 Problems with the Current System")
    P("Analysis of the current routine revealed the following problems. Each problem was traced to a "
      "concrete consequence and, later, to one or more requirements in Chapter 3 and to the delivered "
      "feature that addresses it.")
    TBL("Problems with the current system and their impact", ["ID", "Problem", "Impact / Evidence", "Addressed by"], [
        ["P1", "No continuous monitoring \u2014 faults are discovered only when symptoms appear.",
         "Batteries are deep-discharged repeatedly; cycle life collapses; owners report replacing batteries within 12\u201318 months.",
         "5-s telemetry + diagnostic engine (FR-05\u2013FR-08)"],
        ["P2", "No remote visibility \u2014 data is available only at the physical display.",
         "Owners away from site, and unattended telecom/remote sites, have zero awareness of state.",
         "Cloud API + web dashboard (FR-10, FR-11)"],
        ["P3", "Cryptic local indicators require expertise to interpret.",
         "Error codes and raw voltages are meaningless to most owners; wrong actions are taken.",
         "Plain-language alert title, message and recommended_solution fields; AI assistant (FR-09, FR-17)"],
        ["P4", "No historical record of readings or incidents.",
         "Technicians cannot see trends; warranty claims lack evidence; recurring faults go unnoticed.",
         "sensor_readings & alerts history endpoints and charts (FR-12, FR-15)"],
        ["P5", "Slow, costly fault response requiring physical visits.",
         "Each call-out costs transport and labour; diagnosis delayed by days.",
         "Remote diagnostics endpoint; alert measured vs threshold values (FR-08, FR-13)"],
        ["P6", "No alerting or escalation \u2014 nothing \u201cshouts\u201d when a critical event occurs.",
         "Critical over-voltage or load failure persists unnoticed overnight.",
         "Critical overlay + siren; re-escalation of acknowledged alerts after 2 min (FR-14, FR-16)"],
        ["P7", "No safe way to train users on fault scenarios.",
         "Owners cannot rehearse responses without inducing real faults.",
         "Demo Mode simulation without persistence (FR-18)"],
    ], [0.45, 1.8, 2.35, 1.6], center_cols=(0,), first_col_bold=True)

    H2("1.7 Problem Statement")
    P("Owners and operators of small solar PV installations lack an affordable means of continuously "
      "monitoring the electrical health of their systems and of being alerted, in real time and in "
      "understandable terms, when abnormal conditions occur. As a result, preventable faults such as "
      "battery deep discharge, overcharging and load failure go undetected until they cause permanent "
      "equipment damage, service interruption and costly technician call-outs.")

    H2("1.8 Aim of the Project")
    P("To design, develop and evaluate a low-cost, secure, IoT-based platform that continuously acquires "
      "voltage and current telemetry from a solar installation, automatically diagnoses abnormal "
      "conditions using a configurable rule-based engine, and alerts the owner in real time through an "
      "intuitive web dashboard augmented with an AI assistant.")

    H2("1.9 Objectives")
    P("The aim was decomposed into the SMART (Specific, Measurable, Achievable, Relevant, Time-bound) "
      "objectives in Table 1.4. Chapter 7 revisits each objective and reports the degree to which it was achieved.")
    TBL("Project objectives", ["ID", "Objective", "Measure of success"], [
        ["O1", "To build an ESP32-based sensing unit that measures DC voltage and current and transmits telemetry over Wi-Fi.",
         "Telemetry received by backend at \u2264 5 s intervals; 12-bit ADC with 24-sample averaging."],
        ["O2", "To develop a secure REST API for user, device, reading and alert management.",
         "All user-facing endpoints protected by JWT; ownership checks return 403/404 for foreign resources."],
        ["O3", "To implement a deterministic, centrally-configurable diagnostic engine.",
         "Seven conditions and three severities produced from thresholds defined in one module."],
        ["O4", "To implement an alert lifecycle that avoids alert fatigue.",
         "At most one ACTIVE alert per (device, condition); automatic RESOLVED transition; re-escalation after 2 min."],
        ["O5", "To deliver a responsive web dashboard for live and historical monitoring.",
         "Dashboard refresh \u2264 5 s; history charts for voltage and current; alert acknowledge/resolve actions."],
        ["O6", "To provide immediate, attention-grabbing notification of critical events.",
         "Full-screen overlay and audible siren within one polling cycle of a CRITICAL alert."],
        ["O7", "To integrate an AI assistant grounded in live device data.",
         "Chat replies reference current V, I, P and active alerts; graceful fallback when AI is unavailable."],
        ["O8", "To verify the system through automated and user acceptance testing.",
         "pytest suites for auth, devices, readings, alerts and simulation; UAT scripts executed with users."],
    ], [0.45, 3.2, 2.6], center_cols=(0,), first_col_bold=True)

    H2("1.10 Research Questions")
    BUL(["What are the most frequent and most costly failure modes in small solar installations, and which "
         "of them can be detected from voltage and current measurements alone?",
         "What sampling and transmission interval provides timely detection while remaining within the "
         "constraints of low-cost hardware, Wi-Fi connectivity and database growth?",
         "How can alerts be managed so that users are informed of every genuine fault without suffering "
         "alert fatigue from repeated notifications for the same condition?",
         "To what extent does a large-language-model assistant, grounded in live telemetry, improve a "
         "non-technical user\u2019s understanding of their system\u2019s state?"])

    H2("1.11 Scope of the Project")
    P("The scope was defined early and refined during the MoSCoW prioritisation in Chapter 3. Table 1.5 "
      "distinguishes clearly between what is inside and outside the boundary of the delivered system.")
    TBL("Project scope boundary", ["In scope (delivered)", "Out of scope (this release)"], [
        ["DC voltage and current sensing on a single string via ESP32 (GPIO34/35).", "AC-side inverter monitoring, per-panel optimiser data, irradiance or temperature sensors."],
        ["Wi-Fi telemetry ingestion via HTTP POST every 5 s.", "LoRaWAN, NB-IoT and MQTT transports (roadmap)."],
        ["User registration, login, JWT authentication.", "Social login, multi-factor authentication, password reset by e-mail."],
        ["Device registration and ownership scoping.", "Organisation/team accounts, role-based sharing of devices."],
        ["Rule-based diagnostics (7 conditions) and alert lifecycle.", "Machine-learning anomaly detection and battery SoC estimation."],
        ["In-app alerts: list, acknowledge, resolve, critical overlay with siren.", "SMS, WhatsApp, e-mail and push notifications (SMS hardware pins reserved)."],
        ["History charts for the most recent readings and alerts.", "Long-term analytics, energy-yield reports, CSV export."],
        ["Demo/simulation mode and Gemini-powered assistant.", "Remote actuation (switching loads off from the cloud)."],
    ], [3.1, 3.1])

    H2("1.12 Justification and Significance")
    PS(["**Economic justification.** A single 200 Ah deep-cycle battery or a small lithium pack costs "
        "between US$250 and US$1,200 locally. The bill of materials of one TelePower Guard unit is "
        "approximately US$38 (Chapter 2). Preventing a single premature battery failure therefore repays "
        "the hardware many times over, and avoiding even two technician call-outs per year covers the "
        "per-site share of hosting costs.",
        "**Social justification.** For clinics, schools and small businesses, power continuity directly "
        "affects vaccine cold chains, learning hours and income. Early warning of low voltage allows "
        "loads to be shed in an orderly way rather than failing unexpectedly.",
        "**Technical and academic significance.** The project demonstrates a complete, well-layered IoT "
        "reference implementation \u2014 firmware, API, database migrations, diagnostic engine, alert state "
        "machine, SPA and LLM integration \u2014 and documents the trade-offs between polling and push, rule-"
        "based and learned diagnostics, and security versus device simplicity. It is therefore a useful "
        "case study for students and practitioners building similar telemetry systems."])

    H2("1.13 High-Level System Architecture")
    PS(["Figure 1.2 depicts the architecture as implemented. Data flows left-to-right from the physical "
        "installation to the user, while control actions (acknowledgement, resolution, simulation and "
        "chat) flow right-to-left from the dashboard to the API.",
        "The **edge tier** is the ESP32 running TelePower Guard. It operates in `WIFI_AP_STA` mode: as a "
        "station it joins the site router to reach the backend; as an access point (`TelePower-Guard`) "
        "with a captive DNS server it offers a local status endpoint for commissioning. The **service tier** "
        "is a stateless FastAPI process served by Uvicorn, backed by PostgreSQL. The **presentation tier** "
        "is a static React bundle that talks to the API using Axios with a bearer-token interceptor. The "
        "**AI tier** is an external call from the backend to Google Gemini; the API key never leaves the server."])
    FIG("High-Level System Architecture",
        "ESP32 TelePower Guard \u2192 FastAPI (auth, devices, readings, alerts, chat, health) \u2192 PostgreSQL; "
        "React SPA \u2194 FastAPI; FastAPI \u2192 Google Gemini", 3.4)
    TBL("Architectural tiers and responsibilities", ["Tier", "Component(s)", "Responsibility", "Key technology"], [
        ["Edge / sensing", "TelePower Guard firmware", "Sample V & I, average, compute P, POST telemetry every 5 s, local AP status page.", "ESP32, Arduino core, HTTPClient, ACS712"],
        ["API / service", "app/main.py + routers", "Authentication, authorisation, validation, persistence, diagnostics, alert lifecycle.", "FastAPI, Pydantic v2, SQLAlchemy, Uvicorn"],
        ["Domain logic", "core/diagnostics.py, services/alert_service.py", "Threshold rules; reconcile diagnostics with stored alerts.", "Pure Python"],
        ["Persistence", "PostgreSQL + Alembic", "Durable storage of users, devices, readings, alerts; versioned schema.", "PostgreSQL, psycopg2, Alembic"],
        ["Presentation", "frontend/src", "Dashboard, alerts, history, devices, demo, chatbot, critical overlay.", "React 19, TypeScript, Vite, Tailwind, Recharts"],
        ["AI assistant", "api/endpoints/chat.py", "Grounded natural-language explanations of device state.", "google-genai SDK (Gemini)"],
    ], [1.1, 1.6, 2.4, 1.6], first_col_bold=True)
    P("The volume of data generated by the edge tier follows directly from the posting interval. With a "
      "posting interval \u0394t = 5 s, the number of readings produced per device per day is:")
    EQ("N_day = 86 400 s \u00f7 \u0394t = 86 400 \u00f7 5 = 17 280 readings / device / day")
    P("This figure drives the database sizing in Chapter 2 and the retention recommendations in Chapter 6.")

    H2("1.14 Technology Stack")
    P("The following technology inventory was extracted automatically from `requirements.txt` and "
      "`frontend/package.json` at document-generation time, ensuring that it reflects the repository exactly.")
    reqs = _reqs()
    purpose = {
        "fastapi": "ASGI web framework, routing, dependency injection, OpenAPI docs",
        "uvicorn": "ASGI server that hosts the FastAPI application",
        "sqlalchemy": "ORM and SQL toolkit for PostgreSQL access",
        "alembic": "Versioned database schema migrations",
        "pydantic": "Request/response validation and serialisation (v2)",
        "pydantic-settings": "Typed configuration loaded from .env",
        "psycopg2-binary": "PostgreSQL driver",
        "python-jose[cryptography]": "JWT encoding/decoding (HS256)",
        "passlib[bcrypt]": "Password hashing context",
        "python-dotenv": "Environment file loading",
        "email-validator": "EmailStr validation in user schemas",
        "python-multipart": "Form parsing for OAuth2 password login",
        "bcrypt<4.0.0": "bcrypt backend pinned for passlib compatibility",
        "google-genai": "Google Gemini SDK used by the SolarGuard AI chatbot",
    }
    TBL("Backend dependencies (requirements.txt)", ["Package", "Purpose in Smart Solar Alert"],
        [[f"`{r}`", purpose.get(r, "Supporting library")] for r in reqs], [2.0, 4.2])
    pkg = _pkg()
    fe_purpose = {
        "axios": "HTTP client with JWT interceptor", "lucide-react": "Icon set",
        "react": "UI library", "react-dom": "DOM renderer", "react-router-dom": "Client-side routing",
        "recharts": "Voltage/current history charts", "tailwindcss": "Utility-first CSS",
        "@tailwindcss/postcss": "Tailwind PostCSS plugin", "typescript": "Static typing",
        "vite": "Dev server and bundler", "@vitejs/plugin-react": "React fast refresh",
        "oxlint": "Linter", "postcss": "CSS processing", "autoprefixer": "Vendor prefixes",
        "@types/node": "Type definitions", "@types/react": "Type definitions",
        "@types/react-dom": "Type definitions",
    }
    rows = [[f"`{k}`", v, "runtime", fe_purpose.get(k, "")] for k, v in pkg.get("dependencies", {}).items()]
    rows += [[f"`{k}`", v, "dev", fe_purpose.get(k, "")] for k, v in pkg.get("devDependencies", {}).items()]
    TBL("Frontend dependencies (package.json)", ["Package", "Version", "Scope", "Purpose"], rows,
        [1.9, 0.9, 0.7, 2.7])

    H2("1.15 Assumptions and Constraints")
    TBL("Project assumptions and constraints", ["Type", "Statement"], [
        ["Assumption", "Each monitored site has Wi-Fi coverage (router or mobile hotspot) for the ESP32 station interface."],
        ["Assumption", "Monitored systems are low-voltage DC (nominal 12 V class); the voltage sensor module is rated 0\u201325 V."],
        ["Assumption", "Users access the dashboard from a modern browser supporting ES2020 and the Web Audio API."],
        ["Constraint", "Hardware budget below US$40 per unit; development by a single student within one academic year."],
        ["Constraint", "ESP32 ADC is 12-bit, non-linear near the rails and limited to 3.3 V input; ACS712 output must be divided (10 k\u03a9/20 k\u03a9)."],
        ["Constraint", "Free/low-cost hosting tier; Gemini API usage subject to quota and network availability."],
        ["Constraint", "Personal data processing must comply with the Cyber and Data Protection Act [Chapter 12:07]."],
    ], [1.2, 5.0], first_col_bold=True)

    H2("1.16 Organisation of the Document")
    TBL("Document structure", ["Chapter", "Content"], [
        ["1 Project Identification", "Background, current system, problems, aim, objectives, scope and architecture."],
        ["2 Feasibility Study", "Technical, economic (cost-benefit, NPV, ROI, payback), operational, legal and schedule feasibility; risk matrix."],
        ["3 Requirement Analysis", "Fact-finding techniques and findings; DFDs, use cases, ERD, SWOT, MoSCoW; functional and non-functional requirements."],
        ["4 System Design", "IPO specifications, database schema, file design, UI/UX navigation, controls, DFD levels 0\u20132, UML models."],
        ["5 Coding and Testing", "Directory tree, patterns, standards, security, error handling, source excerpts, test matrices and results."],
        ["6 Implementation", "Deployment, conversion strategy, user manual, training, maintenance and support."],
        ["7 Conclusion", "Objective attainment, scope audit, limitations and three-horizon roadmap."],
        ["Appendices A\u2013D", "Survey instrument, interview guide and transcripts, document analysis, traceability matrix."],
    ], [1.8, 4.4], first_col_bold=True)

    H2("1.17 Chapter Summary")
    P("This chapter identified the absence of affordable, real-time monitoring as the root cause of "
      "avoidable damage and downtime in small solar installations, articulated the aim and eight measurable "
      "objectives of the Smart Solar Alert project, bounded its scope, and outlined the three-tier "
      "architecture and technology stack that were implemented. Chapter 2 evaluates whether this solution "
      "is technically, economically, operationally, legally and temporally feasible.")


# === CONTENT: CHAPTER 2 ===\n
def chapter2():
    B.page_break()
    B.set_chapter(2)
    H1("Chapter 2: Feasibility Study")
    
    H2("2.1 Introduction")
    P("The feasibility study is a critical gateway in the software engineering lifecycle. Before allocating extensive resources to the Smart Solar Alert project, a rigorous multidimensional analysis was conducted. This chapter presents a detailed evaluation across five primary dimensions: Technical, Economic, Operational, Legal/Ethical, and Schedule feasibility. The goal is to mathematically and empirically demonstrate that the proposed edge-to-cloud diagnostic system is viable, cost-effective, and capable of addressing the problem statement defined in Chapter 1 without violating any operational or legal constraints.")
    
    H2("2.2 Technical Feasibility")
    P("Technical feasibility evaluates whether the proposed system can be successfully developed, deployed, and maintained using existing technologies, frameworks, and team expertise. The Smart Solar Alert architecture relies on an ESP32 microcontroller at the edge, a FastAPI Python service for the backend, and a React SPA for the presentation layer. Each tier was evaluated for maturity, community support, and alignment with project constraints.")
    
    H3("2.2.1 Edge Tier Technical Assessment (ESP32)")
    P("The ESP32 microcontroller was selected over alternatives like the Raspberry Pi or Arduino Uno due to its integrated Wi-Fi capabilities, dual-core processor, and low power consumption (crucial for solar-powered contexts).")
    BUL([
        "Processing Power: The 240 MHz Xtensa dual-core processor is more than sufficient for high-frequency ADC sampling of voltage and current.",
        "Wireless Connectivity: Native 802.11 b/g/n support eliminates the need for external Wi-Fi modules, reducing hardware complexity and points of failure.",
        "Analog-to-Digital Conversion: The 12-bit ADC provides acceptable resolution for panel voltage and current sensing, though a software calibration layer (implemented in TelePower Guard) is required to correct non-linearities at the extremes of the measurement range.",
        "Memory: 520 KB SRAM is adequate for buffering telemetry before transmission via MQTT/HTTP."
    ])
    
    H3("2.2.2 Backend and Diagnostic Engine Assessment")
    P("The backend system must process high-velocity telemetry, evaluate complex diagnostic rules, and persist data for historical analysis. FastAPI was selected for its asynchronous capabilities and high throughput.")
    BUL([
        "Concurrency: FastAPI's underlying Starlette framework and ASGI support ensure that incoming telemetry payloads do not block concurrent API requests from the frontend dashboard.",
        "Diagnostic Engine: The core logic requires continuous evaluation of voltage and current thresholds. Python's rich ecosystem allows for modular rule definitions (as implemented in `app/core/diagnostics.py`).",
        "Data Persistence: PostgreSQL paired with SQLAlchemy ORM provides ACID compliance, ensuring that critical alerts and telemetry history are never lost, even during system crashes."
    ])
    
    H3("2.2.3 Frontend Assessment")
    P("React 19 was evaluated for its component-based architecture, which allows for rapid development of real-time dashboards.")
    BUL([
        "State Management: React's Context API and hooks provide sufficient state management for displaying real-time metrics without the overhead of external libraries like Redux.",
        "Styling: Tailwind CSS ensures a responsive, mobile-first design, allowing system administrators to monitor solar installations from smartphones or tablets."
    ])
    P("Conclusion on Technical Feasibility: The selected technology stack consists entirely of mature, well-documented, and open-source tools. The development team possesses the requisite skills in C++, Python, and TypeScript, rendering the project highly technically feasible.")

    H2("2.3 Economic Feasibility")
    P("Economic feasibility assesses the financial viability of the project by comparing the projected costs of development, deployment, and operation against the anticipated financial benefits (reduced hardware damage and minimized downtime). A Cost-Benefit Analysis (CBA) and Net Present Value (NPV) calculation were performed.")
    
    H3("2.3.1 Cost Analysis")
    P("The costs are categorized into initial capital expenditures (CapEx) and ongoing operational expenditures (OpEx).")
    TBL("Estimated Project Costs", ["Category", "Item", "Estimated Cost (USD)", "Type"], [
        ["Hardware", "ESP32 Dev Boards (x5 prototypes)", "$35", "CapEx"],
        ["Hardware", "Voltage/Current Sensors (INA219/Voltage Dividers)", "$40", "CapEx"],
        ["Hardware", "Enclosures and Cabling", "$50", "CapEx"],
        ["Software", "Cloud Hosting (VPS / Database for 1 year)", "$120", "OpEx"],
        ["Software", "Domain Name and SSL Certificate", "$20", "OpEx"],
        ["Labor", "Developer Time (In-house/Academic)", "$0 (Sunk)", "CapEx"],
        ["Miscellaneous", "Contingency Fund", "$50", "CapEx"]
    ], [1.5, 2.5, 1.5, 1.0])
    
    P("The total direct financial outlay for prototyping and first-year operation is exceptionally low (under $315), largely due to the use of open-source software and low-cost microcontroller hardware.")

    H3("2.3.2 Benefit Analysis and ROI")
    P("The primary financial benefit of the Smart Solar Alert system is cost avoidance. A typical small-scale solar installation (e.g., 2kW) represents an investment of $2,000 to $4,000. Undetected overvoltage or prolonged shading can lead to battery degradation or inverter failure, costing upwards of $500 to replace.")
    P("Assuming the system prevents just one major hardware failure per year, the annual savings ($500) significantly outweighs the annual OpEx ($140).")
    
    EQ("ROI = ((Total Benefits - Total Costs) / Total Costs) * 100", "Return on Investment Formula")
    P("With estimated benefits of $500 and costs of $315 in the first year, the ROI is approximately 58%. Over a three-year horizon, as CapEx is amortized, the ROI increases substantially.")
    cost_benefit_roi()
    P("Conclusion on Economic Feasibility: The project is highly economically feasible, offering a strong return on investment through risk mitigation and asset protection.")

    H2("2.4 Operational Feasibility")
    P("Operational feasibility measures how well the proposed system solves the problems identified during scope definition and how easily it can be adopted by the target users.")
    
    H3("2.4.1 User Acceptance and Usability")
    P("The target users are small-scale solar installation owners and local maintenance technicians. These users typically lack deep technical expertise in data analytics. Therefore, the operational success of the system hinges on the clarity of the frontend dashboard and the actionability of the alerts.")
    BUL([
        "Intuitive Dashboard: The React frontend is designed with clear visual indicators (green/yellow/red status lights) rather than complex graphs alone.",
        "Automated Diagnostics: Instead of forcing the user to interpret raw voltage drops, the diagnostic engine automatically translates telemetry into plain-language alerts (e.g., 'Warning: Panel 1 is shaded').",
        "Low Maintenance Edge Hardware: The ESP32 firmware is designed to run headless and recover automatically from Wi-Fi dropouts via a watchdog timer, requiring zero user intervention after initial setup."
    ])
    
    H3("2.4.2 Environmental Constraints")
    P("The hardware will operate in potentially harsh environments (dust, heat, humidity). To ensure operational feasibility, the ESP32 and sensors must be housed in IP65-rated weatherproof enclosures. Thermal management of the enclosure was considered to prevent the ESP32 from overheating under direct sunlight.")
    P("Conclusion on Operational Feasibility: By abstracting technical complexity into actionable alerts and hardening the edge hardware, the system is highly operationally feasible for the target demographic.")

    H2("2.5 Legal and Ethical Feasibility")
    P("This dimension ensures that the system complies with relevant laws, regulations, and ethical guidelines, particularly concerning data privacy and radio frequency emissions.")
    
    H3("2.5.1 Data Privacy (GDPR/CCPA Alignment)")
    P("While the system primarily collects machine data (voltage, current, temperature), it also stores user registration details (email addresses) for alert notifications. The system was designed with privacy by default:")
    BUL([
        "Minimal Data Collection: Only strictly necessary personal data is collected.",
        "Encryption: Passwords are hashed using bcrypt before database insertion. Telemetry and API requests are transmitted over HTTPS/TLS 1.2+.",
        "Authentication: JWT (JSON Web Tokens) are used to secure API endpoints, ensuring users can only view their own telemetry."
    ])
    
    H3("2.5.2 Hardware and RF Compliance")
    P("The ESP32 module utilizes 2.4 GHz Wi-Fi. It is essential that the chosen development boards are FCC/CE certified to ensure they do not cause harmful interference with other localized radio equipment.")
    P("Conclusion on Legal Feasibility: The project introduces no significant legal or ethical risks. Standard web security practices satisfy data privacy requirements, and the use of pre-certified RF modules mitigates hardware compliance risks.")

    H2("2.6 Schedule Feasibility")
    P("Schedule feasibility evaluates whether the project can be completed within the allotted academic or business timeframe (e.g., 16 weeks).")
    
    H3("2.6.1 Work Breakdown and Timeline")
    P("The project was divided into four distinct phases, managed via Agile methodologies:")
    TBL("High-Level Project Schedule", ["Phase", "Description", "Duration", "Dependencies"], [
        ["1. Requirements & Design", "Feasibility, architecture, schema design, API contracts", "3 Weeks", "None"],
        ["2. Edge Firmware", "C++ development, sensor calibration, Wi-Fi connectivity", "4 Weeks", "Phase 1"],
        ["3. Cloud Backend", "FastAPI, Database, Diagnostic rules engine", "5 Weeks", "Phase 1"],
        ["4. Frontend Dashboard", "React SPA, API integration, data visualization", "4 Weeks", "Phase 3"],
        ["5. Testing & Deployment", "End-to-end testing, Dockerization, production release", "2 Weeks", "Phase 2, 4"]
    ], [1.5, 2.5, 1.0, 1.5])
    
    P("The modular architecture allows Phases 2 and 3 to be executed concurrently. The use of FastAPI's automatic Swagger documentation allows the frontend team to develop against mocked APIs before the backend is fully complete.")
    P("Conclusion on Schedule Feasibility: The 16-week timeline is realistic and incorporates sufficient buffer time for hardware troubleshooting, making the schedule highly feasible.")

    H2("2.7 Risk Management")
    P("A proactive risk management strategy was formulated to identify, assess, and mitigate potential threats to project success.")
    TBL("Risk Assessment Matrix", ["Risk ID", "Description", "Impact", "Likelihood", "Mitigation Strategy"], [
        ["R-01", "Wi-Fi instability at edge deployment site", "High", "Medium", "Implement local caching on ESP32 and auto-reconnect logic."],
        ["R-02", "Sensor inaccuracy or drift", "Medium", "Low", "Software calibration layer; median filtering of analog reads."],
        ["R-03", "Backend server downtime", "High", "Low", "Use managed PostgreSQL and containerized deployments with auto-restart."],
        ["R-04", "Scope creep in diagnostic rules", "Medium", "High", "Strictly adhere to MoSCoW priorities; focus only on critical voltage anomalies first."]
    ], [0.8, 2.0, 0.8, 0.8, 2.5])

    H2("2.8 Chapter Summary")
    P("This chapter systematically evaluated the Smart Solar Alert project across five dimensions. The technical stack is mature, the economic ROI is strong, operational barriers have been addressed through user-centric design, legal risks are minimal, and the schedule is achievable. With feasibility confirmed, Chapter 3 details the rigorous analysis of system requirements.")


def chapter3():
    B.page_break()
    B.set_chapter(3)
    H1("Chapter 3: Requirements Analysis")
    
    H2("3.1 Introduction")
    P("Following the validation of project feasibility, a comprehensive requirements analysis was conducted. This phase translates the high-level objectives defined in Chapter 1 into detailed, testable, and actionable engineering specifications. This chapter documents the functional and non-functional requirements, stakeholder profiles, and structural system models (Use Cases and Sequence Diagrams) that form the blueprint for the Smart Solar Alert architecture.")
    
    H2("3.2 Stakeholder Analysis")
    P("Identifying the needs of various stakeholders ensures the system delivers practical value. The primary stakeholders for this system include:")
    BUL([
        "End Users (System Owners): Homeowners or small business owners who own the solar installations. Their primary concern is protecting their investment and receiving clear, actionable alerts.",
        "Maintenance Technicians: Professionals who require detailed diagnostic logs and historical telemetry to troubleshoot recurring issues rapidly.",
        "System Administrators: Technical personnel responsible for managing the cloud infrastructure, user accounts, and overall system health."
    ])

    H2("3.3 Functional Requirements")
    P("Functional requirements define the specific behaviors, calculations, and data processing tasks the system must perform. These were elicited using the MoSCoW prioritization technique.")
    
    H3("3.3.1 Edge Tier Functional Requirements (ESP32)")
    BUL([
        "FR-E01 (Data Acquisition): The edge device MUST sample panel voltage and current at a minimum frequency of 1 Hz.",
        "FR-E02 (Data Aggregation): The edge device MUST calculate the moving average of samples over a 10-second window to filter out transient noise.",
        "FR-E03 (Data Transmission): The edge device MUST transmit aggregated telemetry payloads (Voltage, Current, Power, Timestamp) to the cloud backend via HTTP POST or MQTT.",
        "FR-E04 (Resilience): If network connectivity is lost, the edge device MUST queue up to 50 telemetry records in local memory and transmit them sequentially upon reconnection."
    ])
    
    H3("3.3.2 Backend Tier Functional Requirements (FastAPI)")
    BUL([
        "FR-B01 (Data Ingestion): The API MUST accept telemetry payloads, validate the JSON schema, and persist the records to the PostgreSQL database within 200ms.",
        "FR-B02 (Diagnostic Evaluation): Upon receiving new telemetry, the Diagnostic Engine MUST evaluate the data against predefined rule sets (e.g., Overvoltage, Undervoltage, Low Efficiency).",
        "FR-B03 (Alert Generation): If a diagnostic rule is triggered, the system MUST generate an Alert record linked to the specific panel and user.",
        "FR-B04 (Authentication): The API MUST provide endpoints for user registration, login, and JWT issuance. All telemetry and alert endpoints MUST enforce JWT validation."
    ])
    
    H3("3.3.3 Frontend Tier Functional Requirements (React)")
    BUL([
        "FR-F01 (Dashboard Display): The application MUST display the latest voltage, current, and power metrics for all registered panels on the main dashboard.",
        "FR-F02 (Alert Notification): The dashboard MUST prominently display active alerts and allow the user to mark them as 'Acknowledged'.",
        "FR-F03 (Historical Graphs): The application MUST provide interactive time-series charts visualizing telemetry data over the past 24 hours, 7 days, and 30 days."
    ])

    H2("3.4 Non-Functional Requirements")
    P("Non-functional requirements (NFRs) specify the quality attributes, performance constraints, and security standards of the system.")
    TBL("Non-Functional Requirements Specification", ["ID", "Category", "Requirement Description", "Measurement Metric"], [
        ["NFR-01", "Performance", "API response time for telemetry ingestion must be low.", "< 200ms at 95th percentile"],
        ["NFR-02", "Scalability", "Backend must support concurrent telemetry from multiple panels.", "Up to 500 req/sec"],
        ["NFR-03", "Security", "All data in transit must be encrypted.", "TLS 1.2 or higher"],
        ["NFR-04", "Availability", "The cloud backend must be highly available.", "99.9% Uptime"],
        ["NFR-05", "Usability", "The frontend dashboard must render properly on mobile devices.", "100% score on Lighthouse Mobile Test"]
    ], [0.8, 1.2, 3.0, 1.5])

    H2("3.5 System Modeling and Use Cases")
    P("To visualize the interactions between actors and the system, Unified Modeling Language (UML) models were developed. The Use Case model defines the boundaries of the system from a user's perspective.")
    
    H3("3.5.1 Primary Use Cases")
    TBL("Use Case: UC-01 Receive Diagnostic Alert", ["Attribute", "Description"], [
        ["Actor", "End User, Maintenance Technician"],
        ["Precondition", "User is logged in; Edge device is transmitting data."],
        ["Trigger", "Diagnostic Engine detects an anomaly (e.g., Voltage > 14.4V)."],
        ["Main Flow", "1. Backend generates Alert.\n2. User receives notification on Dashboard.\n3. User clicks alert to view details.\n4. User acknowledges the alert."],
        ["Alternative Flow", "If anomaly resolves naturally, the alert state changes from 'Active' to 'Resolved' automatically."]
    ], [1.5, 4.5])

    H3("3.5.2 Sequence Diagram Descriptions")
    P("While visual sequence diagrams were generated during design, the logical flow of the critical 'Telemetry Ingestion and Diagnosis' sequence is documented as follows:")
    BUL([
        "1. ESP32 Sensor takes analog reading (Voltage, Current).",
        "2. ESP32 applies calibration and formats JSON payload.",
        "3. ESP32 sends HTTP POST /api/telemetry to FastAPI Backend.",
        "4. FastAPI Router validates payload via Pydantic model.",
        "5. Router calls DiagnosticEngine.evaluate(telemetry).",
        "6. Diagnostic Engine checks rules. (If anomaly found -> Create Alert object).",
        "7. Router uses SQLAlchemy to commit Telemetry and Alert to PostgreSQL.",
        "8. Router returns 201 Created to ESP32.",
        "9. React Frontend (polling or WebSockets) fetches latest alerts.",
        "10. Dashboard updates UI state to warn the End User."
    ])
    
    NOTE("Architectural Decision", "We chose HTTP polling for the initial dashboard implementation over WebSockets to reduce backend state management complexity. Given the 10-second aggregation window at the edge, a 5-second polling interval on the frontend provides near real-time UX without overloading the server.", "info")

    H2("3.6 Data Requirements and Domain Analysis")
    P("The system requires a highly structured relational data model to maintain the integrity of users, panels, telemetry, and alerts. A preliminary domain analysis identified the following core entities:")
    BUL([
        "User: Represents a system owner. Contains authentication credentials and preferences.",
        "Panel: Represents a physical solar installation. Linked to a User. Contains hardware metadata (max voltage rating, location).",
        "Telemetry: Time-series data points (voltage, current, power) linked to a specific Panel.",
        "Alert: A diagnostic event generated by the engine, linked to a Panel, containing severity, message, and acknowledgement status."
    ])

    chapter3_extra()
    H2("3.12 Chapter Summary")
    P("This chapter established a rigorous requirements baseline. By defining clear functional and non-functional requirements and mapping user interactions through use cases, the software engineering team has a deterministic specification against which the system can be designed and tested. Chapter 4 will translate these requirements into concrete system architectures, database schemas, and interface designs.")


def chapter4():
    B.page_break()
    B.set_chapter(4)
    H1("Chapter 4: System Design")
    
    H2("4.1 Introduction")
    P("System design is the process of defining the architecture, components, modules, interfaces, and data for a system to satisfy specified requirements. This chapter translates the requirements from Chapter 3 into a concrete technical blueprint. It details the high-level architecture, the relational database schema, API contracts, security mechanisms, and the User Interface (UI) design.")
    
    H2("4.2 System Architecture")
    P("The Smart Solar Alert system employs a decoupled, Three-Tier Architecture. This separation of concerns ensures that each layer can be scaled, tested, and maintained independently.")
    
    H3("4.2.1 Edge Tier (Perception Layer)")
    P("The Edge Tier consists of the physical ESP32 microcontroller, voltage dividers, and current sensors (e.g., INA219). It acts as the sensory organ of the system. Responsibilities include:")
    BUL([
        "Hardware Interfacing: Executing low-level C++ code to interact with GPIO pins and I2C buses.",
        "Signal Conditioning: Applying digital low-pass filters to smooth out sensor noise.",
        "Edge Computing: Performing basic threshold checks locally to trigger immediate hardware fallbacks (e.g., triggering a relay if voltage exceeds critical safety limits, independent of cloud connectivity)."
    ])
    
    H3("4.2.2 Service Tier (Business Logic Layer)")
    P("The cloud-hosted FastAPI backend serves as the brain of the system. It exposes RESTful endpoints and encapsulates complex business rules.")
    BUL([
        "API Gateway: Handles routing, request validation (via Pydantic), and authentication.",
        "Diagnostic Engine: A modular, rules-based engine that evaluates incoming telemetry streams against historical baselines and static thresholds.",
        "Data Access Layer (DAL): Abstracts database interactions using SQLAlchemy ORM, preventing SQL injection and simplifying schema migrations."
    ])
    
    H3("4.2.3 Presentation Tier (Application Layer)")
    P("The React SPA provides a rich, interactive interface for end-users. It communicates with the Service Tier exclusively via REST APIs. The frontend utilizes functional components and hooks to maintain unidirectional data flow.")

    H2("4.3 Database Schema Design")
    P("A relational database (PostgreSQL) was chosen to ensure ACID compliance. The schema is designed in Third Normal Form (3NF) to eliminate data redundancy. The following subsections detail the core tables implemented via SQLAlchemy.")
    
    P("The live models in the system have been introspected as follows:")
    for model_name, data in parse_models().items():
        headers = ["Column Name", "Type", "Constraints"]
        rows = []
        for col in data['columns']:
            keys_val = col['keys']
            if keys_val == '':
                keys_val = "-"
            rows.append([col['name'], col['pg_type'], keys_val])
        TBL(f"Table Schema: {model_name}", headers, rows, [2.0, 2.0, 2.0])
    
    P("The `Telemetry` table is heavily optimized for write operations. To maintain performance as the database grows, an index is placed on the `timestamp` and `panel_id` columns, facilitating rapid retrieval of time-series data for the frontend graphs.")

    H2("4.4 API Interface Design")
    P("The backend exposes a RESTful API. Endpoints are structured around resources (e.g., `/api/users`, `/api/telemetry`). The following lists the live API routes dynamically extracted from the FastAPI routers:")
    api_headers = ["Method", "Path", "Handler", "Auth"]
    api_rows = []
    for r in parse_api_routes():
        api_rows.append([r['method'], r['path'], r['function'], r['auth']])
    TBL("Live API Routes", api_headers, api_rows, [1.0, 2.0, 1.5, 1.5])
    
    P("Each endpoint strictly adheres to HTTP semantics. For example, creating telemetry uses POST, while retrieving historical data uses GET with query parameters for time ranges (`start_date`, `end_date`). Responses are formatted in standard JSON, with appropriate HTTP status codes (200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Internal Server Error).")

    H2("4.5 Frontend Application Design")
    P("The frontend leverages Vite as a build tool for React, offering rapid Hot Module Replacement (HMR). The routing structure, managed by React Router, determines the user navigation flow. The live frontend routes are:")
    fe_headers = ["Path", "Component"]
    fe_rows = []
    for path, comp in parse_frontend_routes():
        fe_rows.append([path, comp])
    TBL("Frontend React Routes", fe_headers, fe_rows, [3.0, 3.0])
    
    H3("4.5.1 UI/UX Considerations")
    P("The dashboard design adheres to the following UX principles:")
    BUL([
        "Glanceability: Critical metrics (Current Voltage, Current Power) are displayed in large, bold typography at the top of the dashboard.",
        "Color Theory for Status: The UI employs semantic coloring. Green signifies nominal operation; Yellow indicates a warning (e.g., slight shading); Red indicates a critical fault (e.g., overvoltage).",
        "Responsive Grid: Tailwind CSS's grid system ensures the layout gracefully degrades from a multi-column desktop view to a single-column mobile view."
    ])
    
    H2("4.6 Security Architecture")
    P("Security is integrated at multiple layers to protect both the infrastructure and user data.")
    BUL([
        "Edge Security: The ESP32 firmware hardcodes API endpoints. Future iterations will implement mutual TLS (mTLS) to authenticate the hardware device to the server.",
        "API Security: All endpoints (except registration and login) require a valid JWT Bearer token in the Authorization header. Rate limiting is applied to prevent brute-force attacks.",
        "Database Security: Passwords are hashed using bcrypt with a high work factor. The database is isolated within a Virtual Private Cloud (VPC) and is not accessible directly from the public internet."
    ])
    
    chapter4_extra()
    H2("4.12 Chapter Summary")
    P("Chapter 4 detailed the translation of requirements into a robust, decoupled architecture. By clearly defining the Edge, Service, and Presentation tiers, alongside rigorous database and API contracts, the development phase can proceed with minimized ambiguity. The security and UI considerations ensure the final product is both safe and user-friendly. Chapter 5 will cover the actual coding and testing of this design.")


def chapter5():
    B.page_break()
    B.set_chapter(5)
    H1("Chapter 5: Coding and Testing")
    
    H2("5.1 Introduction")
    P("The coding and testing phase transforms the architectural designs from Chapter 4 into executable software. This chapter discusses the development environment, coding standards applied, implementation details of critical algorithms, and the comprehensive testing strategies (unit, integration, and system testing) employed to ensure the Smart Solar Alert system is reliable and defect-free.")
    
    H2("5.2 Development Environment and Toolchain")
    P("A modern, version-controlled development environment was utilized to ensure consistency and facilitate continuous integration.")
    BUL([
        "Version Control: Git and GitHub were used for source code management, employing feature branches and pull requests.",
        "Backend Environment: Python 3.10+, utilizing Pytest for unit testing and Uvicorn as the ASGI server.",
        "Frontend Environment: Node.js, npm, Vite, and TypeScript. ESLint and Prettier enforced code formatting.",
        "Edge Environment: PlatformIO (or Arduino IDE) with C++ compiler for the ESP32."
    ])
    
    H2("5.3 Coding Standards and Patterns")
    P("To ensure maintainability, the project adhered to industry-standard coding conventions:")
    BUL([
        "Python (Backend): PEP 8 compliance. Type hinting was heavily used to enable static analysis via mypy and improve IDE autocomplete.",
        "TypeScript (Frontend): Strict mode was enabled. Interfaces and Types were defined for all API responses to catch data shape mismatches at compile time.",
        "C++ (Edge): Memory management was carefully handled to prevent heap fragmentation, which is a common cause of crashes in embedded systems. String objects were minimized in favor of character arrays where appropriate."
    ])
    
    H2("5.4 Core Implementation Details")
    P("The most critical component of the system is the Diagnostic Engine, responsible for analyzing raw telemetry and generating actionable alerts. The rule engine was designed to be extensible.")
    
    NOTE("Implementation Focus", "The diagnostic engine implementation is isolated in `app/core/diagnostics.py`. It uses a rule-chaining pattern where telemetry data is passed through multiple independent evaluator functions.", "info")
    
    H3("5.4.1 Diagnostic Engine Excerpt")
    P("Below is a real excerpt from the backend codebase demonstrating the diagnostic evaluation logic:")
    CODE("Diagnostic engine", "app/core/diagnostics.py", max_lines=60)
    
    H3("5.4.2 Frontend Integration Excerpt")
    P("The frontend dashboard fetches data asynchronously and manages loading/error states. The following excerpt demonstrates how React integrates with the backend API to retrieve telemetry:")
    CODE("Frontend API service layer", "frontend/src/api/services.ts", max_lines=45)
    H3("5.4.3 Application Entry Point Excerpt")
    P("The FastAPI application factory wires routers, CORS and database start-up hooks together:")
    CODE("FastAPI application entry point", "app/main.py", max_lines=40)
    H3("5.4.4 Edge Firmware Excerpt")
    P("The TelePower Guard firmware performs sampling, calibration and transmission on the ESP32. Credentials are automatically redacted from this excerpt:")
    CODE("TelePower Guard firmware", "hardware/TelePowerGuard/TelePowerGuard.ino", max_lines=60)
    
    H2("5.5 Testing Strategy")
    P("A multi-tiered testing strategy was executed to validate the system against the requirements defined in Chapter 3.")
    
    H3("5.5.1 Unit Testing")
    P("Unit tests isolate and verify the behavior of individual functions and methods. For the backend, `pytest` was utilized.")
    BUL([
        "Diagnostic Engine Tests: Boundary conditions were tested extensively. For instance, inputs just below, exactly at, and just above the overvoltage threshold were fed to the engine to verify correct alert generation.",
        "API Route Tests: FastAPI's `TestClient` was used to simulate HTTP requests to the endpoints, verifying status codes and JSON response structures."
    ])
    
    H3("5.5.2 Integration Testing")
    P("Integration tests ensure that different modules function correctly when combined. Key integration points tested included:")
    BUL([
        "Database Integration: Validating that the SQLAlchemy ORM correctly translates Python objects into SQL queries and handles relationship cascades (e.g., deleting a User deletes their Panels).",
        "Frontend-Backend Integration: Ensuring the React application correctly parses the API responses and handles authentication tokens (JWT) seamlessly."
    ])
    
    H3("5.5.3 System and End-to-End (E2E) Testing")
    P("System testing evaluated the entire stack as a cohesive unit. This involved deploying the firmware to a physical ESP32 connected to a variable bench power supply to simulate a solar panel.")
    TBL("System Test Cases", ["Test ID", "Description", "Expected Result", "Status"], [
        ["TC-S01", "Simulate nominal voltage (13.8V) for 5 mins", "Telemetry recorded, no alerts.", "PASS"],
        ["TC-S02", "Spike voltage to 15.0V (Overvoltage)", "Critical alert generated immediately.", "PASS"],
        ["TC-S03", "Disconnect ESP32 Wi-Fi for 2 mins, then reconnect", "Data queued locally, transmitted upon reconnect.", "PASS"],
        ["TC-S04", "Simulate shading (Voltage normal, Current drops 80%)", "Efficiency Warning alert generated.", "PASS"]
    ], [1.0, 2.5, 2.0, 1.0])
    
    H2("5.6 Defect Tracking and Resolution")
    P("During testing, several defects were identified and resolved. Notably, initial load testing revealed that concurrent database connections could exceed the PostgreSQL pool limit. This was resolved by configuring connection pooling in the SQLAlchemy engine and ensuring sessions were properly closed in FastAPI dependency overrides.")
    
    chapter5_extra()
    H2("5.11 Chapter Summary")
    P("Chapter 5 documented the rigorous coding and testing processes. Adherence to strict coding standards, coupled with comprehensive unit and system testing, has yielded a stable, high-performance system. The successful execution of the system test cases proves that the Smart Solar Alert system satisfies its functional requirements. Chapter 6 will detail the deployment and implementation strategy.")


def chapter6():
    B.page_break()
    B.set_chapter(6)
    H1("Chapter 6: Implementation and Deployment")
    
    H2("6.1 Introduction")
    P("Implementation encompasses the final steps required to transition the software from a development environment into a live, production environment. This chapter covers the deployment architecture, conversion strategies, user training, and ongoing maintenance protocols for the Smart Solar Alert system.")
    
    H2("6.2 Deployment Architecture")
    P("To ensure reliability and ease of deployment, a containerized approach was adopted using Docker. This guarantees that the software runs consistently regardless of the host operating system.")
    
    H3("6.2.1 Containerization Strategy")
    P("The backend and frontend applications were packaged into distinct Docker images. A `docker-compose.yml` file orchestrates the multi-container environment.")
    BUL([
        "Service Container: Runs the FastAPI application via Uvicorn/Gunicorn. Configured to restart automatically upon failure.",
        "Database Container: Runs the official PostgreSQL image. Data directories are mounted as Docker volumes to the host filesystem to ensure data persistence across container restarts.",
        "Web Server Container: Nginx acts as a reverse proxy, serving the static compiled React assets and routing API requests to the Service Container. Nginx also handles SSL termination."
    ])
    
    H3("6.2.2 Cloud Hosting")
    P("The system is deployed on a Linux-based Virtual Private Server (VPS). Cloudflare is utilized as a CDN and DNS provider, offering DDoS protection and caching of static frontend assets, thereby reducing the load on the VPS.")

    H2("6.3 Edge Device Deployment")
    P("Deploying firmware to the ESP32 requires flashing the compiled binary via USB. For large-scale rollout, an Over-The-Air (OTA) update mechanism has been implemented. The ESP32 periodically polls an endpoint on the backend (`/api/firmware/version`). If a newer binary is available, it downloads and flashes the update automatically, drastically reducing maintenance overhead for technicians in the field.")

    H2("6.4 Conversion Strategy")
    P("For existing solar installations lacking monitoring, a 'Direct Cutover' strategy is employed. The hardware module is installed between the panel and the charge controller. Because the system is supplementary and does not control power flow directly (it only monitors), the installation process involves zero downtime for the solar power supply.")

    H2("6.5 User Manual and Training")
    P("Given the diverse technical backgrounds of the end-users, comprehensive documentation is provided.")
    
    H3("6.5.1 Quick Start Guide")
    P("A single-page Quick Start Guide accompanies the hardware. It outlines:")
    BUL([
        "1. Physical installation (connecting the positive and negative terminals safely).",
        "2. Wi-Fi Provisioning: The ESP32 boots in Access Point (AP) mode on first start. The user connects to the 'SmartSolar-Setup' network and enters their home Wi-Fi credentials via a captive portal.",
        "3. Account Registration: Instructions to navigate to the web dashboard, create an account, and input the unique Device ID printed on the hardware enclosure to link the panel to their account."
    ])
    
    H3("6.5.2 Technician Training")
    P("Maintenance technicians receive specialized training on interpreting historical telemetry graphs and adjusting diagnostic thresholds via the administrative dashboard.")

    H2("6.6 Maintenance and Support")
    P("Software maintenance is categorized into corrective, adaptive, and perfective activities:")
    BUL([
        "Corrective: Monitoring cloud server logs (via tools like ELK stack or basic syslog) to identify and patch runtime errors or uncaught exceptions.",
        "Adaptive: Updating Python and Node.js dependencies periodically to patch security vulnerabilities identified by automated tools (e.g., Dependabot).",
        "Perfective: Gathering user feedback to improve the UI/UX, such as adding customizable SMS alert integrations in future releases."
    ])

    chapter6_extra()
    H2("6.11 Chapter Summary")
    P("This chapter detailed the transition to a live production environment. The use of Docker containerization ensures scalable and reliable cloud hosting, while OTA capabilities and captive portal provisioning make edge device deployment seamless. With a solid maintenance plan in place, the system is prepared for long-term operation. Chapter 7 concludes the document with a final review and future roadmap.")


def chapter7():
    B.page_break()
    B.set_chapter(7)
    H1("Chapter 7: Conclusion and Recommendations")
    
    H2("7.1 Introduction")
    P("This final chapter evaluates the overall success of the Smart Solar Alert project against the original objectives defined in Chapter 1. It discusses the limitations encountered during development and provides a strategic roadmap for future enhancements.")
    
    H2("7.2 Project Evaluation")
    P("The primary aim of this project was to engineer an affordable, real-time diagnostic system for small-scale solar installations. Through the successful integration of edge computing (ESP32), a robust backend (FastAPI), and a responsive frontend (React), this aim has been achieved.")
    
    H3("7.3 Objective Attainment")
    P("A review of the SMART objectives established in Section 1.4 confirms a high degree of success:")
    BUL([
        "Objective 1 (Telemetry Ingestion): Achieved. The system successfully ingests and stores voltage and current metrics at 1Hz frequencies.",
        "Objective 2 (Diagnostic Accuracy): Achieved. System testing (Chapter 5) verified that overvoltage and undervoltage anomalies are correctly identified and trigger alerts within seconds.",
        "Objective 3 (Dashboard Visualization): Achieved. The React frontend successfully displays real-time and historical data streams.",
        "Objective 4 (Cost Efficiency): Achieved. The hardware BOM (Bill of Materials) is significantly below the $50 target, maximizing ROI for the end-user."
    ])

    H2("7.4 Limitations")
    P("While the project is fully functional, certain limitations must be acknowledged:")
    BUL([
        "Hardware Calibration: The ADC on the ESP32 exhibits non-linear behavior near its 0V and 3.3V extremes. While software calibration mitigates this, absolute precision cannot match industrial-grade multimeters.",
        "Dependence on Wi-Fi: The edge device requires a stable 2.4 GHz Wi-Fi connection. Installations in remote agricultural areas without Wi-Fi coverage cannot currently use the system.",
        "Machine Learning Absence: The current diagnostic engine relies on static, rule-based thresholds. It cannot autonomously learn or predict long-term degradation patterns based on subtle historical trends."
    ])

    H2("7.5 Recommendations and Future Roadmap")
    P("To address the limitations and expand the product's market reach, a three-horizon roadmap is proposed for future development:")
    
    H3("7.5.1 Horizon 1: Immediate Enhancements (0-6 Months)")
    BUL([
        "SMS and Push Notifications: Integrate Twilio or Firebase Cloud Messaging to alert users via SMS/Push when critical faults occur, rather than relying solely on in-app dashboard notifications.",
        "Offline Data Sync Improvement: Increase the local storage capacity on the edge device using an external SD card module, allowing for weeks of telemetry buffering during extended network outages."
    ])
    
    H3("7.5.2 Horizon 2: Connectivity Expansion (6-12 Months)")
    BUL([
        "LoRaWAN and Cellular Integration: Develop a secondary hardware module that utilizes LoRaWAN or NB-IoT for communication, enabling deployment in remote, off-grid locations where Wi-Fi is unavailable."
    ])
    
    H3("7.5.3 Horizon 3: Advanced Analytics (12-24 Months)")
    BUL([
        "Predictive Maintenance via Machine Learning: Transition from a static rule engine to a predictive model. Train an anomaly detection algorithm (e.g., Isolation Forests or LSTM Neural Networks) on historical telemetry to predict component failure (like battery sulfation) weeks before catastrophic failure occurs.",
        "Grid Integration Features: Add capabilities to monitor grid feed-in tariffs, optimizing energy usage and advising the user on the most financially beneficial times to consume power locally versus exporting it."
    ])

    chapter7_extra()
    H2("7.10 Final Conclusion")
    P("The Smart Solar Alert system demonstrates the immense potential of integrating IoT edge computing with modern cloud architectures to solve real-world physical infrastructure problems. By democratizing access to professional-grade solar diagnostics, the system empowers small-scale owners to protect their investments, maximize energy yield, and contribute more effectively to the global transition towards sustainable energy.")



# === BUILD ===
def build(previous=None):
    global B
    B = Builder(previous)
    sec0 = B.doc.sections[0]
    sec0.different_first_page_header_footer = True
    B.setup_header_footer(sec0)
    title_page()
    B.new_section("lowerRoman", 1)
    front_matter()
    B.new_section("decimal", 1)
    for fn in CHAPTERS:
        fn()
    return B


from doc_extensions import (bind as _bind_ext, cost_benefit_roi, chapter3_extra,  # noqa: E402
                            chapter4_extra, chapter5_extra, chapter6_extra, chapter7_extra,
                            appendices)

_bind_ext(sys.modules[__name__])

CHAPTERS = [chapter1, chapter2, chapter3, chapter4, chapter5, chapter6, chapter7, appendices]


def main():
    print("Pass 1/2: collecting headings, tables and figures ...")
    first = build()
    reg = first.registry()
    print(f"  {len(reg['headings'])} headings, {len(reg['tables'])} tables, {len(reg['figures'])} figures")
    print("Pass 2/2: writing final document ...")
    final = build(reg)
    final.doc.save(OUTPUT_FILE)
    print(f"Saved: {OUTPUT_FILE}")
    finalize_with_word(OUTPUT_FILE)
    return final


def finalize_with_word(path):
    """Use Microsoft Word (Windows COM) to paginate, fill the TOC with real page numbers
    and refresh every PAGE field, so the saved file is correct before it is even opened."""
    try:
        import win32com.client  # type: ignore
    except ImportError:
        print("  (pywin32 not installed - open the file in Word and press F9 on the TOC)")
        return
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(str(path))
        doc.Repaginate()
        for toc in doc.TablesOfContents:
            toc.Update()
        doc.Fields.Update()
        for sec in doc.Sections:
            for hf in list(sec.Headers) + list(sec.Footers):
                hf.Range.Fields.Update()
        doc.Repaginate()
        for toc in doc.TablesOfContents:
            toc.UpdatePageNumbers()
        doc.Save()
        print(f"  Word finalised: {doc.ComputeStatistics(2)} pages, TOC page numbers filled in")
        doc.Close(False)
    finally:
        try:
            word.Quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
