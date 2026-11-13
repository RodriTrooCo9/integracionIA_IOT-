#!/usr/bin/env python3
"""
Ensamblador profesional de tesis en formato APA 7.ª edición (.docx).

Lee los archivos fuente auditados en /home/rodrigo/Desktop/IOTtesis/tesis/:
  - cap1_introduccion.md
  - cap2_marco_teorico.md
  - cap3_diseno_metodologico.md
  - referencias_apa7.md
  - anexos_instrumentos.md

Genera /home/rodrigo/Desktop/IOTtesis/tesis/Tesis_Capitulos_I_II_III_APA7.docx
mediante generación directa de OOXML (zipfile + lxml + Pillow) con:
  - Página Carta (Letter 8.5 x 11 in) y márgenes de 2.54 cm (1 in).
  - Tipografía Times New Roman 12 pt (10 pt en tablas/notas), alineación izquierda.
  - Portada institucional sin número de página (w:titlePg).
  - Índices (General, Tablas y Figuras) con campos Word y números de página reales
    verificados en doble pasada mediante LibreOffice + pdftotext.
  - Jerarquía APA 7 de títulos (Niveles 1–5) con inicio de capítulo en página nueva.
  - Tablas APA 7 (solo líneas horizontales, w:tblHeader, w:cantSplit).
  - Figuras incrustadas con proporción exacta en EMU e imágenes reales en word/media/.
  - Conversión integral de LaTeX ($...$ / $$...$$) a OMML y Unicode/sub-superíndices.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from lxml import etree
from PIL import Image

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
TESIS_DIR = Path("/home/rodrigo/Desktop/IOTtesis/tesis")
OUTPUT_DOCX = TESIS_DIR / "Tesis_Capitulos_I_II_III_APA7.docx"

SOURCE_FILES = [
    ("CAP1", TESIS_DIR / "cap1_introduccion.md"),
    ("CAP2", TESIS_DIR / "cap2_marco_teorico.md"),
    ("CAP3", TESIS_DIR / "cap3_diseno_metodologico.md"),
    ("REF", TESIS_DIR / "referencias_apa7.md"),
    ("ANEX", TESIS_DIR / "anexos_instrumentos.md"),
]

# ---------------------------------------------------------------------------
# Constantes OOXML y geometría APA 7
# ---------------------------------------------------------------------------
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"

NSMAP_DOC = {
    "w": W_NS,
    "r": R_NS,
    "m": M_NS,
    "wp": WP_NS,
    "a": A_NS,
    "pic": PIC_NS,
}

PAGE_W_DXA = 12240       # 8.5 in (21.59 cm)
PAGE_H_DXA = 15840       # 11.0 in (27.94 cm)
MARGIN_DXA = 1440        # 1.0 in (2.54 cm)
CONTENT_W_DXA = 9360     # 6.5 in (16.51 cm)
INDENT_DXA = 720         # 0.5 in (1.27 cm)
EMU_PER_INCH = 914400

FONT_MAIN = "Times New Roman"
FONT_MONO = "Courier New"


def wtag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def mtag(name: str) -> str:
    return f"{{{M_NS}}}{name}"


def rtag(name: str) -> str:
    return f"{{{R_NS}}}{name}"


def wptag(name: str) -> str:
    return f"{{{WP_NS}}}{name}"


def atag(name: str) -> str:
    return f"{{{A_NS}}}{name}"


def pictag(name: str) -> str:
    return f"{{{PIC_NS}}}{name}"


def make_el(tag: str, attrib: Optional[dict] = None, text: Optional[str] = None, nsmap: Optional[dict] = None) -> etree._Element:
    el = etree.Element(tag, attrib or {}, nsmap=nsmap)
    if text is not None:
        el.text = text
    return el


def add_el(parent: etree._Element, tag: str, attrib: Optional[dict] = None, text: Optional[str] = None) -> etree._Element:
    el = etree.SubElement(parent, tag, attrib or {})
    if text is not None:
        el.text = text
    return el


# ---------------------------------------------------------------------------
# Conversión de LaTeX a Unicode / Runs Word / OMML
# ---------------------------------------------------------------------------
LATEX_SYMBOLS = {
    "\\_": "_",
    r"\Delta": "Δ",
    r"\Omega": "Ω",
    r"\alpha": "α",
    r"\approx": "≈",
    r"\cap": "∩",
    r"\cdot": "·",
    r"\circ": "°",
    r"\cup": "∪",
    r"\gamma": "γ",
    r"\ge": "≥",
    r"\in": "∈",
    r"\int": "∫",
    r"\lambda": "λ",
    r"\le": "≤",
    r"\lfloor": "⌊",
    r"\ne": "≠",
    r"\pm": "±",
    r"\qquad": "    ",
    r"\quad": "  ",
    r"\rfloor": "⌋",
    r"\rho": "ρ",
    r"\sum": "∑",
    r"\tau": "τ",
    r"\theta": "θ",
    r"\times": "×",
    r"\to": "→",
    r"\%": "%",
    r"\,": "\u2009",
    r"\;": " ",
    r"\ ": " ",
}

GREEK_CHARS = set("ΔΩαγλρτθ")
MATH_OPS = set("=+-*/<>≤≥≈≠∈→·×±∩∪∫∑⌊⌋(),[];:|")


@dataclass
class RunSpec:
    text: str
    bold: bool = False
    italic: bool = False
    font: str = FONT_MAIN
    sz: str = "24"
    vert: Optional[str] = None   # "superscript" | "subscript"
    color: Optional[str] = None  # hex e.g. "7F1D1D"


def _read_braced(s: str, pos: int) -> Tuple[str, int]:
    """Lee un grupo {...} respetando llaves anidadas."""
    if pos >= len(s) or s[pos] != "{":
        return "", pos
    depth = 0
    start = pos + 1
    i = pos
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start:i], i + 1
        i += 1
    return s[start:], len(s)


def _read_atom(s: str, pos: int) -> Tuple[str, int]:
    """Lee un argumento de subíndice/superíndice o comando."""
    while pos < len(s) and s[pos] == " ":
        pos += 1
    if pos >= len(s):
        return "", pos
    if s[pos] == "{":
        return _read_braced(s, pos)
    if s[pos] == "\\":
        m = re.match(r"\\[a-zA-Z]+|\\[,;%_\s]", s[pos:])
        if m:
            cmd = m.group(0)
            nxt = pos + len(cmd)
            if cmd in (r"\text", r"\operatorname") and nxt < len(s) and s[nxt] == "{":
                inner, nxt2 = _read_braced(s, nxt)
                return cmd + "{" + inner + "}", nxt2
            return cmd, nxt
    return s[pos], pos + 1


def _strip_sizing_cmds(expr: str) -> str:
    expr = re.sub(r"\\(?:left|right|bigl|bigr|Bigl|Bigr|Big)(?=[\(\[\{\|\)\]\}\.])", "", expr)
    expr = expr.replace(r"\left.", "").replace(r"\right.", "")
    expr = expr.replace("{,}", ",")
    return expr


def latex_inline_to_runs(
    expr: str,
    sz: str = "24",
    base_bold: bool = False,
    base_italic: bool = False,
    vert: Optional[str] = None,
) -> List[RunSpec]:
    """Convierte expresión matemática LaTeX inline en RunSpecs limpios para Word."""
    expr = _strip_sizing_cmds(expr).strip()
    runs: List[RunSpec] = []
    i = 0

    def push(txt: str, italic: bool, v: Optional[str] = vert) -> None:
        if not txt:
            return
        if runs and runs[-1].italic == (italic or base_italic) and runs[-1].bold == base_bold and runs[-1].vert == v and runs[-1].sz == sz and runs[-1].font == FONT_MAIN:
            runs[-1].text += txt
        else:
            runs.append(RunSpec(
                text=txt,
                bold=base_bold,
                italic=(italic or base_italic),
                font=FONT_MAIN,
                sz=sz,
                vert=v,
            ))

    while i < len(expr):
        ch = expr[i]
        if ch == "\\":
            m = re.match(r"(\\[a-zA-Z]+|\\[,;%_\s])", expr[i:])
            if not m:
                i += 1
                continue
            cmd = m.group(1)
            i += len(cmd)
            if cmd in (r"\text", r"\operatorname"):
                arg, i = _read_braced(expr, i)
                # Dentro de \text{...} mantenemos texto recto
                arg_clean = arg.replace("{,}", ",").replace(r"\%", "%")
                push(arg_clean, italic=False)
            elif cmd == r"\frac":
                num, i = _read_atom(expr, i)
                den, i = _read_atom(expr, i)
                num_runs = latex_inline_to_runs(num, sz=sz, base_bold=base_bold, base_italic=base_italic, vert=vert)
                den_runs = latex_inline_to_runs(den, sz=sz, base_bold=base_bold, base_italic=base_italic, vert=vert)
                need_p_num = len(num_runs) > 1 or any(op in "".join(r.text for r in num_runs) for op in "+- ")
                need_p_den = len(den_runs) > 1 or any(op in "".join(r.text for r in den_runs) for op in "+- ")
                if need_p_num:
                    push("(", False)
                runs.extend(num_runs)
                if need_p_num:
                    push(")", False)
                push(" / ", False)
                if need_p_den:
                    push("(", False)
                runs.extend(den_runs)
                if need_p_den:
                    push(")", False)
            elif cmd == r"\sqrt":
                arg, i = _read_atom(expr, i)
                push("√", False)
                arg_runs = latex_inline_to_runs(arg, sz=sz, base_bold=base_bold, base_italic=base_italic, vert=vert)
                if len(arg_runs) > 1 or len("".join(r.text for r in arg_runs)) > 1:
                    push("(", False)
                    runs.extend(arg_runs)
                    push(")", False)
                else:
                    runs.extend(arg_runs)
            elif cmd == r"\hat":
                arg, i = _read_atom(expr, i)
                push(arg + "\u0302", italic=True)
            elif cmd in (r"\exp", r"\ln", r"\max", r"\min"):
                push(cmd[1:], italic=False)
            elif cmd in LATEX_SYMBOLS:
                sym = LATEX_SYMBOLS[cmd]
                push(sym, italic=(sym in GREEK_CHARS and False))
            else:
                push(cmd.lstrip("\\"), italic=False)
        elif ch == "_":
            i += 1
            arg, i = _read_atom(expr, i)
            sub_runs = latex_inline_to_runs(arg, sz=sz, base_bold=base_bold, base_italic=base_italic, vert="subscript")
            runs.extend(sub_runs)
        elif ch == "^":
            i += 1
            arg, i = _read_atom(expr, i)
            if arg.strip() == r"\circ":
                push("°", italic=False)
            else:
                sup_runs = latex_inline_to_runs(arg, sz=sz, base_bold=base_bold, base_italic=base_italic, vert="superscript")
                runs.extend(sup_runs)
        elif ch in "{}":
            i += 1
        elif ch.isalpha():
            push(ch, italic=True)
            i += 1
        else:
            push(ch, italic=False)
            i += 1
    return runs


# ---------------------------------------------------------------------------
# Conversor LaTeX -> OMML (m:oMathPara) para ecuaciones en bloque $$...$$
# ---------------------------------------------------------------------------
def _omml_run(text: str, italic: bool = True) -> etree._Element:
    r = make_el(mtag("r"))
    rpr = add_el(r, mtag("rPr"))
    if not italic:
        add_el(rpr, mtag("sty"), {mtag("val"): "p"})
    wrpr = add_el(r, wtag("rPr"))
    add_el(wrpr, wtag("rFonts"), {wtag("ascii"): "Cambria Math", wtag("hAnsi"): "Cambria Math"})
    add_el(wrpr, wtag("sz"), {wtag("val"): "24"})
    add_el(wrpr, wtag("szCs"), {wtag("val"): "24"})
    t = add_el(r, mtag("t"), {f"{{{XML_NS}}}space": "preserve"})
    t.text = text
    return r


def _latex_to_omml_nodes(expr: str) -> List[etree._Element]:
    expr = _strip_sizing_cmds(expr).strip()
    nodes: List[etree._Element] = []
    i = 0

    def attach_script(base_node: etree._Element, sub: Optional[str], sup: Optional[str]) -> etree._Element:
        if sub is not None and sup is not None:
            ss = make_el(mtag("sSubSup"))
            e = add_el(ss, mtag("e")); e.append(base_node)
            s_el = add_el(ss, mtag("sub"))
            for n in _latex_to_omml_nodes(sub):
                s_el.append(n)
            p_el = add_el(ss, mtag("sup"))
            for n in _latex_to_omml_nodes(sup):
                p_el.append(n)
            return ss
        elif sub is not None:
            ss = make_el(mtag("sSub"))
            e = add_el(ss, mtag("e")); e.append(base_node)
            s_el = add_el(ss, mtag("sub"))
            for n in _latex_to_omml_nodes(sub):
                s_el.append(n)
            return ss
        else:
            ss = make_el(mtag("sSup"))
            e = add_el(ss, mtag("e")); e.append(base_node)
            p_el = add_el(ss, mtag("sup"))
            for n in _latex_to_omml_nodes(sup):
                p_el.append(n)
            return ss

    while i < len(expr):
        ch = expr[i]
        cur_node: Optional[etree._Element] = None

        if ch == "\\":
            m = re.match(r"(\\[a-zA-Z]+|\\[,;%_\s])", expr[i:])
            if not m:
                i += 1
                continue
            cmd = m.group(1)
            i += len(cmd)
            if cmd in (r"\text", r"\operatorname"):
                arg, i = _read_braced(expr, i)
                cur_node = _omml_run(arg.replace("{,}", ",").replace(r"\%", "%"), italic=False)
            elif cmd == r"\frac":
                num, i = _read_atom(expr, i)
                den, i = _read_atom(expr, i)
                f = make_el(mtag("f"))
                num_el = add_el(f, mtag("num"))
                for n in _latex_to_omml_nodes(num):
                    num_el.append(n)
                den_el = add_el(f, mtag("den"))
                for n in _latex_to_omml_nodes(den):
                    den_el.append(n)
                cur_node = f
            elif cmd == r"\sqrt":
                arg, i = _read_atom(expr, i)
                rad = make_el(mtag("rad"))
                rpr = add_el(rad, mtag("radPr"))
                add_el(rpr, mtag("degHide"), {mtag("val"): "1"})
                add_el(rad, mtag("deg"))
                e_el = add_el(rad, mtag("e"))
                for n in _latex_to_omml_nodes(arg):
                    e_el.append(n)
                cur_node = rad
            elif cmd == r"\hat":
                arg, i = _read_atom(expr, i)
                cur_node = _omml_run(arg + "\u0302", italic=True)
            elif cmd in (r"\exp", r"\ln", r"\max", r"\min"):
                cur_node = _omml_run(cmd[1:], italic=False)
            elif cmd in LATEX_SYMBOLS:
                sym = LATEX_SYMBOLS[cmd]
                cur_node = _omml_run(sym, italic=(sym in GREEK_CHARS))
            else:
                cur_node = _omml_run(cmd.lstrip("\\"), italic=False)
        elif ch in "{}":
            i += 1
            continue
        elif ch in ("_", "^"):
            # Script sin base previa (p. ej. ^\circ C en [^\circ C])
            if ch == "^":
                i += 1
                arg, i = _read_atom(expr, i)
                if arg.strip() == r"\circ":
                    nodes.append(_omml_run("°", italic=False))
                else:
                    base = nodes.pop() if nodes else _omml_run("", italic=False)
                    nodes.append(attach_script(base, None, arg))
            else:
                i += 1
                arg, i = _read_atom(expr, i)
                base = nodes.pop() if nodes else _omml_run("", italic=False)
                nodes.append(attach_script(base, arg, None))
            continue
        else:
            # Agrupa letras o números consecutivos sencillos salvo que haya _ o ^
            if ch.isalpha():
                cur_node = _omml_run(ch, italic=True)
            else:
                cur_node = _omml_run(ch, italic=False)
            i += 1

        if cur_node is not None:
            # Verifica subíndice/superíndice inmediatamente posterior
            sub_arg = None
            sup_arg = None
            while i < len(expr) and expr[i] in ("_", "^"):
                kind = expr[i]
                i += 1
                arg, i = _read_atom(expr, i)
                if kind == "_":
                    sub_arg = arg
                else:
                    if arg.strip() == r"\circ":
                        nodes.append(cur_node)
                        cur_node = _omml_run("°", italic=False)
                    else:
                        sup_arg = arg
            if sub_arg is not None or sup_arg is not None:
                cur_node = attach_script(cur_node, sub_arg, sup_arg)
            nodes.append(cur_node)

    return nodes


def build_omml_para(latex_expr: str, eq_number: Optional[int] = None) -> etree._Element:
    """Construye una tabla sin bordes (92% ecuación OMML centrada | 8% número derecha)."""
    tbl = make_el(wtag("tbl"))
    tblPr = add_el(tbl, wtag("tblPr"))
    add_el(tblPr, wtag("tblW"), {wtag("w"): str(CONTENT_W_DXA), wtag("type"): "dxa"})
    add_el(tblPr, wtag("tblLayout"), {wtag("type"): "fixed"})
    borders = add_el(tblPr, wtag("tblBorders"))
    for b in ("top", "bottom", "left", "right", "insideH", "insideV"):
        add_el(borders, wtag(b), {wtag("val"): "none"})
    cellMar = add_el(tblPr, wtag("tblCellMar"))
    for side, val in (("top", "30"), ("bottom", "30"), ("left", "0"), ("right", "0")):
        add_el(cellMar, wtag(side), {wtag("w"): val, wtag("type"): "dxa"})

    w_eq = CONTENT_W_DXA - 720 if eq_number is not None else CONTENT_W_DXA
    tblGrid = add_el(tbl, wtag("tblGrid"))
    add_el(tblGrid, wtag("gridCol"), {wtag("w"): str(w_eq)})
    if eq_number is not None:
        add_el(tblGrid, wtag("gridCol"), {wtag("w"): "720"})

    tr = add_el(tbl, wtag("tr"))
    trPr = add_el(tr, wtag("trPr"))
    add_el(trPr, wtag("cantSplit"))

    tc1 = add_el(tr, wtag("tc"))
    tcPr1 = add_el(tc1, wtag("tcPr"))
    add_el(tcPr1, wtag("tcW"), {wtag("w"): str(w_eq), wtag("type"): "dxa"})
    add_el(tcPr1, wtag("vAlign"), {wtag("val"): "center"})
    p1 = add_el(tc1, wtag("p"))
    ppr1 = add_el(p1, wtag("pPr"))
    add_el(ppr1, wtag("pStyle"), {wtag("val"): "EquationPara"})
    add_el(ppr1, wtag("jc"), {wtag("val"): "center"})
    add_el(ppr1, wtag("spacing"), {wtag("before"): "20", wtag("after"): "20", wtag("line"): "240", wtag("lineRule"): "auto"})

    # Si una ecuación compuesta con \qquad excede el ancho útil, dividir en líneas limpias
    parts = [latex_expr]
    if len(latex_expr) > 88 and r"\qquad" in latex_expr:
        raw_parts = [pt.strip() for pt in latex_expr.split(r"\qquad") if pt.strip()]
        if len(raw_parts) >= 3:
            mid = (len(raw_parts) + 1) // 2
            parts = [r" \qquad ".join(raw_parts[:mid]), r" \qquad ".join(raw_parts[mid:])]
        elif len(raw_parts) == 2:
            parts = raw_parts

    for idx_pt, pt_expr in enumerate(parts):
        if idx_pt > 0:
            p1 = add_el(tc1, wtag("p"))
            ppr1 = add_el(p1, wtag("pPr"))
            add_el(ppr1, wtag("pStyle"), {wtag("val"): "EquationPara"})
            add_el(ppr1, wtag("jc"), {wtag("val"): "center"})
            add_el(ppr1, wtag("spacing"), {wtag("before"): "20", wtag("after"): "20", wtag("line"): "240", wtag("lineRule"): "auto"})
        omath = add_el(p1, mtag("oMath"))
        for node in _latex_to_omml_nodes(pt_expr):
            omath.append(node)

    if eq_number is not None:
        tc2 = add_el(tr, wtag("tc"))
        tcPr2 = add_el(tc2, wtag("tcPr"))
        add_el(tcPr2, wtag("tcW"), {wtag("w"): "720", wtag("type"): "dxa"})
        add_el(tcPr2, wtag("vAlign"), {wtag("val"): "center"})
        p2 = add_el(tc2, wtag("p"))
        ppr2 = add_el(p2, wtag("pPr"))
        add_el(ppr2, wtag("pStyle"), {wtag("val"): "EquationPara"})
        add_el(ppr2, wtag("jc"), {wtag("val"): "right"})
        add_el(ppr2, wtag("spacing"), {wtag("before"): "20", wtag("after"): "20", wtag("line"): "240", wtag("lineRule"): "auto"})
        r_num = add_el(p2, wtag("r"))
        rpr = add_el(r_num, wtag("rPr"))
        add_el(rpr, wtag("rFonts"), {wtag("ascii"): FONT_MAIN, wtag("hAnsi"): FONT_MAIN, wtag("cs"): FONT_MAIN})
        add_el(rpr, wtag("sz"), {wtag("val"): "24"})
        add_el(rpr, wtag("szCs"), {wtag("val"): "24"})
        t = add_el(r_num, wtag("t"))
        t.text = f"({eq_number})"

    return tbl


# ---------------------------------------------------------------------------
# Parser inline Markdown -> lista de RunSpec
# ---------------------------------------------------------------------------
INLINE_TOKEN_RE = re.compile(
    r"(\$\$.*?\$\$|\$[^$\n]+?\$|`\[DATO FALTANTE[^\]]*\]`|\[DATO FALTANTE[^\]]*\]|`[^`\n]+?`|\*\*\*[^*\n]+?\*\*\*|\*\*[^*\n]+?\*\*|\*[^*\n]+?\*)"
)


def parse_inline(
    text: str,
    sz: str = "24",
    base_bold: bool = False,
    base_italic: bool = False,
    base_color: Optional[str] = None,
) -> List[RunSpec]:
    """Convierte texto con Markdown inline, código, [DATO FALTANTE] y $math$ a RunSpecs."""
    runs: List[RunSpec] = []
    pos = 0
    for m in INLINE_TOKEN_RE.finditer(text):
        if m.start() > pos:
            plain = text[pos:m.start()].replace(r"\_", "_")
            runs.append(RunSpec(text=plain, bold=base_bold, italic=base_italic, font=FONT_MAIN, sz=sz, color=base_color))
        tok = m.group(0)
        if tok.startswith("$$") and tok.endswith("$$"):
            sub_runs = latex_inline_to_runs(tok[2:-2], sz=sz, base_bold=base_bold, base_italic=base_italic)
            for sr in sub_runs:
                sr.color = base_color
            runs.extend(sub_runs)
        elif tok.startswith("$") and tok.endswith("$"):
            sub_runs = latex_inline_to_runs(tok[1:-1], sz=sz, base_bold=base_bold, base_italic=base_italic)
            for sr in sub_runs:
                sr.color = base_color
            runs.extend(sub_runs)
        elif (tok.startswith("`[DATO FALTANTE") and tok.endswith("]`")) or tok.startswith("[DATO FALTANTE"):
            inner = tok[1:-1] if tok.startswith("`") else tok
            # Quita los corchetes externos al llamar recursivamente para evitar bucle
            runs.append(RunSpec(text="[", bold=base_bold, italic=True, font=FONT_MAIN, sz=sz, color="7F1D1D"))
            runs.extend(parse_inline(inner[1:-1], sz=sz, base_bold=base_bold, base_italic=True, base_color="7F1D1D"))
            runs.append(RunSpec(text="]", bold=base_bold, italic=True, font=FONT_MAIN, sz=sz, color="7F1D1D"))
        elif tok.startswith("`") and tok.endswith("`"):
            code_txt = tok[1:-1]
            mono_sz = str(max(16, int(sz) - 3))
            runs.append(RunSpec(text=code_txt, bold=base_bold, italic=base_italic, font=FONT_MONO, sz=mono_sz, color=base_color))
        elif tok.startswith("***") and tok.endswith("***"):
            runs.extend(parse_inline(tok[3:-3], sz=sz, base_bold=True, base_italic=True, base_color=base_color))
        elif tok.startswith("**") and tok.endswith("**"):
            runs.extend(parse_inline(tok[2:-2], sz=sz, base_bold=True, base_italic=base_italic, base_color=base_color))
        elif tok.startswith("*") and tok.endswith("*"):
            runs.extend(parse_inline(tok[1:-1], sz=sz, base_bold=base_bold, base_italic=True, base_color=base_color))
        pos = m.end()
    if pos < len(text):
        runs.append(RunSpec(text=text[pos:].replace(r"\_", "_"), bold=base_bold, italic=base_italic, font=FONT_MAIN, sz=sz, color=base_color))
    return runs


def append_runs_to_p(p: etree._Element, runs: List[RunSpec]) -> None:
    for rs in runs:
        if not rs.text:
            continue
        r = add_el(p, wtag("r"))
        rpr = add_el(r, wtag("rPr"))
        add_el(rpr, wtag("rFonts"), {
            wtag("ascii"): rs.font,
            wtag("hAnsi"): rs.font,
            wtag("cs"): rs.font,
        })
        if rs.bold:
            add_el(rpr, wtag("b"))
            add_el(rpr, wtag("bCs"))
        if rs.italic:
            add_el(rpr, wtag("i"))
            add_el(rpr, wtag("iCs"))
        if rs.color:
            add_el(rpr, wtag("color"), {wtag("val"): rs.color})
        if rs.vert:
            add_el(rpr, wtag("vertAlign"), {wtag("val"): rs.vert})
        add_el(rpr, wtag("sz"), {wtag("val"): rs.sz})
        add_el(rpr, wtag("szCs"), {wtag("val"): rs.sz})
        t = add_el(r, wtag("t"), {f"{{{XML_NS}}}space": "preserve"})
        t.text = rs.text


# ---------------------------------------------------------------------------
# Constructores de párrafos, tablas e imágenes OOXML
# ---------------------------------------------------------------------------
def build_paragraph(
    text_or_runs,
    style: str = "Normal",
    sz: str = "24",
    keep_next: bool = False,
    page_break_before: bool = False,
    jc: Optional[str] = None,
    first_line: Optional[int] = None,
    left_indent: Optional[int] = None,
    hanging: Optional[int] = None,
    space_before: Optional[int] = None,
    space_after: Optional[int] = None,
    line_spacing: Optional[int] = None,
    base_bold: bool = False,
    base_italic: bool = False,
) -> etree._Element:
    p = make_el(wtag("p"))
    ppr = add_el(p, wtag("pPr"))
    add_el(ppr, wtag("pStyle"), {wtag("val"): style})
    if keep_next:
        add_el(ppr, wtag("keepNext"))
    if page_break_before:
        add_el(ppr, wtag("pageBreakBefore"))
    if jc:
        add_el(ppr, wtag("jc"), {wtag("val"): jc})
    if any(x is not None for x in (first_line, left_indent, hanging)):
        attrib = {}
        if left_indent is not None:
            attrib[wtag("left")] = str(left_indent)
        if hanging is not None:
            attrib[wtag("hanging")] = str(hanging)
        if first_line is not None:
            attrib[wtag("firstLine")] = str(first_line)
        add_el(ppr, wtag("ind"), attrib)
    if any(x is not None for x in (space_before, space_after, line_spacing)):
        attrib = {}
        if space_before is not None:
            attrib[wtag("before")] = str(space_before)
        if space_after is not None:
            attrib[wtag("after")] = str(space_after)
        if line_spacing is not None:
            attrib[wtag("line")] = str(line_spacing)
            attrib[wtag("lineRule")] = "auto"
        add_el(ppr, wtag("spacing"), attrib)

    if isinstance(text_or_runs, str):
        runs = parse_inline(text_or_runs, sz=sz, base_bold=base_bold, base_italic=base_italic)
    else:
        runs = text_or_runs
    append_runs_to_p(p, runs)
    return p


def compute_col_widths(rows: List[List[str]], total_w: int = CONTENT_W_DXA) -> List[int]:
    """Calcula anchos proporcionales inteligentes en dxa para tablas sin desbordes."""
    ncols = len(rows[0])
    max_lens = [0.0] * ncols
    col_longest = [0] * ncols
    for r_idx, row in enumerate(rows):
        for c_idx in range(min(ncols, len(row))):
            cell_txt = re.sub(r"[`*]", "", row[c_idx])
            cell_txt = re.sub(r"\\[a-zA-Z]+", "X", cell_txt)
            # Evitar que rutas largas con '/' o '_' inflen una sola palabra
            words = re.split(r"[\s/]+", cell_txt)
            longest_word = max((len(w) for w in words if "_" not in w), default=5)
            col_longest[c_idx] = max(col_longest[c_idx], min(longest_word, 16))
            eff = max(min(longest_word, 18) * 1.9, min(len(cell_txt), 115) ** 0.72 * 3.0)
            if r_idx == 0:
                eff = max(eff, min(len(cell_txt), 40) * 1.0)
            if eff > max_lens[c_idx]:
                max_lens[c_idx] = eff

    # Columnas tipo checkbox Likert ("1", "2", "3", "4", "5") muy estrechas
    for c_idx in range(ncols):
        col_vals = [row[c_idx].strip() for row in rows if c_idx < len(row)]
        if all(v in ("1", "2", "3", "4", "5", "[ ]", "") for v in col_vals):
            max_lens[c_idx] = 3.2
            col_longest[c_idx] = 2

    total_score = sum(max_lens) or ncols
    min_widths = []
    for c_idx in range(ncols):
        if ncols >= 8 and col_longest[c_idx] <= 2:
            min_widths.append(400)
        else:
            min_widths.append(max(680, min(1450, col_longest[c_idx] * 92 + 220)))

    widths = [max(min_widths[i], int(round(total_w * (max_lens[i] / total_score)))) for i in range(ncols)]
    # Si la suma excede total_w, recortar proporcionalmente de las columnas más anchas
    excess = sum(widths) - total_w
    if excess > 0:
        for _ in range(excess):
            idx_max = widths.index(max(widths))
            widths[idx_max] -= 1
    elif excess < 0:
        idx_max = widths.index(max(widths))
        widths[idx_max] += (-excess)
    return widths


def build_apa_table(rows: List[List[str]], alignments: List[str], font_sz: str = "20") -> etree._Element:
    """Construye tabla OOXML en estricto formato APA 7 (solo líneas horizontales)."""
    ncols = len(rows[0])
    col_widths = compute_col_widths(rows, CONTENT_W_DXA)

    tbl = make_el(wtag("tbl"))
    tblPr = add_el(tbl, wtag("tblPr"))
    add_el(tblPr, wtag("tblW"), {wtag("w"): str(CONTENT_W_DXA), wtag("type"): "dxa"})
    add_el(tblPr, wtag("tblLayout"), {wtag("type"): "fixed"})

    # Bordes de tabla: top y bottom sólidos, insideH/insideV/left/right = none
    borders = add_el(tblPr, wtag("tblBorders"))
    add_el(borders, wtag("top"), {wtag("val"): "single", wtag("sz"): "8", wtag("space"): "0", wtag("color"): "000000"})
    add_el(borders, wtag("bottom"), {wtag("val"): "single", wtag("sz"): "8", wtag("space"): "0", wtag("color"): "000000"})
    add_el(borders, wtag("left"), {wtag("val"): "none"})
    add_el(borders, wtag("right"), {wtag("val"): "none"})
    add_el(borders, wtag("insideH"), {wtag("val"): "none"})
    add_el(borders, wtag("insideV"), {wtag("val"): "none"})

    cellMar = add_el(tblPr, wtag("tblCellMar"))
    add_el(cellMar, wtag("top"), {wtag("w"): "40", wtag("type"): "dxa"})
    add_el(cellMar, wtag("bottom"), {wtag("w"): "40", wtag("type"): "dxa"})
    add_el(cellMar, wtag("left"), {wtag("w"): "65", wtag("type"): "dxa"})
    add_el(cellMar, wtag("right"), {wtag("w"): "65", wtag("type"): "dxa"})

    tblGrid = add_el(tbl, wtag("tblGrid"))
    for w in col_widths:
        add_el(tblGrid, wtag("gridCol"), {wtag("w"): str(w)})

    last_row_idx = len(rows) - 1
    for r_idx, row in enumerate(rows):
        tr = add_el(tbl, wtag("tr"))
        trPr = add_el(tr, wtag("trPr"))
        add_el(trPr, wtag("cantSplit"))
        if r_idx == 0:
            add_el(trPr, wtag("tblHeader"))

        for c_idx in range(ncols):
            cell_text = row[c_idx].strip() if c_idx < len(row) else ""
            tc = add_el(tr, wtag("tc"))
            tcPr = add_el(tc, wtag("tcPr"))
            add_el(tcPr, wtag("tcW"), {wtag("w"): str(col_widths[c_idx]), wtag("type"): "dxa"})
            add_el(tcPr, wtag("vAlign"), {wtag("val"): "center" if r_idx == 0 else "top"})

            tcBorders = add_el(tcPr, wtag("tcBorders"))
            if r_idx == 0:
                add_el(tcBorders, wtag("top"), {wtag("val"): "single", wtag("sz"): "8", wtag("space"): "0", wtag("color"): "000000"})
                add_el(tcBorders, wtag("bottom"), {wtag("val"): "single", wtag("sz"): "6", wtag("space"): "0", wtag("color"): "000000"})
            elif r_idx == last_row_idx:
                add_el(tcBorders, wtag("bottom"), {wtag("val"): "single", wtag("sz"): "8", wtag("space"): "0", wtag("color"): "000000"})

            jc_val = alignments[c_idx] if c_idx < len(alignments) else "left"
            p = build_paragraph(
                cell_text,
                style="TableCell",
                sz=font_sz,
                jc=jc_val,
                first_line=0,
                space_before=15,
                space_after=15,
                line_spacing=240,
                base_bold=(r_idx == 0),
            )
            tc.append(p)

    return tbl


@dataclass
class ImageAsset:
    rid: str
    media_name: str
    src_path: Path
    width_px: int
    height_px: int
    width_emu: int
    height_emu: int


def build_image_paragraph(asset: ImageAsset, docpr_id: int) -> etree._Element:
    p = make_el(wtag("p"))
    ppr = add_el(p, wtag("pPr"))
    add_el(ppr, wtag("pStyle"), {wtag("val"): "NormalNoIndent"})
    add_el(ppr, wtag("jc"), {wtag("val"): "center"})
    add_el(ppr, wtag("keepNext"))
    add_el(ppr, wtag("spacing"), {wtag("before"): "60", wtag("after"): "40", wtag("line"): "240", wtag("lineRule"): "auto"})

    r = add_el(p, wtag("r"))
    drawing = add_el(r, wtag("drawing"))
    inline = add_el(drawing, wptag("inline"), {"distT": "0", "distB": "0", "distL": "0", "distR": "0"})
    add_el(inline, wptag("extent"), {"cx": str(asset.width_emu), "cy": str(asset.height_emu)})
    add_el(inline, wptag("effectExtent"), {"l": "0", "t": "0", "r": "0", "b": "0"})
    add_el(inline, wptag("docPr"), {"id": str(docpr_id), "name": asset.media_name})
    cNv = add_el(inline, wptag("cNvGraphicFramePr"))
    add_el(cNv, atag("graphicFrameLocks"), {"noChangeAspect": "1"})

    graphic = add_el(inline, atag("graphic"))
    graphicData = add_el(graphic, atag("graphicData"), {"uri": "http://schemas.openxmlformats.org/drawingml/2006/picture"})
    pic = add_el(graphicData, pictag("pic"))

    nvPicPr = add_el(pic, pictag("nvPicPr"))
    add_el(nvPicPr, pictag("cNvPr"), {"id": str(docpr_id), "name": asset.media_name})
    add_el(nvPicPr, pictag("cNvPicPr"))

    blipFill = add_el(pic, pictag("blipFill"))
    add_el(blipFill, atag("blip"), {rtag("embed"): asset.rid})
    stretch = add_el(blipFill, atag("stretch"))
    add_el(stretch, atag("fillRect"))

    spPr = add_el(pic, pictag("spPr"))
    xfrm = add_el(spPr, atag("xfrm"))
    add_el(xfrm, atag("off"), {"x": "0", "y": "0"})
    add_el(xfrm, atag("ext"), {"cx": str(asset.width_emu), "cy": str(asset.height_emu)})
    prstGeom = add_el(spPr, atag("prstGeom"), {"prst": "rect"})
    add_el(prstGeom, atag("avLst"))

    return p


# ---------------------------------------------------------------------------
# Estructuras de registro para Índices
# ---------------------------------------------------------------------------
@dataclass
class TocEntry:
    level: int
    title: str
    page: str = "..."


@dataclass
class CaptionEntry:
    label: str
    title: str
    page: str = "..."


# ---------------------------------------------------------------------------
# Parser de Markdown por bloques -> elementos OOXML
# ---------------------------------------------------------------------------
def parse_table_alignment(sep_line: str) -> List[str]:
    parts = [p.strip() for p in sep_line.strip().strip("|").split("|")]
    aligns = []
    for p in parts:
        if p.startswith(":") and p.endswith(":"):
            aligns.append("center")
        elif p.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("left")
    return aligns


def split_md_row(line: str) -> List[str]:
    """Divide una fila de tabla Markdown respetando tuberías '|' dentro de $...$ o `...`."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells: List[str] = []
    cur: List[str] = []
    in_math = False
    in_code = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            cur.append(ch)
            cur.append(line[i + 1])
            i += 2
            continue
        if ch == "$" and not in_code:
            in_math = not in_math
            cur.append(ch)
        elif ch == "`" and not in_math:
            in_code = not in_code
            cur.append(ch)
        elif ch == "|" and not in_math and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def clean_plain_title(raw: str) -> str:
    runs = parse_inline(raw, sz="24")
    return "".join(r.text for r in runs).strip()


class ThesisBuilder:
    def __init__(self, body_line_spacing: int = 480, fig_max_w_in: float = 5.2, fig_max_h_in: float = 2.85):
        self.body_line_spacing = body_line_spacing
        self.fig_max_w_in = fig_max_w_in
        self.fig_max_h_in = fig_max_h_in
        self.assets: List[ImageAsset] = []
        self.eq_counter = 0
        self.docpr_counter = 10
        self.toc_entries: List[TocEntry] = []
        self.table_entries: List[CaptionEntry] = []
        self.figure_entries: List[CaptionEntry] = []

    def register_image(self, path_str: str) -> ImageAsset:
        p = Path(path_str)
        if not p.exists():
            raise FileNotFoundError(f"Imagen faltante: {p}")
        with Image.open(p) as im:
            w_px, h_px = im.size
        idx = len(self.assets) + 1
        rid = f"rIdImg{idx}"
        ext = p.suffix.lower()
        media_name = f"fig_{idx:02d}{ext}"

        # Escala manteniendo proporción exacta dentro de límites configurados
        w_in = self.fig_max_w_in
        h_in = w_in * (h_px / w_px)
        if h_in > self.fig_max_h_in:
            h_in = self.fig_max_h_in
            w_in = h_in * (w_px / h_px)

        asset = ImageAsset(
            rid=rid,
            media_name=media_name,
            src_path=p,
            width_px=w_px,
            height_px=h_px,
            width_emu=int(round(w_in * EMU_PER_INCH)),
            height_emu=int(round(h_in * EMU_PER_INCH)),
        )
        self.assets.append(asset)
        return asset

    def parse_markdown_file(self, tag: str, md_path: Path) -> List[etree._Element]:
        lines = md_path.read_text(encoding="utf-8").splitlines()
        elements: List[etree._Element] = []
        n = len(lines)
        i = 0
        is_ref_section = (tag == "REF")

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # Saltar líneas vacías y separadores horizontales
            if not stripped or stripped == "---":
                i += 1
                continue

            # En referencias_apa7.md, omitir la nota meta-editorial de línea 3
            if is_ref_section and stripped.startswith("*Formato APA 7.ª edición — Lista maestra"):
                i += 1
                continue

            # Encabezados # .. ####
            hm = re.match(r"^(#{1,5})\s+(.+)$", stripped)
            if hm:
                lvl = len(hm.group(1))
                title = hm.group(2).strip()
                if lvl == 1:
                    elements.append(build_paragraph(
                        title,
                        style="Heading1",
                        sz="24",
                        keep_next=True,
                        page_break_before=True,
                        jc="center",
                        first_line=0,
                        space_before=0,
                        space_after=120,
                        line_spacing=self.body_line_spacing,
                        base_bold=True,
                    ))
                    self.toc_entries.append(TocEntry(1, clean_plain_title(title)))
                elif lvl == 2:
                    elements.append(build_paragraph(
                        title,
                        style="Heading2",
                        sz="24",
                        keep_next=True,
                        jc="left",
                        first_line=0,
                        space_before=120,
                        space_after=0,
                        line_spacing=self.body_line_spacing,
                        base_bold=True,
                    ))
                    self.toc_entries.append(TocEntry(2, clean_plain_title(title)))
                elif lvl == 3:
                    elements.append(build_paragraph(
                        title,
                        style="Heading3",
                        sz="24",
                        keep_next=True,
                        jc="left",
                        first_line=0,
                        space_before=80,
                        space_after=0,
                        line_spacing=self.body_line_spacing,
                        base_bold=True,
                        base_italic=True,
                    ))
                    self.toc_entries.append(TocEntry(3, clean_plain_title(title)))
                else:
                    elements.append(build_paragraph(
                        title,
                        style="Heading4",
                        sz="24",
                        keep_next=True,
                        jc="left",
                        first_line=INDENT_DXA,
                        space_before=60,
                        space_after=0,
                        line_spacing=self.body_line_spacing,
                        base_bold=True,
                    ))
                i += 1
                continue

            # Ecuación en bloque $$...$$
            eq_m = re.match(r"^\s*\$\$(.+)\$\$\s*$", line)
            if eq_m:
                self.eq_counter += 1
                elements.append(build_omml_para(eq_m.group(1).strip(), eq_number=self.eq_counter))
                i += 1
                continue

            # Bloque de cita > ...
            if stripped.startswith(">"):
                quote_lines = []
                while i < n and lines[i].strip().startswith(">"):
                    quote_lines.append(lines[i].strip().lstrip(">").strip())
                    i += 1
                q_txt = " ".join(quote_lines)
                elements.append(build_paragraph(
                    q_txt,
                    style="NormalNoIndent",
                    sz="24",
                    jc="left",
                    left_indent=INDENT_DXA,
                    first_line=0,
                    space_before=40,
                    space_after=40,
                    line_spacing=self.body_line_spacing,
                ))
                continue

            # Detección de título APA 7 de Tabla (**Tabla N** seguido de *Título*)
            tm = re.match(r"^\*\*(Tabla\s+[A-Z]?\d+)\*\*\s*$", stripped)
            if tm and i + 1 < n:
                tbl_label = tm.group(1)
                next_s = lines[i + 1].strip()
                title_m = re.match(r"^\*(.+)\*\s*$", next_s)
                tbl_title = title_m.group(1) if title_m else next_s
                self.table_entries.append(CaptionEntry(tbl_label, clean_plain_title(tbl_title)))
                elements.append(build_paragraph(
                    tbl_label,
                    style="TableTitleNum",
                    sz="24",
                    keep_next=True,
                    jc="left",
                    first_line=0,
                    space_before=120,
                    space_after=0,
                    line_spacing=276,
                    base_bold=True,
                ))
                elements.append(build_paragraph(
                    tbl_title,
                    style="TableTitleText",
                    sz="24",
                    keep_next=True,
                    jc="left",
                    first_line=0,
                    space_before=0,
                    space_after=60,
                    line_spacing=276,
                    base_italic=True,
                ))
                i += 2
                continue

            # Detección de título APA 7 de Figura (**Figura N** seguido de *Título* y ![...](...))
            fm = re.match(r"^\*\*(Figura\s+\d+)\*\*\s*$", stripped)
            if fm and i + 1 < n:
                fig_label = fm.group(1)
                next_s = lines[i + 1].strip()
                title_m = re.match(r"^\*(.+)\*\s*$", next_s)
                fig_title = title_m.group(1) if title_m else next_s
                self.figure_entries.append(CaptionEntry(fig_label, clean_plain_title(fig_title)))
                elements.append(build_paragraph(
                    fig_label,
                    style="FigureTitleNum",
                    sz="24",
                    keep_next=True,
                    jc="left",
                    first_line=0,
                    space_before=120,
                    space_after=0,
                    line_spacing=276,
                    base_bold=True,
                ))
                elements.append(build_paragraph(
                    fig_title,
                    style="FigureTitleText",
                    sz="24",
                    keep_next=True,
                    jc="left",
                    first_line=0,
                    space_before=0,
                    space_after=60,
                    line_spacing=276,
                    base_italic=True,
                ))
                i += 2
                continue

            # Imagen Markdown ![alt](path)
            im_m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped)
            if im_m:
                asset = self.register_image(im_m.group(2).strip())
                self.docpr_counter += 1
                elements.append(build_image_paragraph(asset, self.docpr_counter))
                i += 1
                continue

            # Tabla Markdown (| ... |)
            if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s:\-\|]+\|$", lines[i + 1].strip()):
                header_cells = split_md_row(lines[i])
                aligns = parse_table_alignment(lines[i + 1])
                rows = [header_cells]
                i += 2
                while i < n and lines[i].strip().startswith("|"):
                    rows.append(split_md_row(lines[i]))
                    i += 1
                # Si la tabla tiene muchas columnas (>= 8), usar 9 pt; si no, 10 pt
                tbl_sz = "18" if len(header_cells) >= 8 else "20"
                elements.append(build_apa_table(rows, aligns, font_sz=tbl_sz))
                continue

            # Nota debajo de tabla o figura (*Nota.* ...)
            if stripped.startswith("*Nota.*"):
                elements.append(build_paragraph(
                    stripped,
                    style="NoteText",
                    sz="20",
                    jc="left",
                    first_line=0,
                    space_before=40,
                    space_after=140,
                    line_spacing=252,
                ))
                i += 1
                continue

            # Listas numeradas o con viñetas (nivel 0 o subnivel)
            lm = re.match(r"^(\s*)(\d+\.|[-*])\s+(.+)$", line)
            if lm:
                indent_spaces = len(lm.group(1))
                marker = lm.group(2)
                content = lm.group(3).strip()
                sub_level = 1 if indent_spaces >= 2 else 0
                left_dxa = (INDENT_DXA * 2) if sub_level == 1 else INDENT_DXA
                hang_dxa = 360
                bullet_prefix = "•  " if marker in ("-", "*") else f"{marker} "
                runs = [RunSpec(text=bullet_prefix, bold=False, italic=False, font=FONT_MAIN, sz="24")]
                runs.extend(parse_inline(content, sz="24"))
                elements.append(build_paragraph(
                    runs,
                    style="NormalNoIndent",
                    sz="24",
                    jc="left",
                    left_indent=left_dxa + hang_dxa,
                    hanging=hang_dxa,
                    space_before=0,
                    space_after=0,
                    line_spacing=self.body_line_spacing,
                ))
                i += 1
                continue

            # Párrafo narrativo o ítem de Referencias
            if is_ref_section:
                elements.append(build_paragraph(
                    stripped,
                    style="ReferenceItem",
                    sz="24",
                    jc="left",
                    left_indent=INDENT_DXA,
                    hanging=INDENT_DXA,
                    space_before=0,
                    space_after=0,
                    line_spacing=self.body_line_spacing,
                ))
                i += 1
                continue

            # Metadatos de cabecera en Anexos (**Proyecto:**, **Institución:**, etc.)
            if tag == "ANEX" and re.match(r"^\*\*(Proyecto|Institución|Postulante|Vinculación documental|Código de|Ubicación|Firma|Propósito|Instrucciones|Observaciones):", stripped):
                elements.append(build_paragraph(
                    stripped,
                    style="NormalNoIndent",
                    sz="24",
                    jc="left",
                    first_line=0,
                    space_before=0,
                    space_after=0,
                    line_spacing=self.body_line_spacing,
                ))
                i += 1
                continue

            # Párrafo narrativo estándar APA 7 (sangría primera línea 1.27 cm, interlineado doble)
            elements.append(build_paragraph(
                stripped,
                style="Normal",
                sz="24",
                jc="left",
                first_line=INDENT_DXA,
                space_before=0,
                space_after=0,
                line_spacing=self.body_line_spacing,
            ))
            i += 1

        return elements


# ---------------------------------------------------------------------------
# Portada institucional e Índices (con campos Word + números de página reales)
# ---------------------------------------------------------------------------
def build_cover_page() -> List[etree._Element]:
    els: List[etree._Element] = []
    center_lines = [
        ("UNIVERSIDAD SALESIANA DE BOLIVIA", True, False, "28", 0, 60),
        ("CARRERA DE INGENIERÍA DE SISTEMAS", True, False, "26", 0, 720),
        ("TESIS DE GRADO", True, False, "24", 240, 480),
        ("SISTEMA PROTOTIPO INTEGRADO DE IOT, CONTROL PID E INTELIGENCIA ARTIFICIAL PARA LA REGULACIÓN MICROCLIMÁTICA Y DETECCIÓN TEMPRANA DE PLAGAS EN EL CULTIVO DE PAPA BAJO INVERNADERO", True, False, "26", 240, 720),
        ("Modalidad: Tesis de Grado para optar al grado de Licenciatura en Ingeniería de Sistemas", False, True, "24", 240, 720),
        ("Postulante:", True, False, "24", 240, 40),
        ("Alvaro Rodrigo De La Barra Velasco", False, False, "24", 0, 360),
        ("Docente Guía:", True, False, "24", 120, 40),
        ("Ing. Freddy Cosme Garnica Carrasco", False, False, "24", 0, 1200),
        ("La Paz – Bolivia", True, False, "24", 480, 40),
        ("2026", True, False, "24", 0, 0),
    ]
    for txt, b, it, sz, sb, sa in center_lines:
        els.append(build_paragraph(
            txt,
            style="NormalNoIndent",
            sz=sz,
            jc="center",
            first_line=0,
            space_before=sb,
            space_after=sa,
            line_spacing=360,
            base_bold=b,
            base_italic=it,
        ))
    return els


def _build_toc_line(label: str, page_str: str, indent_dxa: int = 0, bold: bool = False, italic: bool = False) -> etree._Element:
    p = make_el(wtag("p"))
    ppr = add_el(p, wtag("pPr"))
    add_el(ppr, wtag("pStyle"), {wtag("val"): "NormalNoIndent"})
    add_el(ppr, wtag("ind"), {wtag("left"): str(indent_dxa), wtag("right"): "420"})
    add_el(ppr, wtag("spacing"), {wtag("before"): "20", wtag("after"): "20", wtag("line"): "288", wtag("lineRule"): "auto"})
    tabs = add_el(ppr, wtag("tabs"))
    add_el(tabs, wtag("tab"), {wtag("val"): "right", wtag("leader"): "dot", wtag("pos"): str(CONTENT_W_DXA)})

    append_runs_to_p(p, [RunSpec(text=label, bold=bold, italic=italic, font=FONT_MAIN, sz="24")])
    r_tab = add_el(p, wtag("r"))
    add_el(r_tab, wtag("tab"))
    append_runs_to_p(p, [RunSpec(text=page_str, bold=bold, italic=False, font=FONT_MAIN, sz="24")])
    return p


def build_toc_section(
    toc_entries: List[TocEntry],
    table_entries: List[CaptionEntry],
    figure_entries: List[CaptionEntry],
) -> List[etree._Element]:
    els: List[etree._Element] = []

    # 1. Índice General con campo automático Word TOC + vista previa pre-poblada
    els.append(build_paragraph(
        "ÍNDICE GENERAL",
        style="TOCHeading",
        sz="24",
        keep_next=True,
        page_break_before=True,
        jc="center",
        first_line=0,
        space_before=0,
        space_after=160,
        line_spacing=360,
        base_bold=True,
    ))

    # Campo TOC Word estándar: begin -> instrText -> separate -> entradas cacheadas -> end
    p_begin = make_el(wtag("p"))
    ppr = add_el(p_begin, wtag("pPr"))
    add_el(ppr, wtag("spacing"), {wtag("before"): "0", wtag("after"): "0", wtag("line"): "240", wtag("lineRule"): "auto"})
    r1 = add_el(p_begin, wtag("r")); add_el(r1, wtag("fldChar"), {wtag("fldCharType"): "begin"})
    r2 = add_el(p_begin, wtag("r"))
    it = add_el(r2, wtag("instrText"), {f"{{{XML_NS}}}space": "preserve"})
    it.text = ' TOC \\o "1-3" \\h \\z \\u '
    r3 = add_el(p_begin, wtag("r")); add_el(r3, wtag("fldChar"), {wtag("fldCharType"): "separate"})
    els.append(p_begin)

    for entry in toc_entries:
        ind = 0 if entry.level == 1 else (360 if entry.level == 2 else 720)
        els.append(_build_toc_line(
            entry.title,
            entry.page,
            indent_dxa=ind,
            bold=(entry.level == 1),
            italic=(entry.level == 3),
        ))

    p_end = make_el(wtag("p"))
    r_end = add_el(p_end, wtag("r")); add_el(r_end, wtag("fldChar"), {wtag("fldCharType"): "end"})
    els.append(p_end)

    # 2. Índice de Tablas (en página nueva)
    els.append(build_paragraph(
        "ÍNDICE DE TABLAS",
        style="TOCHeading",
        sz="24",
        keep_next=True,
        page_break_before=True,
        jc="center",
        first_line=0,
        space_before=0,
        space_after=160,
        line_spacing=360,
        base_bold=True,
    ))
    for te in table_entries:
        els.append(_build_toc_line(f"{te.label}. {te.title}", te.page, indent_dxa=0, bold=False))

    # 3. Índice de Figuras (en página nueva)
    els.append(build_paragraph(
        "ÍNDICE DE FIGURAS",
        style="TOCHeading",
        sz="24",
        keep_next=True,
        page_break_before=True,
        jc="center",
        first_line=0,
        space_before=0,
        space_after=160,
        line_spacing=360,
        base_bold=True,
    ))
    for fe in figure_entries:
        els.append(_build_toc_line(f"{fe.label}. {fe.title}", fe.page, indent_dxa=0, bold=False))

    return els


# ---------------------------------------------------------------------------
# Generación de partes auxiliares OOXML (styles, settings, headers, rels, etc.)
# ---------------------------------------------------------------------------
def build_styles_xml(body_line_spacing: int) -> bytes:
    styles = make_el(wtag("styles"), nsmap={"w": W_NS})

    docDefaults = add_el(styles, wtag("docDefaults"))
    rPrDefault = add_el(docDefaults, wtag("rPrDefault"))
    rPr = add_el(rPrDefault, wtag("rPr"))
    add_el(rPr, wtag("rFonts"), {wtag("ascii"): FONT_MAIN, wtag("hAnsi"): FONT_MAIN, wtag("cs"): FONT_MAIN})
    add_el(rPr, wtag("sz"), {wtag("val"): "24"})
    add_el(rPr, wtag("szCs"), {wtag("val"): "24"})
    add_el(rPr, wtag("lang"), {wtag("val"): "es-BO"})

    pPrDefault = add_el(docDefaults, wtag("pPrDefault"))
    pPr = add_el(pPrDefault, wtag("pPr"))
    add_el(pPr, wtag("spacing"), {wtag("before"): "0", wtag("after"): "0", wtag("line"): str(body_line_spacing), wtag("lineRule"): "auto"})

    def add_style(sid: str, name: str, stype: str = "paragraph", based_on: Optional[str] = None,
                  jc: Optional[str] = None, bold: bool = False, italic: bool = False,
                  sz: str = "24", line: Optional[int] = None, before: int = 0, after: int = 0,
                  first_line: Optional[int] = None, left: Optional[int] = None, hanging: Optional[int] = None,
                  outline: Optional[int] = None, keep_next: bool = False, page_break: bool = False):
        st = add_el(styles, wtag("style"), {wtag("type"): stype, wtag("styleId"): sid})
        if sid == "Normal":
            st.set(wtag("default"), "1")
        add_el(st, wtag("name"), {wtag("val"): name})
        if based_on:
            add_el(st, wtag("basedOn"), {wtag("val"): based_on})
        add_el(st, wtag("qFormat"))
        sp = add_el(st, wtag("pPr"))
        if keep_next:
            add_el(sp, wtag("keepNext"))
        if page_break:
            add_el(sp, wtag("pageBreakBefore"))
        if jc:
            add_el(sp, wtag("jc"), {wtag("val"): jc})
        if outline is not None:
            add_el(sp, wtag("outlineLvl"), {wtag("val"): str(outline)})
        sp_attr = {wtag("before"): str(before), wtag("after"): str(after)}
        if line is not None:
            sp_attr[wtag("line")] = str(line)
            sp_attr[wtag("lineRule")] = "auto"
        add_el(sp, wtag("spacing"), sp_attr)
        if any(v is not None for v in (first_line, left, hanging)):
            ind_a = {}
            if left is not None:
                ind_a[wtag("left")] = str(left)
            if hanging is not None:
                ind_a[wtag("hanging")] = str(hanging)
            if first_line is not None:
                ind_a[wtag("firstLine")] = str(first_line)
            add_el(sp, wtag("ind"), ind_a)

        sr = add_el(st, wtag("rPr"))
        add_el(sr, wtag("rFonts"), {wtag("ascii"): FONT_MAIN, wtag("hAnsi"): FONT_MAIN, wtag("cs"): FONT_MAIN})
        if bold:
            add_el(sr, wtag("b")); add_el(sr, wtag("bCs"))
        if italic:
            add_el(sr, wtag("i")); add_el(sr, wtag("iCs"))
        add_el(sr, wtag("sz"), {wtag("val"): sz})
        add_el(sr, wtag("szCs"), {wtag("val"): sz})

    add_style("Normal", "Normal", jc="left", line=body_line_spacing, first_line=INDENT_DXA)
    add_style("NormalNoIndent", "Normal No Indent", based_on="Normal", jc="left", line=body_line_spacing, first_line=0)
    add_style("Heading1", "heading 1", based_on="NormalNoIndent", jc="center", bold=True, line=body_line_spacing, after=120, first_line=0, outline=0, keep_next=True, page_break=True)
    add_style("Heading2", "heading 2", based_on="NormalNoIndent", jc="left", bold=True, line=body_line_spacing, before=120, first_line=0, outline=1, keep_next=True)
    add_style("Heading3", "heading 3", based_on="NormalNoIndent", jc="left", bold=True, italic=True, line=body_line_spacing, before=80, first_line=0, outline=2, keep_next=True)
    add_style("Heading4", "heading 4", based_on="Normal", jc="left", bold=True, line=body_line_spacing, before=60, first_line=INDENT_DXA, outline=3, keep_next=True)
    add_style("TOCHeading", "TOC Heading", based_on="NormalNoIndent", jc="center", bold=True, line=360, after=160, first_line=0, keep_next=True, page_break=True)
    add_style("ReferenceItem", "Reference Item", based_on="NormalNoIndent", jc="left", line=body_line_spacing, left=INDENT_DXA, hanging=INDENT_DXA)
    add_style("TableTitleNum", "Table Title Number", based_on="NormalNoIndent", jc="left", bold=True, line=276, before=120, first_line=0, keep_next=True)
    add_style("TableTitleText", "Table Title Text", based_on="NormalNoIndent", jc="left", italic=True, line=276, after=60, first_line=0, keep_next=True)
    add_style("FigureTitleNum", "Figure Title Number", based_on="NormalNoIndent", jc="left", bold=True, line=276, before=120, first_line=0, keep_next=True)
    add_style("FigureTitleText", "Figure Title Text", based_on="NormalNoIndent", jc="left", italic=True, line=276, after=60, first_line=0, keep_next=True)
    add_style("NoteText", "Note Text", based_on="NormalNoIndent", jc="left", sz="20", line=252, before=40, after=140, first_line=0)
    add_style("TableCell", "Table Cell", based_on="NormalNoIndent", jc="left", sz="20", line=240, before=15, after=15, first_line=0)
    add_style("EquationPara", "Equation Paragraph", based_on="NormalNoIndent", jc="left", line=276, before=80, after=80, first_line=0)

    return etree.tostring(styles, xml_declaration=True, encoding="UTF-8")


def build_settings_xml() -> bytes:
    settings = make_el(wtag("settings"), nsmap={"w": W_NS})
    add_el(settings, wtag("defaultTabStop"), {wtag("val"): "720"})
    add_el(settings, wtag("updateFields"), {wtag("val"): "true"})
    return etree.tostring(settings, xml_declaration=True, encoding="UTF-8")


def build_header_empty_xml() -> bytes:
    hdr = make_el(wtag("hdr"), nsmap={"w": W_NS})
    add_el(hdr, wtag("p"))
    return etree.tostring(hdr, xml_declaration=True, encoding="UTF-8")


def build_header_page_xml() -> bytes:
    hdr = make_el(wtag("hdr"), nsmap={"w": W_NS})
    p = add_el(hdr, wtag("p"))
    ppr = add_el(p, wtag("pPr"))
    add_el(ppr, wtag("jc"), {wtag("val"): "right"})
    fld = add_el(p, wtag("fldSimple"), {wtag("instr"): " PAGE "})
    r = add_el(fld, wtag("r"))
    rpr = add_el(r, wtag("rPr"))
    add_el(rpr, wtag("rFonts"), {wtag("ascii"): FONT_MAIN, wtag("hAnsi"): FONT_MAIN, wtag("cs"): FONT_MAIN})
    add_el(rpr, wtag("sz"), {wtag("val"): "24"})
    add_el(rpr, wtag("szCs"), {wtag("val"): "24"})
    t = add_el(r, wtag("t"))
    t.text = "2"
    return etree.tostring(hdr, xml_declaration=True, encoding="UTF-8")


def build_content_types_xml() -> bytes:
    ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    types = etree.Element(f"{{{ns}}}Types", nsmap={None: ns})
    defaults = [
        ("rels", "application/vnd.openxmlformats-package.relationships+xml"),
        ("xml", "application/xml"),
        ("png", "image/png"),
        ("jpg", "image/jpeg"),
        ("jpeg", "image/jpeg"),
    ]
    for ext, ct in defaults:
        etree.SubElement(types, f"{{{ns}}}Default", {"Extension": ext, "ContentType": ct})
    overrides = [
        ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
        ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
        ("/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"),
        ("/word/header1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"),
        ("/word/header2.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"),
    ]
    for part, ct in overrides:
        etree.SubElement(types, f"{{{ns}}}Override", {"PartName": part, "ContentType": ct})
    return etree.tostring(types, xml_declaration=True, encoding="UTF-8")


def build_root_rels_xml() -> bytes:
    rels = etree.Element(f"{{{REL_NS}}}Relationships", nsmap={None: REL_NS})
    etree.SubElement(rels, f"{{{REL_NS}}}Relationship", {
        "Id": "rId1",
        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        "Target": "word/document.xml",
    })
    return etree.tostring(rels, xml_declaration=True, encoding="UTF-8")


def build_doc_rels_xml(assets: List[ImageAsset]) -> bytes:
    rels = etree.Element(f"{{{REL_NS}}}Relationships", nsmap={None: REL_NS})
    static_rels = [
        ("rIdStyles", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles", "styles.xml"),
        ("rIdSettings", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings", "settings.xml"),
        ("rIdHdr1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header", "header1.xml"),
        ("rIdHdr2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header", "header2.xml"),
    ]
    for rid, rtype, target in static_rels:
        etree.SubElement(rels, f"{{{REL_NS}}}Relationship", {"Id": rid, "Type": rtype, "Target": target})
    for a in assets:
        etree.SubElement(rels, f"{{{REL_NS}}}Relationship", {
            "Id": a.rid,
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
            "Target": f"media/{a.media_name}",
        })
    return etree.tostring(rels, xml_declaration=True, encoding="UTF-8")


# ---------------------------------------------------------------------------
# Ensamblaje completo y extracción de páginas reales con LibreOffice
# ---------------------------------------------------------------------------
def assemble_docx(
    output_path: Path,
    body_line_spacing: int = 480,
    fig_max_w_in: float = 5.2,
    fig_max_h_in: float = 2.85,
    page_map: Optional[dict] = None,
) -> Tuple[List[TocEntry], List[CaptionEntry], List[CaptionEntry]]:
    builder = ThesisBuilder(
        body_line_spacing=body_line_spacing,
        fig_max_w_in=fig_max_w_in,
        fig_max_h_in=fig_max_h_in,
    )

    body_sections: List[etree._Element] = []
    for tag, path in SOURCE_FILES:
        body_sections.extend(builder.parse_markdown_file(tag, path))

    if page_map:
        for te in builder.toc_entries:
            if te.title in page_map["toc"]:
                te.page = str(page_map["toc"][te.title])
        for tbl in builder.table_entries:
            if tbl.label in page_map["tables"]:
                tbl.page = str(page_map["tables"][tbl.label])
        for fig in builder.figure_entries:
            if fig.label in page_map["figures"]:
                fig.page = str(page_map["figures"][fig.label])

    doc = make_el(wtag("document"), nsmap=NSMAP_DOC)
    body = add_el(doc, wtag("body"))

    # Portada
    for el in build_cover_page():
        body.append(el)

    # Índices
    for el in build_toc_section(builder.toc_entries, builder.table_entries, builder.figure_entries):
        body.append(el)

    # Capítulos I, II, III, Referencias, Anexos
    for el in body_sections:
        body.append(el)

    # Propiedades de sección APA 7 (Carta, márgenes 2.54 cm, titlePg sin número en portada)
    sectPr = add_el(body, wtag("sectPr"))
    add_el(sectPr, wtag("headerReference"), {wtag("type"): "first", rtag("id"): "rIdHdr1"})
    add_el(sectPr, wtag("headerReference"), {wtag("type"): "default", rtag("id"): "rIdHdr2"})
    add_el(sectPr, wtag("pgSz"), {wtag("w"): str(PAGE_W_DXA), wtag("h"): str(PAGE_H_DXA)})
    add_el(sectPr, wtag("pgMar"), {
        wtag("top"): str(MARGIN_DXA),
        wtag("right"): str(MARGIN_DXA),
        wtag("bottom"): str(MARGIN_DXA),
        wtag("left"): str(MARGIN_DXA),
        wtag("header"): "720",
        wtag("footer"): "720",
        wtag("gutter"): "0",
    })
    add_el(sectPr, wtag("titlePg"))

    doc_bytes = etree.tostring(doc, xml_declaration=True, encoding="UTF-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", build_content_types_xml())
        zf.writestr("_rels/.rels", build_root_rels_xml())
        zf.writestr("word/document.xml", doc_bytes)
        zf.writestr("word/styles.xml", build_styles_xml(body_line_spacing))
        zf.writestr("word/settings.xml", build_settings_xml())
        zf.writestr("word/header1.xml", build_header_empty_xml())
        zf.writestr("word/header2.xml", build_header_page_xml())
        zf.writestr("word/_rels/document.xml.rels", build_doc_rels_xml(builder.assets))
        for asset in builder.assets:
            zf.write(asset.src_path, f"word/media/{asset.media_name}")

    return builder.toc_entries, builder.table_entries, builder.figure_entries


def extract_real_pages(
    docx_path: Path,
    toc_entries: List[TocEntry],
    table_entries: List[CaptionEntry],
    figure_entries: List[CaptionEntry],
) -> Tuple[dict, dict]:
    """Convierte docx -> pdf con LibreOffice y extrae números de página reales."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(docx_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pdf_path = tmp / (docx_path.stem + ".pdf")
        txt = subprocess.check_output(["pdftotext", str(pdf_path), "-"], text=True)
        pages = txt.split("\x0c")
        if pages and not pages[-1].strip():
            pages = pages[:-1]

        # Normaliza texto por página para búsqueda robusta sin saltos de línea
        norm_pages = [re.sub(r"\s+", " ", p) for p in pages]
        # Ignorar páginas preliminares de portada e índices al buscar ocurrencias reales del cuerpo
        # Buscamos dónde arranca "CAPÍTULO I. INTRODUCCIÓN" fuera del índice (segunda o última coincidencia)
        cap_starts = {}
        for marker in ["CAPÍTULO I. INTRODUCCIÓN", "CAPÍTULO II. MARCO TEÓRICO", "CAPÍTULO III. DISEÑO METODOLÓGICO", "REFERENCIAS", "ANEXOS DE INSTRUMENTOS METODOLÓGICOS Y PROTOCOLOS EXPERIMENTALES"]:
            matches = [idx + 1 for idx, ptxt in enumerate(norm_pages) if marker in ptxt]
            cap_starts[marker] = matches[-1] if matches else None

        body_start_idx = (cap_starts.get("CAPÍTULO I. INTRODUCCIÓN") or 5) - 1

        page_map = {"toc": {}, "tables": {}, "figures": {}}
        search_from = body_start_idx
        for te in toc_entries:
            needle = re.sub(r"\s+", " ", te.title)[:55]
            found = None
            for idx in range(search_from, len(norm_pages)):
                if needle in norm_pages[idx]:
                    found = idx + 1
                    search_from = idx
                    break
            if found is None:
                for idx in range(body_start_idx, len(norm_pages)):
                    if needle[:30] in norm_pages[idx]:
                        found = idx + 1
                        break
            if found:
                page_map["toc"][te.title] = found

        for tbl in table_entries:
            # Buscar en el cuerpo la etiqueta exacta "Tabla N"
            pat = re.compile(rf"\b{re.escape(tbl.label)}\b")
            for idx in range(body_start_idx, len(norm_pages)):
                if pat.search(norm_pages[idx]):
                    page_map["tables"][tbl.label] = idx + 1
                    break

        for fig in figure_entries:
            pat = re.compile(rf"\b{re.escape(fig.label)}\b")
            for idx in range(body_start_idx, len(norm_pages)):
                if pat.search(norm_pages[idx]):
                    page_map["figures"][fig.label] = idx + 1
                    break

        stats = {
            "total_pages": len(pages),
            "cap_starts": cap_starts,
            "cap3_pages": (
                (cap_starts["REFERENCIAS"] - cap_starts["CAPÍTULO III. DISEÑO METODOLÓGICO"])
                if cap_starts.get("REFERENCIAS") and cap_starts.get("CAPÍTULO III. DISEÑO METODOLÓGICO")
                else None
            ),
        }
        return page_map, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ensamblador APA 7 .docx para tesis USB.")
    parser.add_argument("--line-spacing", type=int, default=480, help="Interlineado OOXML (480=doble, 360=1.5)")
    parser.add_argument("--fig-w", type=float, default=5.2, help="Ancho máximo de figura en pulgadas")
    parser.add_argument("--fig-h", type=float, default=2.85, help="Alto máximo de figura en pulgadas")
    parser.add_argument("--output", type=Path, default=OUTPUT_DOCX)
    args = parser.parse_args()

    # Pasada 1: generar documento base y medir páginas reales en LibreOffice
    toc_e, tbl_e, fig_e = assemble_docx(
        args.output,
        body_line_spacing=args.line_spacing,
        fig_max_w_in=args.fig_w,
        fig_max_h_in=args.fig_h,
    )
    page_map, stats = extract_real_pages(args.output, toc_e, tbl_e, fig_e)

    # Pasada 2: estampar números de página exactos en Índices y re-verificar
    toc_e, tbl_e, fig_e = assemble_docx(
        args.output,
        body_line_spacing=args.line_spacing,
        fig_max_w_in=args.fig_w,
        fig_max_h_in=args.fig_h,
        page_map=page_map,
    )
    _, stats_final = extract_real_pages(args.output, toc_e, tbl_e, fig_e)

    print("=== RESUMEN DE ENSAMBLAJE DOCX APA 7 ===")
    print(f"Archivo generado : {args.output}")
    print(f"Total páginas PDF: {stats_final['total_pages']}")
    print(f"Inicio capítulos : {stats_final['cap_starts']}")
    print(f"Páginas Cap. III : {stats_final['cap3_pages']}")
    print(f"Tablas indexadas : {len(tbl_e)} | Figuras indexadas: {len(fig_e)}")


if __name__ == "__main__":
    main()
