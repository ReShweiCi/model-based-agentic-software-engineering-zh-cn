#!/usr/bin/env python3
"""build_zh_epub.py — 构建并校验两本中文译本的通用兼容 EPUB3 电子书。

从 translations/zh-CN/ 下与 PDF 完全同源的 Typst 源码出发（单一事实来源，零漂移）：
  1. 使用 Typst 0.15.1 渲染第 1 页带中文标题的高清封面 PNG，经 Pillow 压成 cover.jpg；
  2. 使用 Typst 0.15.1 (`--features html --format html --input target=epub`) 导出整书语义 HTML
     （块级数学公式经 Typst `html.frame` 渲染为完整矢量路径 SVG，交叉引用自动按章编号）；
  3. 使用 `rsvg-convert` + Pillow 将全部汉化插图 SVG 与块级公式 SVG 统一光栅化为高分辨率 PNG
     嵌入 `OEBPS/assets/`，彻底解决微信读书 / Kindle / 静读天下等阅读器不显示 SVG 或缺字问题；
  4. 将全部行内 MathML 无损转换为通用 HTML 语义标签（标准 ASCII + `<em>`/`<sub>`/`<sup>` +
     常规 Unicode 数学运算符），彻底消除不支持 MathML 或数学斜体字体的阅读器中文本隐身问题；
  5. 优化表格结构（表标题置顶、标红“表 X.Y”标签、包裹 `.table-wrap`、允许长表跨页）、
     拆分为逐章 XHTML5、将脚注归属章末支持原生弹窗、重写跨章锚点、生成两级目录并严格校验。

依赖：Python 3 标准库 + Pillow + typst (0.15.1+) + librsvg2-bin (`rsvg-convert`) + fonts-noto-cjk。

用法：
  python3 translations/zh-CN/scripts/build_zh_epub.py --out-dir dist
  python3 translations/zh-CN/scripts/build_zh_epub.py --book mage --out-dir dist
  python3 translations/zh-CN/scripts/build_zh_epub.py --check dist/mage-book-zh.epub
"""
from __future__ import annotations

import argparse
import base64
from html.parser import HTMLParser
import io
import json
import pathlib
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ZH_ROOT = SCRIPT_DIR.parent  # translations/zh-CN
REPO_ROOT = ZH_ROOT.parent.parent
EPUB_CSS = ZH_ROOT / "epub" / "epub-zh.css"

XHTML_NS = "http://www.w3.org/1999/xhtml"
EPUB_NS = "http://www.idpf.org/2007/ops"
OPF_NS = "http://www.idpf.org/2007/opf"

VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img",
    "input", "link", "meta", "param", "source", "track", "wbr",
})

BOOKS = {
    "se-handbook": {
        "typ_entry": ZH_ROOT / "se-handbook" / "book-zh.typ",
        "out_name": "software-engineering-handbook-zh.epub",
        "identifier": "urn:uuid:7e9a3d10-4b2c-4f8a-9c51-5e48616e6462",
        "title": "软件工程手册：一种判断与决策的方法",
        "subtitle": "The Software Engineering Handbook: A Judgment and Decision-Making Approach（非官方中文译本）",
        "author": "James C. Davis",
        "date": "2026-09-12",
        "modified": "2026-11-25",
        "rights": "© James C. Davis, 2026–present (MIT License); 非官方社区中文译本",
        "description": "《软件工程手册：一种判断与决策的方法》完整中文版，涵盖软件工程、流程、团队协作、工程知识、需求、规约、架构、设计、验证、研发与面向失败的工程。",
    },
    "mage": {
        "typ_entry": ZH_ROOT / "mage" / "book-zh.typ",
        "out_name": "mage-book-zh.epub",
        "identifier": "urn:uuid:7e9a3d10-4b2c-4f8a-9c51-4d4147457a68",
        "title": "基于模型的智能体工程（MAGE）：软件工程案例研究",
        "subtitle": "Model-Based Agentic Engineering: A Case Study in Software Engineering（非官方中文译本）",
        "author": "James C. Davis",
        "date": "2026-07-22",
        "modified": "2026-11-25",
        "rights": "© James C. Davis, 2026–present (MIT License); 非官方社区中文译本",
        "description": "《基于模型的智能体工程（MAGE）：软件工程案例研究》完整中文版，包含全 7 章、结语、附录 A 工程蓝图、附录 B 实践指南、后记以及英文索引与参考文献。",
    },
}


# ── 轻量级 HTML5 -> 节点树解析器（纯标准库） ────────────────────────────────────────────────────


class Node:
    __slots__ = ("tag", "attrs", "children", "text")

    def __init__(self, tag: str | None = None, attrs: dict[str, str] | None = None, text: str = ""):
        self.tag = tag
        self.attrs = attrs if attrs is not None else {}
        self.children: list[Node] = []
        self.text = text

    def plain_text(self) -> str:
        if self.tag is None:
            return self.text
        return "".join(c.plain_text() for c in self.children)

    def iter_elements(self):
        if self.tag is not None:
            yield self
            for c in self.children:
                yield from c.iter_elements()

    def clone(self) -> "Node":
        n = Node(self.tag, dict(self.attrs), self.text)
        n.children = [c.clone() for c in self.children]
        return n


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack: list[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_l = tag.lower()
        attr_dict = {k: ("" if v is None else v) for k, v in attrs}
        node = Node(tag_l, attr_dict)
        self.stack[-1].children.append(node)
        if tag_l not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_l = tag.lower()
        attr_dict = {k: ("" if v is None else v) for k, v in attrs}
        self.stack[-1].children.append(Node(tag_l, attr_dict))

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag_l:
                del self.stack[i:]
                break

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(Node(None, None, data))


def _xml_escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _xml_escape_attr(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def serialize_xhtml(node: Node) -> str:
    if node.tag is None:
        return _xml_escape_text(node.text)
    tag = node.tag
    attrs = dict(node.attrs)
    if tag in ("ul", "ol") and attrs.get("style") == "list-style-type: none":
        attrs.pop("style", None)
    attr_str = "".join(f' {k}="{_xml_escape_attr(v)}"' for k, v in attrs.items())
    if tag in VOID_TAGS:
        return f"<{tag}{attr_str}/>"
    inner = "".join(serialize_xhtml(c) for c in node.children)
    return f"<{tag}{attr_str}>{inner}</{tag}>"


# ── 行内 MathML -> 通用纯 HTML 语义转换（兼容所有无 MathML/无数学字体的阅读器） ─────────────────

_SPACED_OPS = frozenset({
    "=", "≠", "≈", "≤", "≥", "<", ">", "+", "−", "-", "×", "·",
    "∧", "∨", "⇒", "⇔", "→", "←", "↔", "⇝", "⊢", "⊨",
    "⊆", "⊂", "⊇", "⊃", "∈", "∉", "∩", "∪", "|", "∣",
})


def _norm_math_chars(s: str) -> str:
    out = []
    for ch in s:
        cp = ord(ch)
        if 0x1D400 <= cp <= 0x1D7FF:
            out.append(unicodedata.normalize("NFKC", ch))
        else:
            out.append(ch)
    return "".join(out)


def _mathml_children_to_html(node: Node, compact: bool = False) -> list[Node]:
    tag = node.tag
    if tag is None:
        txt = _norm_math_chars(node.text)
        return [Node(None, None, txt)] if txt else []

    if tag in ("math", "mrow", "mstyle", "mpadded"):
        res: list[Node] = []
        for c in node.children:
            res.extend(_mathml_children_to_html(c, compact=compact))
        return res

    if tag == "mi":
        txt = _norm_math_chars(node.plain_text()).strip()
        if not txt:
            return []
        if len(txt) == 1 and txt.isalpha():
            em = Node("em")
            em.children.append(Node(None, None, txt))
            return [em]
        return [Node(None, None, txt)]

    if tag in ("mn", "mtext"):
        txt = _norm_math_chars(node.plain_text())
        return [Node(None, None, txt)] if txt else []

    if tag == "mo":
        txt = _norm_math_chars(node.plain_text()).strip()
        if not txt:
            return []
        if not compact and txt in _SPACED_OPS:
            return [Node(None, None, f" {txt} ")]
        if not compact and txt == ",":
            return [Node(None, None, ", ")]
        return [Node(None, None, txt)]

    if tag == "mspace":
        return [Node(None, None, " ")]

    if tag == "msub" and len(node.children) >= 2:
        base = _mathml_children_to_html(node.children[0], compact=compact)
        sub = Node("sub")
        sub.children.extend(_mathml_children_to_html(node.children[1], compact=True))
        return base + [sub]

    if tag == "msup" and len(node.children) >= 2:
        base = _mathml_children_to_html(node.children[0], compact=compact)
        sup = Node("sup")
        sup.children.extend(_mathml_children_to_html(node.children[1], compact=True))
        return base + [sup]

    if tag == "msubsup" and len(node.children) >= 3:
        base = _mathml_children_to_html(node.children[0], compact=compact)
        sub = Node("sub")
        sub.children.extend(_mathml_children_to_html(node.children[1], compact=True))
        sup = Node("sup")
        sup.children.extend(_mathml_children_to_html(node.children[2], compact=True))
        return base + [sub, sup]

    if tag == "mfrac" and len(node.children) >= 2:
        num = _mathml_children_to_html(node.children[0], compact=True)
        den = _mathml_children_to_html(node.children[1], compact=True)
        return num + [Node(None, None, "/")] + den

    # 兜底：保留全部规范化纯文本
    txt = _norm_math_chars(node.plain_text())
    return [Node(None, None, txt)] if txt else []


def convert_inline_math_in_tree(root_nodes: list[Node]) -> None:
    def _walk(parent_children: list[Node]) -> None:
        for i, child in enumerate(parent_children):
            if child.tag == "math":
                span = Node("span", {"class": "math-inline"})
                span.children = _mathml_children_to_html(child)
                # 清理首尾多余空格（例如孤立箭头 $\rightarrow$）
                if span.children and span.children[0].tag is None:
                    span.children[0].text = span.children[0].text.lstrip()
                if span.children and span.children[-1].tag is None:
                    span.children[-1].text = span.children[-1].text.rstrip()
                parent_children[i] = span
            elif child.tag is not None:
                _walk(child.children)

    _walk(root_nodes)


# ── 工具定位、Typst 与 rsvg-convert 图像光栅化 ──────────────────────────────────────────────────


def find_bin(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    candidate = pathlib.Path.home() / ".local" / "bin" / name
    if candidate.is_file():
        return str(candidate)
    raise SystemExit(f"ERROR: required binary '{name}' not found in PATH")


def run_typst(args: list[str]) -> None:
    cmd = [find_bin("typst"), *args]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stdout)
        sys.stderr.write(res.stderr)
        raise SystemExit(f"ERROR: typst failed (rc={res.returncode}): {' '.join(cmd)}")


def render_cover_jpg(typ_entry: pathlib.Path, work_dir: pathlib.Path) -> bytes:
    """用 Typst 编译第 1 页带中文标题封面 PNG，再用 Pillow 压缩为高分辨率 JPEG。"""
    from PIL import Image

    cover_png = work_dir / "cover.png"
    run_typst([
        "compile",
        "--root", str(ZH_ROOT),
        "--format", "png",
        "--pages", "1",
        "--ppi", "180",
        str(typ_entry),
        str(cover_png),
    ])
    cover_jpg = work_dir / "cover.jpg"
    Image.open(cover_png).convert("RGB").save(cover_jpg, "JPEG", quality=88, optimize=True)
    return cover_jpg.read_bytes()


def svg_to_png_bytes(svg_bytes: bytes, *, target_width: int | None = 1500, zoom: float | None = None) -> bytes:
    """使用 rsvg-convert 将 SVG（含中文思源字体或 Typst 矢量路径公式）光栅化为高清优化 PNG。"""
    from PIL import Image

    rsvg = find_bin("rsvg-convert")
    cmd = [rsvg, "--format=png", "--background-color=#fdfcf9"]
    if zoom is not None:
        cmd.extend(["--zoom", str(zoom)])
    elif target_width is not None:
        # 读取 SVG 原始 viewBox/width，避免小图被过度放大或大图超宽
        svg_txt = svg_bytes.decode("utf-8", errors="ignore")
        vb_m = re.search(r'viewBox="[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"', svg_txt)
        w_m = re.search(r'\bwidth="([\d.]+)(?:px)?"', svg_txt)
        nat_w = float(vb_m.group(1)) if vb_m else (float(w_m.group(1)) if w_m else 720.0)
        render_w = int(min(target_width, max(960, nat_w * 2.2)))
        cmd.extend(["--width", str(render_w)])

    res = subprocess.run(cmd, input=svg_bytes, capture_output=True)
    if res.returncode != 0 or not res.stdout:
        raise SystemExit(
            f"ERROR: rsvg-convert failed (rc={res.returncode}): {res.stderr.decode('utf-8', errors='ignore')}"
        )

    # 用 Pillow 做高质量调色板压缩（矢量图与公式通常颜色很少，256 色 PNG 极清晰且体积极小）
    img = Image.open(io.BytesIO(res.stdout)).convert("RGB")
    q = img.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    q.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ── 核心构建流程 ────────────────────────────────────────────────────────────────────────────────

_MATH_BLOCK_SVG_RE = re.compile(
    r'<div class="epub-math-block">\s*(<svg\b.*?</svg>)\s*</div>',
    re.S,
)
_CAP_LABEL_RE = re.compile(r"^((?:图|表)\s*[A-Z0-9]+(?:\.[0-9]+)?)(?:[\s\u00a0\u2003\u3000]+)(.*)$", re.S)


def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _extract_body_nodes(html_text: str) -> list[Node]:
    parser = TreeBuilder()
    parser.feed(html_text)
    parser.close()
    for el in parser.root.iter_elements():
        if el.tag == "body":
            return el.children
    raise SystemExit("ERROR: Typst HTML output has no <body> element")


def _style_caption_label(figcaption: Node) -> None:
    """将题注开头的 '图 1.1' / '表 A.1' 包裹在 <span class='caption-label'> 中以突出层次。"""
    if not figcaption.children:
        return
    first = figcaption.children[0]
    if first.tag is None:
        m = _CAP_LABEL_RE.match(first.text)
        if m:
            lbl_span = Node("span", {"class": "caption-label"})
            lbl_span.children.append(Node(None, None, m.group(1)))
            rest = m.group(2)
            new_children = [lbl_span]
            if rest:
                new_children.append(Node(None, None, rest))
            figcaption.children = new_children + figcaption.children[1:]


def _upgrade_figures_and_tables(nodes: list[Node]) -> None:
    """规范化图片 figure 与表格 figure（表标题置顶、包裹 .table-wrap、移除不合理的固定宽高）。"""
    for root in nodes:
        for el in list(root.iter_elements()):
            if el.tag != "figure":
                continue
            has_table = any(c.tag == "table" for c in el.children)
            has_img = any(c.tag == "img" for c in el.children)
            if has_table:
                el.attrs["class"] = "epub-table-figure"
                figcaps = [c for c in el.children if c.tag == "figcaption"]
                others = [c for c in el.children if c.tag != "figcaption"]
                for fc in figcaps:
                    fc.attrs["class"] = "table-caption"
                    _style_caption_label(fc)
                wrapped_others: list[Node] = []
                for o in others:
                    if o.tag == "table":
                        wrap = Node("div", {"class": "table-wrap"})
                        wrap.children.append(o)
                        wrapped_others.append(wrap)
                    else:
                        wrapped_others.append(o)
                # 表标题置于表格正上方
                el.children = figcaps + wrapped_others
            elif has_img:
                el.attrs["class"] = "epub-image-figure"
                for c in el.children:
                    if c.tag == "figcaption":
                        _style_caption_label(c)


def build_book_epub(book_key: str, out_dir: pathlib.Path) -> pathlib.Path:
    cfg = BOOKS[book_key]
    typ_entry: pathlib.Path = cfg["typ_entry"]
    out_path = out_dir / cfg["out_name"]

    print(f"== 构建中文 EPUB3: {book_key} ({cfg['title']}) ==")
    with tempfile.TemporaryDirectory(prefix=f"zh-epub-{book_key}-") as tmp:
        work_dir = pathlib.Path(tmp)
        html_path = work_dir / f"{book_key}.html"

        # 1. 渲染高清带中文标题封面
        cover_jpg = render_cover_jpg(typ_entry, work_dir)
        print(f"  封面已渲染: cover.jpg ({len(cover_jpg) // 1024} KiB)")

        # 2. 用 Typst 0.15.1 导出整书语义 HTML
        run_typst([
            "compile",
            "--root", str(ZH_ROOT),
            "--features", "html",
            "--format", "html",
            "--input", "target=epub",
            str(typ_entry),
            str(html_path),
        ])
        raw_html = html_path.read_text(encoding="utf-8")

        # 3. 提前原样提取 Typst html.frame 渲染的块级公式 SVG（避免 HTMLParser 小写化 SVG 属性名）
        math_block_svgs: list[bytes] = []

        def _extract_math_svg(m: re.Match[str]) -> str:
            idx = len(math_block_svgs)
            math_block_svgs.append(m.group(1).encode("utf-8"))
            return f'<div class="epub-math-block" data-eq-idx="{idx}"></div>'

        raw_html = _MATH_BLOCK_SVG_RE.sub(_extract_math_svg, raw_html)
        body_nodes = _extract_body_nodes(raw_html)

        # 4. 剥离并索引全书脚注 (<section role="doc-endnotes">)
        endnotes_by_id: dict[str, Node] = {}
        content_nodes: list[Node] = []
        for node in body_nodes:
            if node.tag == "section" and node.attrs.get("role") == "doc-endnotes":
                for el in node.iter_elements():
                    if el.tag == "li" and "id" in el.attrs:
                        endnotes_by_id[el.attrs["id"]] = el.clone()
            else:
                content_nodes.append(node)

        # 5. 按 <div class="epub-split"> 拆分章节
        raw_chapters: list[dict] = []
        current: dict | None = None
        for node in content_nodes:
            if node.tag == "div" and "epub-split" in node.attrs.get("class", "").split():
                current = {
                    "kind": node.attrs.get("data-kind", "chapter"),
                    "kicker": node.attrs.get("data-kicker", "").strip(),
                    "data_title": node.attrs.get("data-title", "").strip(),
                    "anchor_id": node.attrs.get("id", "").strip(),
                    "nodes": [],
                }
                raw_chapters.append(current)
            else:
                if current is not None:
                    current["nodes"].append(node)

        if not raw_chapters:
            raise SystemExit(f"ERROR: {book_key}: no epub-split chapters found")

        # 6. 逐章处理：SVG/公式转高清 PNG、行内 MathML 转纯 HTML、优化表格、组装脚注
        assets: dict[str, bytes] = {}
        asset_by_hash: dict[bytes, str] = {}
        fig_seq = 0
        eq_seq = 0
        used_slugs: set[str] = set()
        counters = {"frontmatter": 0, "chapter": 0, "backmatter": 0}
        chapters: list[dict] = []

        for ch in raw_chapters:
            kind = ch["kind"]
            kicker = ch["kicker"]
            title_text = ch["data_title"]
            if not title_text:
                for n in ch["nodes"]:
                    for el in n.iter_elements():
                        if el.tag == "h1":
                            title_text = _normalize_ws(el.plain_text())
                            break
                    if title_text:
                        break
            if not title_text:
                title_text = "未命名章节"

            if kind == "copyright":
                slug = "copyright"
            elif kind == "frontmatter":
                counters["frontmatter"] += 1
                slug = f"front-{counters['frontmatter']:02d}"
            elif kind == "chapter":
                counters["chapter"] += 1
                slug = f"ch-{counters['chapter']:02d}"
            elif kind == "appendix-a":
                slug = "appendix-a"
            elif kind == "appendix-b":
                slug = "appendix-b"
            else:
                counters["backmatter"] += 1
                slug = f"back-{counters['backmatter']:02d}"

            base_slug = slug
            suffix = 2
            while slug in used_slugs:
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            used_slugs.add(slug)

            if ch["anchor_id"]:
                attached = False
                for n in ch["nodes"]:
                    if n.tag == "header":
                        n.attrs["id"] = ch["anchor_id"]
                        attached = True
                        break
                if not attached:
                    ch["nodes"].insert(0, Node("div", {"id": ch["anchor_id"]}))

            # 6a. 转换行内 MathML -> 纯 HTML 通用语义标签
            convert_inline_math_in_tree(ch["nodes"])

            # 6b. 将块级公式占位符替换为按 em 比例精确缩放的高清 Retina PNG <img>
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag == "div" and "epub-math-block" in el.attrs.get("class", "").split():
                        idx_str = el.attrs.pop("data-eq-idx", "")
                        if idx_str.isdigit():
                            svg_bytes = math_block_svgs[int(idx_str)]
                            svg_txt = svg_bytes.decode("utf-8", errors="ignore")
                            # 从 Typst SVG 的 pt 宽度计算相对 11pt 正文的真实 em 宽度，确保所有公式字号统一
                            wm = re.search(r'\bwidth="([\d.]+)pt"', svg_txt)
                            w_em = (float(wm.group(1)) / 11.0) if wm else 18.0
                            png_bytes = svg_to_png_bytes(svg_bytes, target_width=None, zoom=3.0)
                            eq_seq += 1
                            rel_asset = f"assets/eq-{eq_seq:03d}.png"
                            assets[rel_asset] = png_bytes
                            img_node = Node("img", {
                                "src": rel_asset,
                                "alt": f"公式 {eq_seq}",
                                "style": f"width: {w_em:.2f}em; max-width: 100%; height: auto;",
                            })
                            el.children = [img_node]

            # 6c. 将全部 data URI 插图（尤其是 SVG）统一光栅化为高清 PNG 嵌入
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag == "figure":
                        cap_text = ""
                        for child in el.iter_elements():
                            if child.tag == "figcaption":
                                cap_text = _normalize_ws(child.plain_text())
                                break
                        for child in el.iter_elements():
                            if child.tag == "img" and not child.attrs.get("alt"):
                                child.attrs["alt"] = cap_text[:180] if cap_text else "插图"
                    if el.tag == "img":
                        src = el.attrs.get("src", "")
                        if src.startswith("data:"):
                            m = re.match(r"^data:([^;,]+);base64,(.+)$", src, re.S)
                            if not m:
                                raise SystemExit(f"ERROR: unsupported data URI in {slug}")
                            mime, b64 = m.group(1).lower(), m.group(2)
                            raw_bytes = base64.b64decode(b64)
                            if raw_bytes in asset_by_hash:
                                rel_asset = asset_by_hash[raw_bytes]
                            else:
                                fig_seq += 1
                                if mime == "image/svg+xml":
                                    png_bytes = svg_to_png_bytes(raw_bytes, target_width=1500)
                                    rel_asset = f"assets/fig-{fig_seq:03d}.png"
                                    assets[rel_asset] = png_bytes
                                elif mime == "image/png":
                                    rel_asset = f"assets/fig-{fig_seq:03d}.png"
                                    assets[rel_asset] = raw_bytes
                                elif mime == "image/jpeg":
                                    rel_asset = f"assets/fig-{fig_seq:03d}.jpg"
                                    assets[rel_asset] = raw_bytes
                                else:
                                    raise SystemExit(f"ERROR: unsupported image mime {mime}")
                                asset_by_hash[raw_bytes] = rel_asset
                            el.attrs["src"] = rel_asset
                            el.attrs.pop("width", None)
                            el.attrs.pop("height", None)
                            el.attrs.pop("style", None)
                            if not el.attrs.get("alt"):
                                el.attrs["alt"] = "插图"

            # 6d. 升级表格与插图 figure（表标题置顶 + table-wrap + 醒目标签）
            _upgrade_figures_and_tables(ch["nodes"])

            # 6e. 收集二级目录项 (<h2>)
            sub_toc: list[tuple[str, str]] = []
            sec_idx = 0
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag == "h2":
                        sec_idx += 1
                        sec_id = el.attrs.get("id")
                        if not sec_id:
                            sec_id = f"{slug}-sec-{sec_idx}"
                            el.attrs["id"] = sec_id
                        sec_title = _normalize_ws(el.plain_text())
                        if sec_title:
                            sub_toc.append((sec_title, sec_id))

            # 6f. 收集本章引用的脚注并在章末构造独立脚注区（同步转换脚注里的行内公式）
            used_note_ids: list[str] = []
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag == "sup" and el.attrs.get("role") == "doc-noteref":
                        for a in el.iter_elements():
                            if a.tag == "a" and a.attrs.get("href", "").startswith("#"):
                                a.attrs["epub:type"] = "noteref"
                                nid = a.attrs["href"][1:]
                                if nid in endnotes_by_id and nid not in used_note_ids:
                                    used_note_ids.append(nid)

            if used_note_ids:
                fn_sec = Node("section", {
                    "class": "epub-footnotes",
                    "epub:type": "footnotes",
                    "role": "doc-endnotes",
                })
                fn_h2 = Node("h2")
                fn_h2.children.append(Node(None, None, "注释"))
                fn_ol = Node("ol")
                for nid in used_note_ids:
                    li = endnotes_by_id[nid].clone()
                    li.attrs["epub:type"] = "footnote"
                    convert_inline_math_in_tree([li])
                    fn_ol.children.append(li)
                fn_sec.children.extend([fn_h2, fn_ol])
                ch["nodes"].append(fn_sec)

            toc_label = f"{kicker}　{title_text}" if kicker else title_text
            chapters.append({
                "slug": slug,
                "href": f"{slug}.xhtml",
                "kind": kind,
                "kicker": kicker,
                "title": title_text,
                "toc_label": toc_label,
                "sub_toc": sub_toc,
                "nodes": ch["nodes"],
            })

        # 7. 建立全书 id -> filename.xhtml 映射并改写跨章链接
        id_to_href: dict[str, str] = {}
        for ch in chapters:
            seen_local: set[str] = set()
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    eid = el.attrs.get("id")
                    if eid:
                        if eid in seen_local:
                            el.attrs.pop("id", None)
                            continue
                        seen_local.add(eid)
                        id_to_href.setdefault(eid, ch["href"])

        for ch in chapters:
            cur_href = ch["href"]
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag == "a":
                        href = el.attrs.get("href", "")
                        if href.startswith("#"):
                            frag = href[1:]
                            target_href = id_to_href.get(frag)
                            if target_href and target_href != cur_href:
                                el.attrs["href"] = f"{target_href}#{frag}"

        # 8. 序列化每一章为标准 XHTML5 并逐页做严格 XML 校验
        xhtml_shell = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<!DOCTYPE html>\n"
            f'<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" xml:lang="zh-CN" lang="zh-CN">\n'
            "<head>\n"
            '  <meta charset="utf-8"/>\n'
            "  <title>{title}</title>\n"
            '  <link rel="stylesheet" type="text/css" href="epub.css"/>\n'
            "</head>\n"
            "<body{body_attrs}>\n"
            "{body}\n"
            "</body>\n"
            "</html>\n"
        )

        page_docs: dict[str, str] = {}
        for ch in chapters:
            body_xml = "\n".join(serialize_xhtml(n) for n in ch["nodes"])
            doc = xhtml_shell.format(
                title=_xml_escape_text(f"{ch['toc_label']} — {cfg['title']}"),
                body_attrs="",
                body=body_xml,
            )
            try:
                ET.fromstring(doc.encode("utf-8"))
            except ET.ParseError as exc:
                raise SystemExit(f"ERROR: {book_key}/{ch['href']} is not well-formed XHTML: {exc}") from exc
            page_docs[ch["slug"]] = doc

        # 9. 生成 cover.xhtml 与 nav.xhtml
        cover_xhtml = xhtml_shell.format(
            title=_xml_escape_text(f"封面 — {cfg['title']}"),
            body_attrs=' epub:type="cover"',
            body=(
                '<div style="text-align:center; margin:0; padding:0;">\n'
                f'  <img src="cover.jpg" alt="{_xml_escape_attr(cfg["title"] + " 封面")}" '
                'style="max-width:100%; height:auto;"/>\n'
                "</div>"
            ),
        )

        toc_items: list[str] = []
        first_body_href = next((c["href"] for c in chapters if c["kind"] == "chapter"), chapters[0]["href"])
        for ch in chapters:
            if ch["kind"] == "copyright":
                continue
            label_esc = _xml_escape_text(ch["toc_label"])
            if ch["sub_toc"]:
                sub_lis = "\n".join(
                    f'      <li><a href="{ch["href"]}#{sid}">{_xml_escape_text(stitle)}</a></li>'
                    for stitle, sid in ch["sub_toc"]
                )
                toc_items.append(
                    f'    <li><a href="{ch["href"]}">{label_esc}</a>\n'
                    f"      <ol>\n{sub_lis}\n      </ol>\n"
                    f"    </li>"
                )
            else:
                toc_items.append(f'    <li><a href="{ch["href"]}">{label_esc}</a></li>')

        nav_body = (
            '<nav epub:type="toc" role="doc-toc" id="toc">\n'
            "  <h1>目录</h1>\n"
            "  <ol>\n"
            + "\n".join(toc_items)
            + "\n  </ol>\n"
            "</nav>\n"
            '<nav epub:type="landmarks" id="landmarks" hidden="hidden">\n'
            "  <h2>导览</h2>\n"
            "  <ol>\n"
            '    <li><a epub:type="cover" href="cover.xhtml">封面</a></li>\n'
            '    <li><a epub:type="toc" href="nav.xhtml">目录</a></li>\n'
            f'    <li><a epub:type="bodymatter" href="{first_body_href}">开始阅读</a></li>\n'
            "  </ol>\n"
            "</nav>"
        )
        nav_xhtml = xhtml_shell.format(
            title=_xml_escape_text(f"目录 — {cfg['title']}"),
            body_attrs="",
            body=nav_body,
        )

        for doc in (cover_xhtml, nav_xhtml):
            ET.fromstring(doc.encode("utf-8"))

        # 10. 生成 OEBPS/content.opf
        manifest_lines = [
            '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '    <item id="cover-page" href="cover.xhtml" media-type="application/xhtml+xml"/>',
            '    <item id="cover-img" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
            '    <item id="css" href="epub.css" media-type="text/css"/>',
        ]
        spine_lines = ['    <itemref idref="cover-page"/>']
        for ch in chapters:
            slug = ch["slug"]
            manifest_lines.append(
                f'    <item id="pg-{slug}" href="{ch["href"]}" media-type="application/xhtml+xml"/>'
            )
            spine_lines.append(f'    <itemref idref="pg-{slug}"/>')
            if ch["kind"] == "copyright":
                spine_lines.append('    <itemref idref="nav"/>')

        media_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        for idx, rel in enumerate(sorted(assets), start=1):
            ext = pathlib.Path(rel).suffix.lower()
            manifest_lines.append(
                f'    <item id="asset-{idx:03d}" href="{rel}" media-type="{media_map[ext]}"/>'
            )

        opf_xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            f'<package xmlns="{OPF_NS}" version="3.0" unique-identifier="pub-id" xml:lang="zh-CN">\n'
            '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
            f'    <dc:identifier id="pub-id">{_xml_escape_text(cfg["identifier"])}</dc:identifier>\n'
            f'    <dc:title id="title">{_xml_escape_text(cfg["title"])}</dc:title>\n'
            '    <meta refines="#title" property="title-type">main</meta>\n'
            f'    <dc:title id="subtitle">{_xml_escape_text(cfg["subtitle"])}</dc:title>\n'
            '    <meta refines="#subtitle" property="title-type">subtitle</meta>\n'
            f'    <dc:creator id="creator">{_xml_escape_text(cfg["author"])}</dc:creator>\n'
            '    <meta refines="#creator" property="role" scheme="marc:relators">aut</meta>\n'
            "    <dc:language>zh-CN</dc:language>\n"
            f'    <dc:date>{_xml_escape_text(cfg["date"])}</dc:date>\n'
            f'    <dc:rights>{_xml_escape_text(cfg["rights"])}</dc:rights>\n'
            f'    <dc:description>{_xml_escape_text(cfg["description"])}</dc:description>\n'
            f'    <meta property="dcterms:modified">{_xml_escape_text(cfg["modified"])}T00:00:00Z</meta>\n'
            '    <meta property="schema:accessMode">textual</meta>\n'
            '    <meta property="schema:accessMode">visual</meta>\n'
            '    <meta property="schema:accessModeSufficient">textual,visual</meta>\n'
            '    <meta property="schema:accessibilityFeature">structuralNavigation</meta>\n'
            '    <meta property="schema:accessibilityFeature">tableOfContents</meta>\n'
            '    <meta property="schema:accessibilityHazard">none</meta>\n'
            '    <meta name="cover" content="cover-img"/>\n'
            "  </metadata>\n"
            "  <manifest>\n"
            + "\n".join(manifest_lines)
            + "\n  </manifest>\n"
            "  <spine>\n"
            + "\n".join(spine_lines)
            + "\n  </spine>\n"
            "</package>\n"
        )
        ET.fromstring(opf_xml.encode("utf-8"))

        container_xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
            "  <rootfiles>\n"
            '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
            "  </rootfiles>\n"
            "</container>\n"
        )

        # 11. 打包 EPUB3
        y, mo, d = (int(p) for p in cfg["modified"].split("-"))
        stamp = (y, mo, d, 0, 0, 0)

        def _put(zf: zipfile.ZipFile, name: str, data: bytes, compress: int = zipfile.ZIP_DEFLATED) -> None:
            zi = zipfile.ZipInfo(name, date_time=stamp)
            zi.compress_type = compress
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, data)

        out_dir.mkdir(parents=True, exist_ok=True)
        staged = work_dir / cfg["out_name"]
        with zipfile.ZipFile(staged, "w") as zf:
            _put(zf, "mimetype", b"application/epub+zip", compress=zipfile.ZIP_STORED)
            _put(zf, "META-INF/container.xml", container_xml.encode("utf-8"))
            _put(zf, "OEBPS/content.opf", opf_xml.encode("utf-8"))
            _put(zf, "OEBPS/nav.xhtml", nav_xhtml.encode("utf-8"))
            _put(zf, "OEBPS/cover.xhtml", cover_xhtml.encode("utf-8"))
            _put(zf, "OEBPS/cover.jpg", cover_jpg)
            _put(zf, "OEBPS/epub.css", EPUB_CSS.read_bytes())
            for ch in chapters:
                _put(zf, f"OEBPS/{ch['href']}", page_docs[ch["slug"]].encode("utf-8"))
            for rel in sorted(assets):
                _put(zf, f"OEBPS/{rel}", assets[rel])

        # 12. 严格校验后再覆盖目标文件
        report = validate_epub(staged)
        shutil.copy2(staged, out_path)

    size_mb = out_path.stat().st_size / 1_048_576
    print(
        f"  完成: {out_path} ({size_mb:.2f} MB) | "
        f"章节={len(chapters)} | 高清插图PNG={fig_seq} | 公式PNG={eq_seq} | "
        f"脚注={len(endnotes_by_id)} | 内部链接验证={report['local_references']}"
    )
    return out_path


# ── 严格 EPUB3 容器与跨阅读器兼容性校验器 ───────────────────────────────────────────────────────


def validate_epub(path: pathlib.Path) -> dict:
    """全面校验 EPUB3 容器、OPF、Spine、XML 良构性、图片有效性、零残留 MathML/数学平面字符与所有链接。"""
    from PIL import Image

    ns = {"opf": OPF_NS, "x": XHTML_NS}
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise ValueError(f"{path.name}: duplicate ZIP entries")
        first = zf.infolist()[0]
        if (
            first.filename != "mimetype"
            or first.compress_type != zipfile.ZIP_STORED
            or zf.read("mimetype") != b"application/epub+zip"
        ):
            raise ValueError(f"{path.name}: mimetype must be first, uncompressed, exact")
        if zf.testzip() is not None:
            raise ValueError(f"{path.name}: ZIP CRC corruption")

        container = ET.fromstring(zf.read("META-INF/container.xml"))
        roots = container.findall(
            "{urn:oasis:names:tc:opendocument:xmlns:container}rootfiles/"
            "{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
        )
        if len(roots) != 1:
            raise ValueError(f"{path.name}: expected 1 rootfile in container.xml")
        pkg_path = roots[0].get("full-path", "")
        opf = ET.fromstring(zf.read(pkg_path))
        base = posixpath.dirname(pkg_path)

        items = opf.findall("opf:manifest/opf:item", ns)
        ids = [it.get("id") for it in items]
        if len(ids) != len(set(ids)) or None in ids:
            raise ValueError(f"{path.name}: manifest IDs invalid or duplicate")

        resources = {
            it.get("id"): posixpath.normpath(posixpath.join(base, unquote(it.get("href", ""))))
            for it in items
        }
        if len(resources.values()) != len(set(resources.values())):
            raise ValueError(f"{path.name}: manifest hrefs duplicate")
        for target in resources.values():
            if target not in names:
                raise ValueError(f"{path.name}: missing manifested resource: {target}")
        if set(names) != set(resources.values()) | {"mimetype", "META-INF/container.xml", pkg_path}:
            extra = set(names) - (set(resources.values()) | {"mimetype", "META-INF/container.xml", pkg_path})
            raise ValueError(f"{path.name}: unmanifested ZIP entries: {sorted(extra)}")

        spine = [it.get("idref") for it in opf.findall("opf:spine/opf:itemref", ns)]
        if not spine or len(spine) != len(set(spine)) or any(k not in resources for k in spine):
            raise ValueError(f"{path.name}: invalid spine")

        nav_items = [it for it in items if "nav" in it.get("properties", "").split()]
        if len(nav_items) != 1:
            raise ValueError(f"{path.name}: expected exactly 1 nav item")

        documents: dict[str, ET.Element] = {}
        anchors: dict[str, set[str]] = {}
        checked_images = 0

        for it in items:
            mtype = it.get("media-type", "")
            target = resources[it.get("id")]
            raw_bytes = zf.read(target)
            if mtype.startswith("image/"):
                if mtype == "image/svg+xml":
                    raise ValueError(f"{path.name}: unrasterized SVG found (compat hazard): {target}")
                im = Image.open(io.BytesIO(raw_bytes))
                if im.width <= 0 or im.height <= 0:
                    raise ValueError(f"{path.name}: zero-sized image: {target}")
                checked_images += 1
                continue
            if mtype != "application/xhtml+xml":
                continue

            text = raw_bytes.decode("utf-8")
            if "<math" in text:
                raise ValueError(f"{path.name}: raw <math> tag left in {target}")
            bad_math_chars = [ch for ch in text if 0x1D400 <= ord(ch) <= 0x1D7FF]
            if bad_math_chars:
                raise ValueError(
                    f"{path.name}: mathematical plane Unicode chars left in {target}: {bad_math_chars[:5]}"
                )

            doc = ET.fromstring(raw_bytes)
            labels = [el.get("id") for el in doc.iter() if el.get("id")]
            if len(labels) != len(set(labels)):
                raise ValueError(f"{path.name}: duplicate id in {target}")
            documents[target] = doc
            anchors[target] = set(labels)

        nav_path = resources[nav_items[0].get("id")]
        nav_doc = documents[nav_path]
        tocs = [
            el for el in nav_doc.iter()
            if el.tag == f"{{{XHTML_NS}}}nav"
            and "toc" in el.get(f"{{{EPUB_NS}}}type", "").split()
        ]
        if len(tocs) != 1 or not tocs[0].findall(".//x:a", ns):
            raise ValueError(f"{path.name}: nav.xhtml missing populated toc")

        checked_refs = 0
        for source, doc in documents.items():
            for el in doc.iter():
                for k, val in el.attrib.items():
                    if k.rsplit("}", 1)[-1] not in {"href", "src"}:
                        continue
                    u = urlsplit(val)
                    if u.scheme or u.netloc:
                        continue
                    target = (
                        posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(u.path)))
                        if u.path else source
                    )
                    if target not in names:
                        raise ValueError(f"{path.name}: broken local resource in {source}: {val}")
                    if u.fragment and unquote(u.fragment) not in anchors.get(target, set()):
                        raise ValueError(f"{path.name}: broken fragment in {source}: {val}")
                    checked_refs += 1

        return {
            "file": str(path),
            "documents": len(documents),
            "spine_items": len(spine),
            "images_verified": checked_images,
            "resources": len(resources),
            "local_references": checked_refs,
        }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build and validate universal-compat Chinese EPUB3 editions.")
    ap.add_argument(
        "--book",
        choices=["all", "se-handbook", "mage"],
        default="all",
        help="Which book to build (default: all)",
    )
    ap.add_argument(
        "--out-dir",
        type=pathlib.Path,
        default=REPO_ROOT / "dist",
        help="Output directory for generated .epub files (default: dist/)",
    )
    ap.add_argument(
        "--check",
        type=pathlib.Path,
        nargs="+",
        help="Validate existing .epub file(s) without rebuilding",
    )
    args = ap.parse_args(argv)

    if args.check:
        for epub_file in args.check:
            rep = validate_epub(epub_file)
            print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0

    targets = ["se-handbook", "mage"] if args.book == "all" else [args.book]
    for key in targets:
        build_book_epub(key, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
