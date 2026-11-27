#!/usr/bin/env python3
"""zh_book_extractor.py — 从中文版 Typst 源码提取两本书的完整语义章节树与矢量资源。

供方案一（自建静态在线阅读站 `build_zh_web.py`）与方案二（MkDocs Material 站 `build_zh_mkdocs.py`）共同复用，
保证两套在线方案与 PDF / EPUB3 完全同源（单一事实来源，零漂移）。
"""
from __future__ import annotations

import base64
import pathlib
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_zh_epub as epub_mod  # noqa: E402

ZH_ROOT = epub_mod.ZH_ROOT
REPO_ROOT = epub_mod.REPO_ROOT
SVG_NS = "http://www.w3.org/2000/svg"
_SVG_METADATA_RE = re.compile(r"<metadata\b[^>]*>.*?</metadata>", re.S)
_SVG_OPEN_RE = re.compile(r"<svg\b([^>]*)>")
_VB_RE = re.compile(r'viewBox="[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"')

WEB_BOOKS = {
    "se-handbook": {
        **epub_mod.BOOKS["se-handbook"],
        "short_title": "软件工程手册",
        "en_title": "The Software Engineering Handbook",
        "en_subtitle": "A Judgment and Decision-Making Approach",
        "url_slug": "se-handbook",
        "pdf_filename": "software-engineering-handbook-zh.pdf",
        "epub_filename": "software-engineering-handbook-zh.epub",
        "release_base": "https://github.com/ReShweiCi/model-based-agentic-software-engineering-zh-cn/releases/download/zh-pdf-latest",
        "summary": "面向判断与决策的软件工程指南，涵盖流程、团队协作、工程知识、需求、规约、架构、设计、验证、研发与面向失败的工程。",
    },
    "mage": {
        **epub_mod.BOOKS["mage"],
        "short_title": "基于模型的智能体工程（MAGE）",
        "en_title": "Model-Based Agentic Engineering",
        "en_subtitle": "A Case Study in Software Engineering",
        "url_slug": "mage",
        "pdf_filename": "mage-book-zh.pdf",
        "epub_filename": "mage-book-zh.epub",
        "release_base": "https://github.com/ReShweiCi/model-based-agentic-software-engineering-zh-cn/releases/download/zh-pdf-latest",
        "summary": "系统阐释在商品化智能时代如何通过建模、对齐与治理转化驾驭编程智能体，包含 DocAble 案例研究、工程蓝图与实践指南。",
    },
}


def _clean_vector_svg(raw: bytes) -> bytes:
    """清理 SVG 元数据、确保 xmlns 与固有宽高完整，使浏览器无损矢量显示。"""
    text = raw.decode("utf-8", errors="ignore")
    text = _SVG_METADATA_RE.sub("", text)

    def _fix_open(m: re.Match[str]) -> str:
        attrs = m.group(1)
        if "xmlns=" not in attrs:
            attrs = f' xmlns="{SVG_NS}"' + attrs
        if "width=" not in attrs or "height=" not in attrs:
            vb = _VB_RE.search(attrs)
            if vb:
                w, h = vb.group(1), vb.group(2)
                if "width=" not in attrs:
                    attrs += f' width="{w}"'
                if "height=" not in attrs:
                    attrs += f' height="{h}"'
        return f"<svg{attrs}>"

    text = _SVG_OPEN_RE.sub(_fix_open, text, count=1)
    # 校验 XML 良构性
    ET.fromstring(text.encode("utf-8"))
    return text.encode("utf-8")


def extract_book_for_web(book_key: str) -> dict:
    """编译一本中文 Typst 书并提取为结构化章节列表、高清矢量 SVG 资源与封面 JPEG。"""
    cfg = WEB_BOOKS[book_key]
    typ_entry: pathlib.Path = cfg["typ_entry"]

    with tempfile.TemporaryDirectory(prefix=f"zh-web-{book_key}-") as tmp:
        work_dir = pathlib.Path(tmp)
        html_path = work_dir / f"{book_key}.html"

        # 1. 渲染与 PDF 一致的带中文标题封面
        cover_jpg = epub_mod.render_cover_jpg(typ_entry, work_dir)

        # 2. 导出整书语义 HTML
        epub_mod.run_typst([
            "compile",
            "--root", str(ZH_ROOT),
            "--features", "html",
            "--format", "html",
            "--input", "target=epub",
            str(typ_entry),
            str(html_path),
        ])
        raw_html = html_path.read_text(encoding="utf-8")

        # 3. 提前提取块级公式的矢量路径 SVG
        math_block_svgs: list[bytes] = []

        def _extract_math_svg(m: re.Match[str]) -> str:
            idx = len(math_block_svgs)
            math_block_svgs.append(m.group(1).encode("utf-8"))
            return f'<div class="epub-math-block" data-eq-idx="{idx}"></div>'

        raw_html = epub_mod._MATH_BLOCK_SVG_RE.sub(_extract_math_svg, raw_html)
        body_nodes = epub_mod._extract_body_nodes(raw_html)

        # 4. 剥离全书脚注
        endnotes_by_id: dict[str, epub_mod.Node] = {}
        content_nodes: list[epub_mod.Node] = []
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
                            title_text = epub_mod._normalize_ws(el.plain_text())
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
                    ch["nodes"].insert(0, epub_mod.Node("div", {"id": ch["anchor_id"]}))

            # 转换行内 MathML -> 纯 HTML 通用语义标签
            epub_mod.convert_inline_math_in_tree(ch["nodes"])

            # 块级公式直接导出为无损矢量路径 SVG，按 em 精准匹配正文字号
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag == "div" and "epub-math-block" in el.attrs.get("class", "").split():
                        idx_str = el.attrs.pop("data-eq-idx", "")
                        if idx_str.isdigit():
                            svg_bytes = _clean_vector_svg(math_block_svgs[int(idx_str)])
                            svg_txt = svg_bytes.decode("utf-8", errors="ignore")
                            wm = re.search(r'\bwidth="([\d.]+)pt"', svg_txt)
                            w_em = (float(wm.group(1)) / 11.0) if wm else 18.0
                            eq_seq += 1
                            rel_asset = f"assets/eq-{eq_seq:03d}.svg"
                            assets[rel_asset] = svg_bytes
                            img_node = epub_mod.Node("img", {
                                "src": rel_asset,
                                "alt": f"公式 {eq_seq}",
                                "class": "math-svg",
                                "style": f"width: {w_em:.2f}em; max-width: 100%; height: auto;",
                            })
                            el.children = [img_node]

            # 汉化插图直接导出为高清无损矢量 SVG（或原始 PNG/JPG）
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag == "figure":
                        cap_text = ""
                        for child in el.iter_elements():
                            if child.tag == "figcaption":
                                cap_text = epub_mod._normalize_ws(child.plain_text())
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
                                    rel_asset = f"assets/fig-{fig_seq:03d}.svg"
                                    assets[rel_asset] = _clean_vector_svg(raw_bytes)
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
                            el.attrs["loading"] = "lazy"
                            el.attrs.pop("width", None)
                            el.attrs.pop("height", None)
                            el.attrs.pop("style", None)
                            if not el.attrs.get("alt"):
                                el.attrs["alt"] = "插图"

            # 升级表格与图注（表标题置顶 + table-wrap + 醒目标签）
            epub_mod._upgrade_figures_and_tables(ch["nodes"])

            # 为 h2 / h3 分配稳定 id，构建本页 TOC
            toc_headings: list[dict] = []
            sec_idx = 0
            sub_idx = 0
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag in ("h2", "h3"):
                        level = int(el.tag[1])
                        hid = el.attrs.get("id")
                        if not hid:
                            if level == 2:
                                sec_idx += 1
                                hid = f"{slug}-s{sec_idx}"
                            else:
                                sub_idx += 1
                                hid = f"{slug}-ss{sub_idx}"
                            el.attrs["id"] = hid
                        htxt = epub_mod._normalize_ws(el.plain_text())
                        if htxt:
                            toc_headings.append({"level": level, "id": hid, "text": htxt})

            # 收集本章脚注并附着于章末，同时提取纯文本供悬停预览
            used_note_ids: list[str] = []
            notes_preview: dict[str, str] = {}
            for n in ch["nodes"]:
                for el in n.iter_elements():
                    if el.tag == "sup" and el.attrs.get("role") == "doc-noteref":
                        for a in el.iter_elements():
                            if a.tag == "a" and a.attrs.get("href", "").startswith("#"):
                                nid = a.attrs["href"][1:]
                                if nid in endnotes_by_id:
                                    if nid not in used_note_ids:
                                        used_note_ids.append(nid)
                                    # 去除开头回跳编号作为简洁提示
                                    note_clone = endnotes_by_id[nid].clone()
                                    epub_mod.convert_inline_math_in_tree([note_clone])
                                    raw_note_txt = epub_mod._normalize_ws(note_clone.plain_text())
                                    raw_note_txt = re.sub(r"^\d+\s*", "", raw_note_txt)
                                    notes_preview[nid] = raw_note_txt
                                    a.attrs["data-footnote"] = raw_note_txt

            if used_note_ids:
                fn_sec = epub_mod.Node("section", {"class": "epub-footnotes", "role": "doc-endnotes"})
                fn_h2 = epub_mod.Node("h2", {"id": f"{slug}-footnotes"})
                fn_h2.children.append(epub_mod.Node(None, None, "注释"))
                fn_ol = epub_mod.Node("ol")
                for nid in used_note_ids:
                    li = endnotes_by_id[nid].clone()
                    epub_mod.convert_inline_math_in_tree([li])
                    fn_ol.children.append(li)
                fn_sec.children.extend([fn_h2, fn_ol])
                ch["nodes"].append(fn_sec)

            toc_label = f"{kicker}　{title_text}" if kicker else title_text
            chapters.append({
                "slug": slug,
                "href": f"{slug}.html",
                "kind": kind,
                "kicker": kicker,
                "title": title_text,
                "toc_label": toc_label,
                "toc_headings": toc_headings,
                "nodes": ch["nodes"],
            })

        # 6. 全局 id -> slug.html 跨章链接改写
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

        # 7. 序列化正文 HTML 与纯文本搜索摘要
        for ch in chapters:
            ch["body_html"] = "\n".join(epub_mod.serialize_xhtml(n) for n in ch["nodes"])
            ch["plain_text"] = epub_mod._normalize_ws(
                " ".join(n.plain_text() for n in ch["nodes"])
            )

        return {
            "key": book_key,
            "cfg": cfg,
            "cover_jpg": cover_jpg,
            "chapters": chapters,
            "assets": assets,
            "stats": {
                "chapters": len(chapters),
                "figures": fig_seq,
                "equations": eq_seq,
                "footnotes": len(endnotes_by_id),
            },
        }
