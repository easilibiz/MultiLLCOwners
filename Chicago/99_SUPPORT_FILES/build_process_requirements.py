from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Chicago_LLC_Portfolio_Process_Requirements.docx"
FIG = ROOT / "qa_llc_process" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

BLACK = "000000"
DARK = "333333"
MID = "666666"
LIGHT = "E6E6E6"
PALE = "F3F3F3"
WHITE = "FFFFFF"


def pc(value):
    return "#" + value if isinstance(value, str) and len(value) == 6 else value


def font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    bolds = [
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf"),
    ]
    paths = bolds if bold else candidates
    for p in paths:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def box(draw, xy, title, lines=(), fill=WHITE, width=3, title_size=30, body_size=24, align="center"):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=16, fill=pc(fill), outline=pc(BLACK), width=width)
    f1, f2 = font(title_size, True), font(body_size)
    parts = [title] + list(lines)
    heights = [draw.textbbox((0, 0), t, font=f1 if i == 0 else f2)[3] for i, t in enumerate(parts)]
    total = sum(heights) + 12 * (len(parts) - 1)
    y = y1 + (y2 - y1 - total) / 2
    for i, t in enumerate(parts):
        ff = f1 if i == 0 else f2
        bb = draw.textbbox((0, 0), t, font=ff)
        if align == "left":
            x = x1 + 24
        else:
            x = x1 + (x2 - x1 - (bb[2] - bb[0])) / 2
        draw.text((x, y), t, fill=pc(BLACK), font=ff)
        y += heights[i] + 12


def arrow(draw, start, end, width=4, dashed=False):
    x1, y1 = start
    x2, y2 = end
    if dashed:
        steps = 12
        for i in range(0, steps, 2):
            a, b = i / steps, min((i + 1) / steps, 1)
            draw.line((x1 + (x2-x1)*a, y1 + (y2-y1)*a, x1 + (x2-x1)*b, y1 + (y2-y1)*b), fill=pc(BLACK), width=width)
    else:
        draw.line((x1, y1, x2, y2), fill=pc(BLACK), width=width)
    import math
    angle = math.atan2(y2-y1, x2-x1)
    length = 18
    for delta in (2.55, -2.55):
        draw.line((x2, y2, x2 + length*math.cos(angle+delta), y2 + length*math.sin(angle+delta)), fill=pc(BLACK), width=width)


def canvas(title, subtitle=""):
    im = Image.new("RGB", (1800, 1050), pc(WHITE))
    d = ImageDraw.Draw(im)
    d.text((70, 42), title, font=font(40, True), fill=pc(BLACK))
    if subtitle:
        d.text((70, 96), subtitle, font=font(25), fill=pc(MID))
    d.line((70, 140, 1730, 140), fill=pc(BLACK), width=3)
    return im, d


def save(im, name):
    p = FIG / name
    im.save(p, dpi=(200, 200))
    return p


def fig_workflow():
    im, d = canvas("End-to-end portfolio discovery workflow", "The clustering key is the normalized owner tax mailing address")
    labels = [
        ("1. Parcel universe", "All parcels; no property-type filter"),
        ("2. LLC owner filter", "Normalized owner name ends in LLC"),
        ("3. Normalize", "LLC name + owner mailing address"),
        ("4. Group", "By owner mailing address"),
        ("5. Threshold", "2+ LLCs and 2+ parcels"),
        ("6. Review", "Intermediary flags + SOS evidence"),
        ("7. Route", "High / medium / manual review"),
        ("8. Deliver", "Shortlist + property evidence"),
    ]
    coords = []
    for row in range(2):
        for col in range(4):
            x1 = 70 + col * 425
            y1 = 200 + row * 370
            coords.append((x1, y1, x1 + 360, y1 + 205))
    order = [0, 1, 2, 3, 7, 6, 5, 4]
    for idx, pos in enumerate(order):
        title, sub = labels[idx]
        box(d, coords[pos], title, (sub,), fill=PALE if idx in (3, 4) else WHITE, title_size=27, body_size=21)
    for a, b in zip(order[:-1], order[1:]):
        A, B = coords[a], coords[b]
        if A[1] == B[1]:
            arrow(d, (A[2], (A[1]+A[3])//2), (B[0], (B[1]+B[3])//2))
        else:
            arrow(d, ((A[0]+A[2])//2, A[3]), ((B[0]+B[2])//2, B[1]))
    d.text((70, 955), "Control rule: never substitute the physical property address for the owner mailing address.", font=font(27, True), fill=pc(BLACK))
    return save(im, "01_workflow.png")


def fig_grouping():
    im, d = canvas("Correct grouping key vs. the wrong key", "Three differently named LLCs can reveal one probable portfolio")
    box(d, (610, 185, 1190, 335), "OWNER TAX MAILING ADDRESS", ("1250 W Example Ave, Suite 400", "Chicago, IL 60607"), fill=PALE, title_size=29, body_size=23)
    llcs = ["Lakeside 101 LLC", "West End Holdings LLC", "Huron Property LLC"]
    props = ["101 Lake St", "88 West End Ave", "740 Huron St"]
    for i in range(3):
        x = 90 + i * 575
        box(d, (x, 500, x+480, 640), llcs[i], ("Different legal entity name",), title_size=27, body_size=20)
        box(d, (x, 760, x+480, 900), "PROPERTY / SITUS", (props[i], "Evidence only — not a key"), fill=WHITE, title_size=25, body_size=20)
        arrow(d, (900, 335), (x+240, 500))
        arrow(d, (x+240, 640), (x+240, 760), dashed=True)
    d.text((70, 960), "CORRECT: shared owner mailing address creates the candidate cluster.   WRONG: grouping by property address fragments the portfolio.", font=font(25, True), fill=pc(BLACK))
    return save(im, "02_grouping_key.png")


def fig_relationships():
    im, d = canvas("Data relationship model", "One address may link many LLCs; each LLC may own one or more parcels")
    box(d, (70, 390, 480, 620), "OWNER MAILING ADDRESS", ("Normalized hub", "Candidate portfolio key"), fill=PALE, title_size=27, body_size=22)
    for i, name in enumerate(["LLC A", "LLC B", "LLC C"]):
        y = 190 + i*280
        box(d, (670, y, 1030, y+155), name, ("Legal owner name",), title_size=29, body_size=21)
        arrow(d, (480, 505), (670, y+78))
        box(d, (1300, y-35, 1710, y+190), "PARCEL RECORDS", ("PIN / parcel ID", "Property address", "Tax-roll evidence"), title_size=25, body_size=20)
        arrow(d, (1030, y+78), (1300, y+78))
    box(d, (660, 920, 1040, 1015), "SOS ENTITY EVIDENCE", ("Manager / agent / entity address",), fill=WHITE, title_size=22, body_size=18)
    for i in range(3):
        arrow(d, (850, 920), (850, 345+i*280), dashed=True)
    d.text((1160, 945), "Corroborates after clustering", font=font(23, True), fill=pc(BLACK))
    return save(im, "03_relationships.png")


def fig_decision_tree():
    im, d = canvas("Cluster qualification and routing decision tree", "Thresholds establish a candidate; corroboration sets confidence")
    steps = [
        ("Valid normalized owner mailing address?", 170),
        ("2+ distinct normalized LLC names?", 360),
        ("2+ distinct parcels / properties?", 550),
        ("Intermediary or mass-service address flag?", 740),
    ]
    for label, y in steps:
        box(d, (560, y, 1240, y+125), label, (), fill=PALE, title_size=25)
    for i in range(len(steps)-1):
        arrow(d, (900, steps[i][1]+125), (900, steps[i+1][1]))
        d.text((915, steps[i][1]+142), "YES", font=font(20, True), fill=pc(BLACK))
    for _, y in steps[:3]:
        arrow(d, (560, y+63), (280, y+63))
        d.text((430, y+33), "NO", font=font(20, True), fill=pc(BLACK))
    box(d, (60, 425, 280, 655), "DO NOT QUALIFY", ("Retain QA reason", "in exclusion log"), title_size=25, body_size=20)
    arrow(d, (560, 803), (300, 900)); d.text((420, 830), "YES", font=font(20, True), fill=pc(BLACK))
    arrow(d, (1240, 803), (1500, 900)); d.text((1290, 830), "NO", font=font(20, True), fill=pc(BLACK))
    box(d, (80, 900, 520, 1015), "MANUAL REVIEW", ("Do not silently exclude",), title_size=26, body_size=20)
    box(d, (1280, 900, 1720, 1015), "SOS CORROBORATION", ("Route high / medium / review",), title_size=25, body_size=19)
    return save(im, "04_decision_tree.png")


def fig_outputs():
    im, d = canvas("Required output package", "Every candidate cluster must remain traceable to parcel-level evidence")
    box(d, (650, 170, 1150, 330), "QUALIFIED CLUSTERS", ("Shared owner mailing address", "2+ LLCs | 2+ parcels"), fill=PALE, title_size=29, body_size=22)
    outputs = [
        ("Cluster summary", "One row per address cluster"),
        ("Property evidence", "One row per parcel / LLC"),
        ("Entity enrichment", "SOS match and corroboration"),
        ("Mailing shortlist", "Recipient, address, confidence"),
        ("QA / exclusion log", "Reasons, flags, and exceptions"),
    ]
    for i, (t, s) in enumerate(outputs):
        x = 65 + (i % 3) * 575
        y = 510 + (i // 3) * 270
        box(d, (x, y, x+500, y+175), t, (s,), title_size=26, body_size=20)
        arrow(d, (900, 330), (x+250, y))
    d.text((70, 985), "Auditability rule: a mailed record must be reproducible from the source parcel record, normalization, grouping, flags, and corroboration.", font=font(23, True), fill=pc(BLACK))
    return save(im, "05_outputs.png")


FIGURES = [fig_workflow(), fig_grouping(), fig_relationships(), fig_decision_tree(), fig_outputs()]


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcPr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in("w:tcMar")
    if tcMar is None:
        tcMar = OxmlElement("w:tcMar")
        tcPr.append(tcMar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tcMar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tcMar.append(node)
        node.set(qn("w:w"), str(v)); node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)


def set_table_geometry(table, widths):
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    tblW.set(qn("w:w"), "9360"); tblW.set(qn("w:type"), "dxa")
    ind = OxmlElement("w:tblInd"); ind.set(qn("w:w"), "120"); ind.set(qn("w:type"), "dxa"); tblPr.append(ind)
    grid = table._tbl.tblGrid
    for child in list(grid): grid.remove(child)
    for w in widths:
        col = OxmlElement("w:gridCol"); col.set(qn("w:w"), str(w)); grid.append(col)
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            cell.width = Inches(widths[i]/1440)
            tcW = cell._tc.get_or_add_tcPr().find(qn("w:tcW"))
            tcW.set(qn("w:w"), str(widths[i])); tcW.set(qn("w:type"), "dxa")
            set_cell_margins(cell)


def set_font(run, size=11, bold=None, italic=None, color=BLACK):
    run.font.name = "Calibri"
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Calibri")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Calibri")
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None: run.bold = bold
    if italic is not None: run.italic = italic


def add_field(paragraph, instruction):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = instruction
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t"); txt.text = "1"
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, sep, txt, end])
    set_font(run, 9, color=MID)


def setup_numbering(doc):
    num_part = doc.part.numbering_part.element
    max_abs = max([int(x.get(qn("w:abstractNumId"))) for x in num_part.findall(qn("w:abstractNum"))] or [0])
    max_num = max([int(x.get(qn("w:numId"))) for x in num_part.findall(qn("w:num"))] or [0])
    ids = {}
    for kind, fmt, text_marker in (("bullet", "bullet", "•"), ("decimal", "decimal", "%1.")):
        max_abs += 1; max_num += 1
        abstract = OxmlElement("w:abstractNum"); abstract.set(qn("w:abstractNumId"), str(max_abs))
        multi = OxmlElement("w:multiLevelType"); multi.set(qn("w:val"), "singleLevel"); abstract.append(multi)
        lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0"); abstract.append(lvl)
        start = OxmlElement("w:start"); start.set(qn("w:val"), "1"); lvl.append(start)
        numFmt = OxmlElement("w:numFmt"); numFmt.set(qn("w:val"), fmt); lvl.append(numFmt)
        lvlText = OxmlElement("w:lvlText"); lvlText.set(qn("w:val"), text_marker); lvl.append(lvlText)
        suff = OxmlElement("w:suff"); suff.set(qn("w:val"), "tab"); lvl.append(suff)
        pPr = OxmlElement("w:pPr")
        tabs = OxmlElement("w:tabs"); tab = OxmlElement("w:tab"); tab.set(qn("w:val"), "num"); tab.set(qn("w:pos"), "540"); tabs.append(tab); pPr.append(tabs)
        ind = OxmlElement("w:ind"); ind.set(qn("w:left"), "540"); ind.set(qn("w:hanging"), "270"); pPr.append(ind)
        spacing = OxmlElement("w:spacing"); spacing.set(qn("w:after"), "80"); spacing.set(qn("w:line"), "300"); spacing.set(qn("w:lineRule"), "auto"); pPr.append(spacing)
        lvl.append(pPr)
        if kind == "bullet":
            rPr = OxmlElement("w:rPr"); rf = OxmlElement("w:rFonts"); rf.set(qn("w:ascii"), "Calibri"); rf.set(qn("w:hAnsi"), "Calibri"); rPr.append(rf); lvl.append(rPr)
        num_part.append(abstract)
        num = OxmlElement("w:num"); num.set(qn("w:numId"), str(max_num)); aid = OxmlElement("w:abstractNumId"); aid.set(qn("w:val"), str(max_abs)); num.append(aid); num_part.append(num)
        ids[kind] = max_num
    return ids


doc = Document()
doc.settings.odd_and_even_pages_header_footer = True
section = doc.sections[0]
section.page_width = Inches(8.5); section.page_height = Inches(11)
section.top_margin = Inches(1); section.bottom_margin = Inches(1); section.left_margin = Inches(1); section.right_margin = Inches(1)
section.header_distance = Inches(0.492); section.footer_distance = Inches(0.492)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Calibri"; normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
normal.font.size = Pt(11); normal.font.color.rgb = RGBColor(0,0,0)
normal.paragraph_format.space_before = Pt(0); normal.paragraph_format.space_after = Pt(6); normal.paragraph_format.line_spacing = 1.25
for name, size, before, after in (("Heading 1",16,18,10),("Heading 2",13,14,7),("Heading 3",12,10,5)):
    s = styles[name]; s.font.name="Calibri"; s._element.rPr.rFonts.set(qn("w:ascii"),"Calibri"); s._element.rPr.rFonts.set(qn("w:hAnsi"),"Calibri")
    s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_before=Pt(before); s.paragraph_format.space_after=Pt(after); s.paragraph_format.keep_with_next=True

for list_style_name in ("List Bullet", "List Number"):
    ls = styles[list_style_name]
    ls.font.name = "Calibri"; ls.font.size = Pt(11); ls.font.color.rgb = RGBColor(0,0,0)
    ls.paragraph_format.left_indent = Inches(0.375)
    ls.paragraph_format.first_line_indent = Inches(-0.188)
    ls.paragraph_format.space_after = Pt(4)
    ls.paragraph_format.line_spacing = 1.25

# Patch Word's built-in list definitions to the compact-reference preset geometry.
num_root = doc.part.numbering_part.element
for abstract in num_root.findall(qn("w:abstractNum")):
    if abstract.get(qn("w:abstractNumId")) not in ("7", "8"):
        continue
    lvl = abstract.find(qn("w:lvl")); ppr = lvl.find(qn("w:pPr"))
    tab = ppr.find(qn("w:tabs")).find(qn("w:tab")); tab.set(qn("w:pos"), "540")
    ind = ppr.find(qn("w:ind")); ind.set(qn("w:left"), "540"); ind.set(qn("w:hanging"), "270")
    spacing = ppr.find(qn("w:spacing"))
    if spacing is None: spacing = OxmlElement("w:spacing"); ppr.append(spacing)
    spacing.set(qn("w:after"), "80"); spacing.set(qn("w:line"), "300"); spacing.set(qn("w:lineRule"), "auto")


def add_list(text, kind="bullet"):
    p = doc.add_paragraph(style="List Bullet" if kind == "bullet" else "List Number")
    r = p.add_run(text); set_font(r)
    return p


def add_numbered(items):
    """Add one independently restarting real numbered-list sequence."""
    root = doc.part.numbering_part.element
    next_id = max([int(x.get(qn("w:numId"))) for x in root.findall(qn("w:num"))] or [0]) + 1
    num = OxmlElement("w:num"); num.set(qn("w:numId"), str(next_id))
    aid = OxmlElement("w:abstractNumId"); aid.set(qn("w:val"), "7"); num.append(aid); root.append(num)
    override = OxmlElement("w:lvlOverride"); override.set(qn("w:ilvl"), "0")
    start_override = OxmlElement("w:startOverride"); start_override.set(qn("w:val"), "1")
    override.append(start_override); num.append(override)
    for text_value in items:
        p = doc.add_paragraph()
        numPr = OxmlElement("w:numPr")
        ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), "0"); numPr.append(ilvl)
        numId = OxmlElement("w:numId"); numId.set(qn("w:val"), str(next_id)); numPr.append(numId)
        p._p.get_or_add_pPr().append(numPr)
        r = p.add_run(text_value); set_font(r)
    return next_id


def add_rule(paragraph, color=BLACK, size="12"):
    pPr = paragraph._p.get_or_add_pPr(); pbdr = OxmlElement("w:pBdr"); bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single"); bot.set(qn("w:sz"), size); bot.set(qn("w:space"), "6"); bot.set(qn("w:color"), color)
    pbdr.append(bot); pPr.append(pbdr)


def add_table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=""; r=c.paragraphs[0].add_run(h); set_font(r,9.5,True); shade(c,LIGHT); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_repeat_table_header(t.rows[0])
    for row in rows:
        cells=t.add_row().cells
        for i,val in enumerate(row):
            cells[i].text=""; r=cells[i].paragraphs[0].add_run(str(val)); set_font(r,9.3)
            cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.TOP
    set_table_geometry(t,widths)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return t


def add_figure(path, number, title, note):
    p = doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(4); p.paragraph_format.space_after=Pt(5)
    run=p.add_run(); run.add_picture(str(path), width=Inches(6.5))
    docPr = run._r.xpath(".//wp:docPr")
    if docPr: docPr[0].set("descr", title)
    cap=doc.add_paragraph(); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER; cap.paragraph_format.space_after=Pt(4)
    r=cap.add_run(f"Figure {number}. {title}"); set_font(r,9.5,True)
    n=doc.add_paragraph(); n.alignment=WD_ALIGN_PARAGRAPH.CENTER; n.paragraph_format.space_after=Pt(6)
    r=n.add_run(note); set_font(r,8.5,False,True,MID)


# Footer and page numbers. Populate both odd/default and even parts identically.
for header_part in (section.header, section.even_page_header):
    hp=header_part.paragraphs[0]; hp.text=""
for footer_part in (section.footer, section.even_page_footer):
    footer_part.paragraphs[0].text=""
    ft=footer_part.add_table(rows=1, cols=1, width=Inches(6.5)); ft.autofit=False; ft.alignment=WD_TABLE_ALIGNMENT.CENTER
    cell=ft.rows[0].cells[0]; cell.width=Inches(6.5); set_cell_margins(cell, top=0, bottom=0, start=0, end=0)
    fp=cell.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER; fp.paragraph_format.space_after=Pt(0)
    r=fp.add_run("Confidential Working Specification  |  Page "); set_font(r,8.5,color=MID)
    add_field(fp,"PAGE"); r=fp.add_run(" of "); set_font(r,8.5,color=MID); add_field(fp,"NUMPAGES")

# Cover — editorial_cover pattern, monochrome override
p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(112); p.paragraph_format.space_after=Pt(16); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run("REUSABLE MARKET SPECIFICATION"); set_font(r,10,True,color=MID)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(10)
r=p.add_run("LLC Portfolio Identification\nand Mailing Research"); set_font(r,28,True)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(30)
r=p.add_run("Process requirements, decision rules, data model, and operating diagrams"); set_font(r,14,color=DARK)
p=doc.add_paragraph(); add_rule(p,"000000","12")
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(24)
r=p.add_run("Chicago / Cook County implementation baseline"); set_font(r,12,True)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run("Version 1.0  |  28 August 2026"); set_font(r,10,color=MID)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(80)
r=p.add_run("Core rule"); set_font(r,10,True,color=MID)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run("Group different LLC owners by the same normalized owner tax mailing address — never by the property address."); set_font(r,14,True)
doc.add_page_break()

doc.add_heading("1. Purpose and intended use", level=1)
doc.add_paragraph("This specification defines a repeatable process for discovering probable real-estate portfolios held through multiple differently named limited liability companies. It is designed to be reused market by market, beginning with Chicago and Cook County, and to produce a defensible mailing shortlist backed by parcel-level evidence.")
doc.add_heading("The business question", level=2)
doc.add_paragraph("Which owner tax mailing addresses receive records for two or more distinct LLC owners that collectively hold two or more distinct parcels, and what public entity evidence supports the conclusion that those LLCs may share a common controller or operating portfolio?")
doc.add_heading("Required interpretation", level=2)
add_list("The result is a probable common-controller or common-portfolio signal, not proof of beneficial ownership.")
add_list("A manager, registered agent, organizer, attorney, tax processor, or property manager is not automatically the beneficial owner.")
add_list("Every mailed candidate must remain traceable to the public source records and the transformations that created the cluster.")
doc.add_heading("Out of scope", level=2)
add_list("Filtering to multifamily, 2+ unit, commercial, or any other property class before the LLC-owner test.")
add_list("Grouping LLCs by the property or situs address.")
add_list("Treating a shared registered-agent address as conclusive proof of shared ownership.")
add_list("Naming a person as recipient without credible cross-entity support.")

doc.add_page_break()
doc.add_heading("2. Executive requirements", level=1)
rows=[
    ("R-01","Universe","Begin with every parcel in the selected geography."),
    ("R-02","LLC test","Keep records whose normalized legal owner name ends with LLC."),
    ("R-03","Key","Use normalized owner tax mailing address as the candidate-cluster key."),
    ("R-04","Threshold","Require 2+ distinct normalized LLC names and 2+ distinct parcels."),
    ("R-05","Evidence","Retain property address as inventory evidence only."),
    ("R-06","Review","Flag intermediaries and mass-service addresses; never silently remove them."),
    ("R-07","Enrichment","Use Secretary of State records after clustering to corroborate entities."),
    ("R-08","Outputs","Produce both cluster-level decisions and parcel-level audit evidence."),
]
add_table(["ID","Requirement","Mandatory rule"],rows,[900,1500,6960])
doc.add_page_break()

doc.add_heading("3. End-to-end workflow", level=1)
doc.add_paragraph("The process separates discovery, qualification, corroboration, and mailing preparation. This prevents entity-enrichment data from biasing the initial portfolio signal.")
add_figure(FIGURES[0],1,"End-to-end portfolio discovery workflow","The owner mailing address is normalized before grouping; Secretary of State evidence enters only after the threshold test.")
doc.add_page_break()

doc.add_heading("4. Source data requirements", level=1)
doc.add_heading("Minimum parcel-record fields", level=2)
rows=[
    ("Parcel identifier","Stable parcel/PIN key","Deduplication, evidence, joins","Required"),
    ("Legal owner name","Tax-roll or assessment owner","LLC suffix filter; entity identity","Required"),
    ("Owner mailing name","Addressee on tax record","Recipient candidate; QA","Preferred"),
    ("Owner mailing address","Street, unit, city, state, ZIP","Primary clustering key","Required"),
    ("Property/situs address","Location of owned parcel","Inventory and evidence only","Required"),
    ("Source date/version","Assessment roll vintage","Reproducibility","Required"),
]
add_table(["Field","Meaning","Use","Status"],rows,[1900,2300,3860,1300])
doc.add_heading("Chicago / Cook County baseline mapping", level=2)
rows=[
    ("owner_address_name","Legal owner name","Normalize; test suffix LLC"),
    ("mail_address_full","Owner tax mailing street/unit","Normalize; cluster key"),
    ("mail_address_city_name","Mailing city","Cluster-key component"),
    ("mail_address_state","Mailing state","Cluster-key component"),
    ("mail_address_zipcode_1","Mailing ZIP","Cluster-key component"),
    ("prop_address_full","Physical property address","Output/evidence only"),
    ("pin","Parcel identifier","Distinct parcel count and audit key"),
]
add_table(["Cook County field","Role","Processing rule"],rows,[2400,2500,4460])

doc.add_page_break()
doc.add_heading("5. LLC owner selection", level=1)
doc.add_paragraph("The LLC test applies to the normalized legal owner name. It is intentionally broad and does not depend on property type, unit count, assessed use, or building class.")
doc.add_heading("Required owner-name normalization", level=2)
add_list("Convert to uppercase and trim leading/trailing whitespace.")
add_list("Collapse repeated internal whitespace.")
add_list("Standardize terminal variants such as L.L.C., L L C, and punctuation-separated forms to LLC.")
add_list("Preserve the original source owner name alongside the normalized value.")
add_list("Pass only when the normalized owner name ends with the standalone suffix LLC.")
doc.add_heading("Examples", level=2)
add_table(["Source owner name","Normalized owner name","Keep?"],[("Lake View Owner, L.L.C.","LAKE VIEW OWNER LLC","Yes"),("West Loop Holdings LLC","WEST LOOP HOLDINGS LLC","Yes"),("LLC Management Services Inc.","LLC MANAGEMENT SERVICES INC","No — does not end in LLC"),("John and Mary Smith","JOHN AND MARY SMITH","No")],[3500,3860,2000])
doc.add_page_break()

doc.add_heading("6. Correct clustering logic", level=1)
add_figure(FIGURES[1],2,"Correct grouping key versus the wrong key","Different property addresses are expected. Their shared owner mailing address is the candidate portfolio signal.")
doc.add_heading("Non-negotiable rule", level=2)
doc.add_paragraph("The physical property address must never be used as the initial grouping key. It identifies the asset, not the place where the owner receives tax mail.")
doc.add_page_break()

doc.add_heading("7. Mailing-address normalization", level=1)
doc.add_paragraph("Normalization must improve match consistency without erasing meaningful unit, suite, or postal information. Store both the source value and each normalized component.")
rows=[
    ("Case and whitespace","Uppercase; trim; collapse repeated spaces"),
    ("Punctuation","Remove non-semantic punctuation; preserve unit meaning"),
    ("Street suffixes","Standardize common equivalents, e.g., STREET→ST, AVENUE→AVE"),
    ("Directionals","Standardize NORTH→N, SOUTH→S, EAST→E, WEST→W when unambiguous"),
    ("Units","Standardize SUITE/STE and APARTMENT/APT; do not drop the unit"),
    ("City/state","Normalize spelling and two-letter state abbreviation"),
    ("ZIP","Use five-digit ZIP as the default; preserve ZIP+4 separately"),
    ("PO boxes","Standardize PO BOX; retain as a valid mailing address"),
    ("Missing/invalid","Do not cluster; route to QA/exclusion log"),
]
add_table(["Component","Rule"],rows,[1900,7460])
doc.add_heading("Recommended cluster key", level=2)
doc.add_paragraph("normalized_street_line_1 + normalized_street_line_2 + normalized_city + normalized_state + normalized_zip5")
doc.add_paragraph("Exact normalized matching is the production baseline. Fuzzy or probabilistic address matching, if later introduced, must be a separate review layer with an explainable score and no silent merges.")

doc.add_heading("8. Data relationship model", level=1)
add_figure(FIGURES[2],3,"Data relationship model","The address hub creates a candidate cluster; parcel records prove holdings; entity records corroborate after discovery.")
doc.add_page_break()

doc.add_heading("9. Cluster construction and qualification", level=1)
doc.add_heading("Algorithm", level=2)
steps=[
    "Load the complete parcel universe for the target geography and source vintage.",
    "Normalize the legal owner name and retain rows where it ends with LLC.",
    "Normalize the owner tax mailing address and quarantine missing or invalid values.",
    "Group records by the exact normalized owner mailing address.",
    "Within each address group, count distinct normalized LLC names and distinct parcel identifiers.",
    "Qualify groups with at least two distinct LLC names and at least two distinct parcels.",
    "Apply intermediary and mass-service-address flags without deleting the group.",
    "Enrich each distinct LLC with Secretary of State evidence and assign confidence.",
    "Create the cluster summary, property evidence, mailing shortlist, and QA logs.",
]
add_numbered(steps)
doc.add_heading("Formal acceptance expression", level=2)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(8); p.paragraph_format.space_after=Pt(8)
r=p.add_run("normalized_owner_mailing_address  →  2+ distinct normalized LLC names  →  2+ distinct parcels"); set_font(r,12,True)
doc.add_heading("Distinctness and deduplication", level=2)
add_list("A parcel is distinct by stable parcel/PIN identifier, not by formatted property address.")
add_list("An LLC is distinct by normalized legal name within the parcel source; entity identifiers may later refine this.")
add_list("Duplicate source rows must not inflate parcel or LLC counts.")
add_list("One LLC owning several parcels does not satisfy the multi-LLC requirement by itself.")

doc.add_heading("10. Qualification and routing", level=1)
add_figure(FIGURES[3],4,"Cluster qualification and routing decision tree","A service-address flag changes the review route; it does not erase the candidate.")
doc.add_page_break()

doc.add_heading("11. Intermediary and false-positive controls", level=1)
doc.add_paragraph("Shared addresses may represent a common controller, but they may also belong to professional intermediaries. These cases must be visible, explainable, and reviewable.")
rows=[
    ("Registered agent","Address reused across unrelated entities; agent name present","Flag; compare managers/principals and address scale"),
    ("Law firm","Firm name, attorney suite, many unrelated clients","Flag for manual review"),
    ("Tax processor/accountant","Tax-service addressee or very high entity volume","Flag; seek corroborating manager evidence"),
    ("Property manager","Management company receives bills for many owners","Flag; compare owner/entity records"),
    ("Mass service/virtual office","Address links unusually many LLCs across broad industries","Flag; lower confidence absent corroboration"),
    ("Property address reused as mail","Mailing address equals one situs address","Flag; do not assume owner residence or control"),
]
add_table(["Pattern","Observable signal","Required treatment"],rows,[1700,3850,3810])
doc.add_heading("Scale-based review", level=2)
doc.add_paragraph("The project should calculate the number of distinct LLCs, parcels, owner names, and industry/entity patterns per mailing address. High-volume addresses are not automatically invalid, but require stronger corroboration and often manual review.")

doc.add_page_break()
doc.add_heading("12. Secretary of State corroboration", level=1)
doc.add_paragraph("Illinois Secretary of State data is used after parcel clustering. It should validate entity identity and reveal repeated managers, principals, registered agents, or entity addresses across the LLCs in a candidate cluster.")
doc.add_heading("Recommended entity fields", level=2)
add_list("Entity file number, exact legal name, status, formation date, jurisdiction, and entity address.")
add_list("Registered-agent name and address.")
add_list("Manager/member or principal names and addresses where publicly available.")
add_list("Annual-report or series-LLC relationships where applicable.")
doc.add_heading("Match hierarchy", level=2)
add_numbered(["Exact normalized legal name plus jurisdiction/status.","Exact legal name plus corroborating address or file number.","Fuzzy name candidates only as manual-review leads; never as silent matches."])
doc.add_heading("Interpretation guardrails", level=2)
add_list("Manager does not necessarily mean beneficial owner.")
add_list("Registered-agent matches alone are weak control evidence.")
add_list("Repeated credible manager/principal names or addresses across multiple LLCs materially strengthen the portfolio hypothesis.")

doc.add_heading("13. Confidence framework", level=1)
rows=[
    ("High","Shared owner mailing address; repeated credible manager/principal or entity-address support across LLCs; no strong intermediary flag","Eligible for mailing shortlist after final QA"),
    ("Medium","Shared owner mailing address; active entity matches; limited direct manager proof; no strong contradiction","Eligible with conservative recipient naming"),
    ("Low / review","Agent, law firm, tax processor, property manager, mass-mailing address, situs reuse, ambiguous entity match, or conflicting evidence","Manual review before any mailing"),
]
add_table(["Level","Evidence pattern","Routing"],rows,[1500,5100,2760])
doc.add_heading("Recipient naming", level=2)
add_list("Use a person’s name only when the same credible person is supported across multiple LLCs in the cluster.")
add_list("Otherwise use the tax-roll mailing name when suitable.")
add_list("If no defensible recipient name exists, use “Property Owner” rather than inventing a person.")
add_list("Retain the LLC names and property list in the evidence file even when the outbound card uses a generalized addressee.")

doc.add_heading("14. Required output package", level=1)
add_figure(FIGURES[4],5,"Required output package","The mailing shortlist is a downstream view, not a substitute for cluster and parcel evidence.")
doc.add_page_break()

doc.add_heading("15. Output schemas", level=1)
doc.add_heading("A. Cluster summary — one row per normalized owner mailing address", level=2)
add_table(["Field","Definition"],[("cluster_id","Stable project-generated identifier"),("normalized_owner_mailing_address","Exact grouping key"),("source_owner_mailing_addresses","Observed source variants"),("distinct_llc_count","Count of normalized LLC names"),("distinct_parcel_count","Count of parcel/PIN values"),("llc_names","All source and normalized LLC names"),("property_geography","Cities/neighborhoods/ZIPs represented"),("intermediary_flags","All triggered review flags"),("confidence_level","High, medium, or low/review"),("decision_reason","Human-readable rationale")],[3000,6360])
doc.add_heading("B. Property evidence — one row per parcel-owner record", level=2)
add_table(["Field","Definition"],[("cluster_id","Foreign key to cluster summary"),("parcel_id / PIN","Stable parcel identifier"),("source_owner_name","Owner text as published"),("normalized_llc_name","Normalized distinct-LLC key"),("property_address","Situs/inventory address; never clustering key"),("owner_mailing_name","Tax-roll addressee"),("source_owner_mailing_address","Published mailing address"),("normalized_owner_mailing_address","Cluster key"),("source_version","Dataset vintage and retrieval date")],[3000,6360])
doc.add_heading("C. Entity enrichment and mailing shortlist", level=2)
add_table(["Artifact","Minimum fields"],[("Entity enrichment","cluster_id, LLC name, entity/file ID, status, entity address, agent, managers/principals, match method, source date"),("Mailing shortlist","cluster_id, recipient, deliverable mailing address, LLC count, parcel count, confidence, review status, rationale"),("QA/exclusion log","record/cluster ID, rule triggered, reason, source values, reviewer, disposition, timestamp")],[2300,7060])

doc.add_heading("16. Quality assurance and acceptance tests", level=1)
doc.add_heading("Record-level tests", level=2)
for x in ["Every included owner name passes the normalized terminal LLC test.","Every included parcel has a stable parcel/PIN key.","Every clustered record has a nonblank normalized owner mailing address.","Every property address is stored separately from the owner mailing address."]: add_list(x)
doc.add_heading("Cluster-level tests", level=2)
for x in ["Every qualified cluster contains 2+ distinct normalized LLC names.","Every qualified cluster contains 2+ distinct parcel identifiers.","No duplicate source row inflates either count.","All intermediary flags are retained with the cluster.","Confidence and recipient decisions have a written rationale."]: add_list(x)
doc.add_heading("Auditability tests", level=2)
for x in ["A reviewer can reproduce the group from the normalized address and property evidence file.","Original source fields are retained beside normalized fields.","Dataset vintage, retrieval date, and processing version are recorded.","Manual overrides identify reviewer, timestamp, prior value, new value, and reason."]: add_list(x)
doc.add_heading("Acceptance rule", level=2)
doc.add_paragraph("The process is accepted only when 100% of qualified clusters satisfy the two-LLC/two-parcel threshold, 100% of mailed records link to parcel-level evidence, and no property/situs address is used as a clustering key.")

doc.add_heading("17. Market adaptation checklist", level=1)
add_numbered([
    "Define the target geography and obtain the complete parcel universe.",
    "Confirm which source fields contain legal owner name, owner mailing name/address, property address, and parcel ID.",
    "Document access method, terms, refresh cadence, and dataset vintage.",
    "Map local LLC suffix variants and address conventions into the normalization rules.",
    "Locate the relevant Secretary of State entity and manager/agent records.",
    "Profile high-volume mailing addresses and build local intermediary indicators.",
    "Run threshold and QA tests before entity enrichment or mailing selection.",
    "Perform a documented sample review across high-, medium-, and review-routed clusters.",
    "Freeze the output schema, processing version, and source snapshot for reproducibility.",
])
doc.add_heading("Market configuration record", level=2)
add_table(["Configuration item","Required entry"],[("Market / MSA","Name and geographic boundaries"),("Parcel authority","Agency, dataset, access method, refresh date"),("Entity authority","Secretary of State source and refresh date"),("Field mapping","Local field → canonical field"),("Normalization version","Named ruleset/version"),("Thresholds","Default: 2+ LLCs and 2+ parcels"),("Known intermediaries","Local firms, agents, processors, virtual offices"),("QA owner","Reviewer and approval date")],[3000,6360])

doc.add_page_break()
doc.add_heading("18. Mailing preparation and operating safeguards", level=1)
doc.add_paragraph("Mailing preparation begins only after cluster qualification, entity review, and recipient routing. The research dataset and the outbound mailing list should remain separate artifacts so later suppression or compliance decisions do not alter the underlying evidence.")
add_list("Validate address deliverability and standardization through an authorized postal process before printing.")
add_list("Maintain suppression lists for returned mail, opt-outs, do-not-contact decisions, and duplicate households/addresses.")
add_list("Do not include sensitive personal information on the card or in exposed tracking parameters.")
add_list("Use public-record information only for the documented business purpose and review applicable federal, state, and local solicitation rules before launch.")
add_list("Retain the research basis, mailing version, and campaign date so each card can be traced to an approved shortlist record.")
doc.add_heading("Pre-mail release gate", level=2)
add_table(["Gate","Required approval"],[("Data","Cluster and parcel evidence passed all acceptance tests"),("Identity","Recipient name and confidence treatment follow this specification"),("Address","Deliverability check completed; suppressions applied"),("Content","Card copy approved; no unsupported ownership claims"),("Compliance","Campaign reviewed for applicable solicitation/privacy requirements"),("Archive","Source snapshot, shortlist version, and approval log retained")],[1900,7460])

doc.add_page_break()
doc.add_heading("19. Chicago / Cook County implementation baseline", level=1)
doc.add_paragraph("Chicago is the first implementation market under this reusable specification. Cook County parcel/assessment records provide the owner, mailing, situs, and PIN elements needed for discovery. Illinois Secretary of State entity records provide the post-cluster corroboration layer.")
doc.add_heading("Implementation sequence", level=2)
add_numbered(["Acquire and version the countywide parcel source.","Apply the LLC suffix test to the legal owner field.","Normalize mail_address_full plus city, state, and ZIP into the owner mailing key.","Group countywide by that owner mailing key and apply the two-LLC/two-parcel threshold.","Profile and flag likely intermediaries and service addresses.","Match qualifying LLCs to Illinois entity, agent, annual-report, manager, and series records where available.","Review confidence, assign recipient treatment, and publish the five-output package."])
doc.add_heading("Success measure", level=2)
doc.add_paragraph("The Chicago research phase is ready to trigger when the source snapshot, field mapping, normalization rules, intermediary review method, entity-source access, output locations, and QA reviewer are documented and testable against this specification.")

doc.add_page_break()
doc.add_heading("20. Definitions and version control", level=1)
add_table(["Term","Definition"],[("Owner mailing address","Address where the parcel authority sends owner/tax correspondence; the clustering key"),("Property/situs address","Physical location of the parcel; inventory evidence only"),("Candidate cluster","Records sharing one normalized owner mailing address before final confidence review"),("Qualified cluster","Candidate meeting 2+ LLC and 2+ parcel thresholds"),("Intermediary flag","Signal that the address may belong to a professional service provider"),("Corroboration","Independent entity evidence supporting a common-control hypothesis"),("Probable portfolio","Qualified and reviewed cluster; not a legal conclusion of beneficial ownership")],[2600,6760])
doc.add_heading("Document control", level=2)
add_table(["Version","Date","Status","Change"],[("1.0","28 Aug 2026","Baseline","Initial reusable specification; Chicago/Cook County implementation mapping")],[1100,1700,1600,4960])
doc.add_paragraph("Future changes should preserve the core grouping rule unless a formally approved version explicitly replaces it: group different LLC owners by normalized owner tax mailing address, not by property address.")

# Keep rows from splitting when practical and ensure all text is monochrome.
for table in doc.tables:
    for row in table.rows:
        trPr=row._tr.get_or_add_trPr(); cant=OxmlElement("w:cantSplit"); trPr.append(cant)
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(3); p.paragraph_format.line_spacing=1.05

# Ask Word/LibreOffice to update fields on open.
settings = doc.settings._element
update = OxmlElement("w:updateFields"); update.set(qn("w:val"), "true"); settings.append(update)

doc.core_properties.title = "LLC Portfolio Identification and Mailing Research — Process Requirements"
doc.core_properties.subject = "Reusable requirements specification with Chicago/Cook County baseline"
doc.core_properties.author = "OpenAI Codex"
doc.core_properties.keywords = "LLC, parcel, owner mailing address, portfolio, Chicago, Cook County"
doc.save(OUT)
print(OUT)
