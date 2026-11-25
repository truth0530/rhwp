#!/usr/bin/env python3
"""Build samples/group-child-affine-textbox.hwpx (synthetic).

Takes samples/tac-host-spacing.hwpx as the package template and replaces its
body with two paragraphs:

1. A group (hp:container) whose child is a rounded rectangle with a text box
   ("묶음 안 글상자"). The child declares curSz 0x0 and a renderingInfo with
   two scale/rotation pairs. The second pair has a non-zero rotation, so the
   composed matrix keeps small off-diagonal terms (render_b, render_c). This is
   the form Hancom writes for a group child that was rotated and then scaled
   with the group.
2. The same rectangle as a top-level object ("묶음 밖 글상자"), for comparison.

The text is neutral and contains no personal or institutional data.

Usage: python3 tools/fixture_generators/build_group_child_affine_textbox_fixture.py
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "samples/tac-host-spacing.hwpx"
OUT = ROOT / "samples/group-child-affine-textbox.hwpx"

ORG_W, ORG_H = 7668, 2232
IDENT = (1, 0, 0, 0, 1, 0)
SCA2 = (4.434896, 0.862057, -8271.399414, -2.595511, 1.438715, 6027.226074)
ROT2 = (0.857167, -0.515038, 0, 0.515038, 0.857167, 0)


def compose(a, b):
    return (
        a[0] * b[0] + a[1] * b[3],
        a[0] * b[1] + a[1] * b[4],
        a[0] * b[2] + a[1] * b[5] + a[2],
        a[3] * b[0] + a[4] * b[3],
        a[3] * b[1] + a[4] * b[4],
        a[3] * b[2] + a[4] * b[5] + a[5],
    )


def bbox(m, w, h):
    pts = [(0, 0), (w, 0), (w, h), (0, h)]
    xs = [m[0] * x + m[1] * y + m[2] for x, y in pts]
    ys = [m[3] * x + m[4] * y + m[5] for x, y in pts]
    return min(xs), min(ys), max(xs), max(ys)


def mat(tag, m):
    vals = " ".join(f'e{i + 1}="{v:g}"' for i, v in enumerate(m))
    return f"<hc:{tag} {vals}/>"


def text_para(text, width):
    return (
        '<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="0"><hp:t>{text}</hp:t></hp:run>'
        '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" textheight="1000" '
        f'baseline="850" spacing="600" horzpos="0" horzsize="{width}" flags="393216"/>'
        "</hp:linesegarray></hp:p>"
    )


def rect(instid, text, rendering, cur, last_width, group_level, tail=""):
    return (
        '<hp:rect id="0" zOrder="1" numberingType="NONE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" '
        f'lock="0" dropcapstyle="None" href="" groupLevel="{group_level}" instid="{instid}" ratio="20">'
        f'<hp:offset x="0" y="0"/><hp:orgSz width="{ORG_W}" height="{ORG_H}"/>'
        f'<hp:curSz width="{cur[0]}" height="{cur[1]}"/><hp:flip horizontal="0" vertical="0"/>'
        f'<hp:rotationInfo angle="0" centerX="{ORG_W // 2}" centerY="{ORG_H // 2}" rotateimage="1"/>'
        f"<hp:renderingInfo>{rendering}</hp:renderingInfo>"
        '<hp:lineShape color="#000000" width="33" style="SOLID" endCap="FLAT" headStyle="NORMAL" '
        'tailStyle="NORMAL" headfill="1" tailfill="1" headSz="MEDIUM_MEDIUM" tailSz="MEDIUM_MEDIUM" '
        'outlineStyle="NORMAL" alpha="0"/>'
        '<hp:fillBrush><hc:winBrush faceColor="#E5E5E5" hatchColor="#000000" alpha="0"/></hp:fillBrush>'
        '<hp:shadow type="NONE" color="#B2B2B2" offsetX="0" offsetY="0" alpha="0"/>'
        f'<hp:drawText lastWidth="{last_width}" name="" editable="0">'
        '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="TOP" linkListIDRef="0" '
        'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
        f"{text_para(text, last_width)}</hp:subList>"
        '<hp:textMargin left="283" right="283" top="283" bottom="283"/></hp:drawText>'
        f'<hc:pt0 x="0" y="0"/><hc:pt1 x="{ORG_W}" y="0"/>'
        f'<hc:pt2 x="{ORG_W}" y="{ORG_H}"/><hc:pt3 x="0" y="{ORG_H}"/>'
        f"{tail}</hp:rect>"
    )


def build_section(template_section):
    # Child matrix: trans x (rot1 x sca1) x (rot2 x sca2), shifted to the group origin.
    m = compose(compose(compose(IDENT, IDENT), ROT2), SCA2)
    x0, y0, x1, y1 = bbox(m, ORG_W, ORG_H)
    trans = (1, 0, round(-x0 + 1000), 0, 1, round(-y0 + 1000))
    m = compose(compose(compose(trans, IDENT), ROT2), SCA2)
    _, _, gx1, gy1 = bbox(m, ORG_W, ORG_H)
    group_w, group_h = round(gx1 + 1000), round(gy1 + 1000)
    child_w = round((m[0] ** 2 + m[3] ** 2) ** 0.5 * ORG_W)

    child_rendering = (
        mat("transMatrix", trans)
        + mat("scaMatrix", IDENT)
        + mat("rotMatrix", IDENT)
        + mat("scaMatrix", SCA2)
        + mat("rotMatrix", ROT2)
    )
    child = rect(2001, "묶음 안 글상자", child_rendering, (0, 0), child_w, 1)
    ident_rendering = mat("transMatrix", IDENT) + mat("scaMatrix", IDENT) + mat("rotMatrix", IDENT)
    group = (
        '<hp:container id="0" zOrder="0" numberingType="NONE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" '
        'lock="0" dropcapstyle="None" href="" groupLevel="0" instid="1000">'
        f'<hp:sz width="{group_w}" height="{group_h}" protect="0"/>'
        '<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" '
        'vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
        '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:offset x="0" y="0"/><hp:orgSz width="{group_w}" height="{group_h}"/>'
        f'<hp:curSz width="{group_w}" height="{group_h}"/><hp:flip horizontal="0" vertical="0"/>'
        f'<hp:rotationInfo angle="0" centerX="{group_w // 2}" centerY="{group_h // 2}" rotateimage="1"/>'
        f"<hp:renderingInfo>{ident_rendering}</hp:renderingInfo>"
        f"{child}</hp:container>"
    )

    top_w, top_h = child_w, ORG_H * 2
    top_rendering = mat("transMatrix", IDENT) + mat("scaMatrix", (top_w / ORG_W, 0, 0, 0, 2, 0)) + mat(
        "rotMatrix", IDENT
    )
    top_tail = (
        f'<hp:sz width="{top_w}" widthRelTo="ABSOLUTE" height="{top_h}" heightRelTo="ABSOLUTE" protect="0"/>'
        '<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" '
        'vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="1000"/>'
        '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
    )
    top = rect(3001, "묶음 밖 글상자", top_rendering, (top_w, top_h), top_w, 0, top_tail)

    head = template_section[: template_section.index("<hp:bookmark")]
    return (
        head
        + f'<hp:container_placeholder/></hp:run><hp:linesegarray><hp:lineseg textpos="0" vertpos="0" '
        f'vertsize="{group_h}" textheight="{group_h}" baseline="{group_h}" spacing="600" horzpos="0" '
        'horzsize="48188" flags="393216"/></hp:linesegarray></hp:p>'
        '<hp:p id="3" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="0">{top}</hp:run><hp:linesegarray><hp:lineseg textpos="0" '
        f'vertpos="{group_h + 600}" vertsize="{top_h}" textheight="{top_h}" baseline="{top_h}" '
        'spacing="600" horzpos="0" horzsize="48188" flags="393216"/></hp:linesegarray></hp:p>'
        "</hs:sec>"
    ).replace("<hp:container_placeholder/>", group)


def main():
    with zipfile.ZipFile(TEMPLATE) as src, zipfile.ZipFile(OUT, "w") as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "Contents/section0.xml":
                data = build_section(data.decode("utf-8")).encode("utf-8")
            method = zipfile.ZIP_STORED if info.filename == "mimetype" else zipfile.ZIP_DEFLATED
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = method
            dst.writestr(zi, data)
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
