#!/usr/bin/env python3
"""build_zh_web.py — 两本中文译本的纯静态在线阅读站生成器。

只依赖 Python 标准库与 Typst 0.15.1（无 Node/MkDocs），输出可直接部署到 GitHub Pages：
  - 书架首页：两本书的封面、简介、在线阅读入口与 PDF/EPUB 下载；
  - 三栏阅读页：左侧章节目录、中间正文、右侧本页大纲（窄屏时目录收为抽屉，大纲并入目录）；
  - 客户端全文搜索（Ctrl+K 或 `/`），跨两本书检索并高亮片段；
  - 日间 / 护眼 / 夜间三种主题与五档字号，选择保存在浏览器本地；
  - SVG 插图灯箱、脚注悬停预览、阅读进度条、键盘 ←/→ 翻章。

用法：
  python3 translations/zh-CN/scripts/build_zh_web.py --out-dir dist/web-custom
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import zh_book_extractor as ext  # noqa: E402

REPO_ROOT = ext.REPO_ROOT

SITE_CSS = r"""/* zh-web-reader — Umber Monograph 中文双书在线阅读站样式 */
:root {
  --bg: #fdfcf9;
  --bg-elev: #f6f4ef;
  --bg-header: #1c1917;
  --fg-header: #faf8f5;
  --ink: #1c1917;
  --muted: #57534e;
  --rule: #e4e0d8;
  --accent: #9a3f12;
  --accent-soft: rgba(154, 63, 18, 0.08);
  --code-bg: #f3efe7;
  --plate-bg: #fdfcf9;
  --shadow: 0 8px 28px rgba(28, 25, 23, 0.08);
  --font-serif: "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", Georgia, serif;
  --font-sans: "Noto Sans CJK SC", "Source Han Sans SC", "PingFang SC", -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: "Noto Sans Mono CJK SC", "JetBrains Mono", ui-monospace, SFMono-Regular, monospace;
  --reader-size: 17px;
  --reader-max: 44rem;
}

[data-theme="sepia"] {
  --bg: #f4ecd8;
  --bg-elev: #ebe0c6;
  --bg-header: #2c241b;
  --ink: #2b2118;
  --muted: #665643;
  --rule: #dacba8;
  --code-bg: #e7dac0;
  --plate-bg: #faf5e8;
}

[data-theme="dark"] {
  --bg: #161514;
  --bg-elev: #201e1c;
  --bg-header: #0f0e0d;
  --ink: #e7e3dc;
  --muted: #a69f95;
  --rule: #322f2b;
  --accent: #e07a47;
  --accent-soft: rgba(224, 122, 71, 0.14);
  --code-bg: #24211e;
  --plate-bg: #f8f6f1;
  --shadow: 0 10px 32px rgba(0, 0, 0, 0.45);
}

* { box-sizing: border-box; }
html {
  scroll-behavior: smooth;
  -webkit-text-size-adjust: 100%; text-size-adjust: 100%;
  -webkit-tap-highlight-color: transparent;
}
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-sans);
  line-height: 1.75;
  -webkit-font-smoothing: antialiased;
  overflow-x: clip;
  transition: background-color 0.2s ease, color 0.2s ease;
}
body.no-scroll { overflow: hidden; }
img, svg, video { max-width: 100%; }
button { font: inherit; color: inherit; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* 顶栏与阅读进度条 */
.topbar {
  position: sticky; top: 0; z-index: 60;
  background: var(--bg-header); color: var(--fg-header);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  padding-top: env(safe-area-inset-top);
  transition: transform 0.25s ease;
}
.topbar-inner {
  max-width: 92rem; margin: 0 auto;
  height: 56px;
  padding: 0 max(1rem, env(safe-area-inset-right)) 0 max(1rem, env(safe-area-inset-left));
  display: flex; align-items: center; gap: 0.75rem;
}
.brand {
  display: flex; align-items: center; gap: 0.55rem; min-width: 0;
  color: var(--fg-header); font-weight: 700; font-size: 0.96rem;
  letter-spacing: 0.02em; white-space: nowrap;
}
.brand:hover { text-decoration: none; opacity: 0.92; }
.brand-text { overflow: hidden; text-overflow: ellipsis; }
.brand-badge {
  flex: none;
  background: #9a3f12; color: #fff; font-size: 0.72rem;
  padding: 0.15rem 0.45rem; border-radius: 4px; letter-spacing: 0.06em;
}
.book-switch {
  display: flex; align-items: center; gap: 0.25rem; margin-left: 0.5rem;
}
.book-switch a {
  color: rgba(250,248,245,0.78); font-size: 0.86rem;
  padding: 0.32rem 0.65rem; border-radius: 6px; white-space: nowrap;
}
.book-switch a.active, .book-switch a:hover {
  color: #fff; background: rgba(255,255,255,0.12); text-decoration: none;
}
.topbar-spacer { flex: 1; }
.toolbar {
  display: flex; align-items: center; gap: 0.4rem; flex: none;
}
.icon-btn {
  background: rgba(255,255,255,0.08); color: var(--fg-header);
  border: 1px solid rgba(255,255,255,0.14); border-radius: 8px;
  height: 34px; min-width: 34px; padding: 0 0.62rem; font-size: 0.84rem;
  cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
  gap: 0.4rem; white-space: nowrap;
  transition: background-color 0.15s ease;
}
.icon-btn svg { width: 17px; height: 17px; flex: none; }
.icon-btn:hover, .icon-btn[aria-expanded="true"] { background: rgba(255,255,255,0.18); }
.icon-btn kbd {
  font-family: var(--font-sans); font-size: 0.7rem; opacity: 0.6;
  border: 1px solid rgba(255,255,255,0.25); border-radius: 4px; padding: 0 0.3rem;
}
.menu-toggle { display: none; }
.progress-bar {
  position: fixed; top: 0; left: 0; z-index: 70;
  height: 3px; width: 0%; background: #e07a47;
  transition: width 0.08s linear; pointer-events: none;
}

/* 阅读设置弹层（主题 / 字号 / 书籍切换） */
.settings { position: relative; }
.settings-panel {
  position: absolute; right: 0; top: calc(100% + 10px); z-index: 75;
  width: 260px; padding: 0.9rem; border-radius: 12px;
  background: var(--bg); color: var(--ink); border: 1px solid var(--rule);
  box-shadow: 0 16px 40px rgba(0,0,0,0.22);
  opacity: 0; transform: translateY(-6px) scale(0.98); transform-origin: top right;
  visibility: hidden; transition: opacity 0.15s ease, transform 0.15s ease, visibility 0.15s;
}
.settings-panel.open { opacity: 1; transform: none; visibility: visible; }
.sp-label {
  font-size: 0.74rem; font-weight: 700; letter-spacing: 0.08em; color: var(--muted);
  margin: 0.15rem 0 0.4rem;
}
.sp-label:not(:first-child) { margin-top: 0.85rem; }
.seg {
  display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 0.3rem;
  background: var(--bg-elev); border: 1px solid var(--rule); border-radius: 9px; padding: 0.25rem;
}
.seg button {
  border: none; background: transparent; border-radius: 6px; cursor: pointer;
  padding: 0.42rem 0.2rem; font-size: 0.84rem; color: var(--ink);
}
.seg button:hover { background: var(--accent-soft); }
.seg button.active { background: var(--accent); color: #fff; font-weight: 600; }
.seg .font-val {
  display: flex; align-items: center; justify-content: center;
  font-size: 0.84rem; color: var(--muted); font-variant-numeric: tabular-nums;
}
.sp-books { display: none; }
.sp-books a {
  display: block; padding: 0.5rem 0.65rem; border-radius: 7px; color: var(--ink);
  font-size: 0.9rem; border: 1px solid var(--rule); margin-top: 0.35rem;
}
.sp-books a.active { border-color: var(--accent); color: var(--accent); font-weight: 600; }
.sp-books a:hover { text-decoration: none; background: var(--accent-soft); }

/* 书架首页 */
.home-hero {
  max-width: 72rem; margin: 0 auto; padding: 3.2rem 1.5rem 2rem; text-align: center;
}
.home-kicker {
  font-size: 0.8rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin-bottom: 0.6rem;
}
.home-hero h1 {
  font-family: var(--font-serif); font-size: clamp(1.75rem, 3.2vw, 2.5rem);
  margin: 0 0 0.75rem; line-height: 1.28;
}
.home-hero p {
  max-width: 44rem; margin: 0 auto; color: var(--muted); font-size: 1rem;
}
.shelf-grid {
  max-width: 72rem; margin: 1.5rem auto 4rem; padding: 0 1.5rem;
  display: grid; grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr));
  gap: 2rem;
}
.book-card {
  background: var(--bg-elev); border: 1px solid var(--rule); border-radius: 12px;
  overflow: hidden; display: flex; flex-direction: column; min-width: 0;
  box-shadow: var(--shadow); transition: transform 0.18s ease, box-shadow 0.18s ease;
}
@media (hover: hover) {
  .book-card:hover { transform: translateY(-3px); box-shadow: 0 14px 36px rgba(28,25,23,0.14); }
}
.book-card-cover {
  background: var(--plate-bg); padding: 1.4rem; display: flex; justify-content: center;
  border-bottom: 1px solid var(--rule);
}
.book-card-cover img {
  width: 210px; height: auto; border-radius: 5px;
  box-shadow: 0 10px 24px rgba(0,0,0,0.18);
}
.book-card-body {
  padding: 1.4rem 1.5rem 1.6rem; display: flex; flex-direction: column; flex: 1;
}
.book-card h2 {
  font-family: var(--font-serif); margin: 0 0 0.25rem; font-size: 1.32rem; line-height: 1.35;
}
.book-en { font-size: 0.85rem; color: var(--muted); margin-bottom: 0.8rem; }
.book-desc { font-size: 0.93rem; color: var(--ink); opacity: 0.9; margin: 0 0 1.25rem; flex: 1; }
.card-actions { display: flex; flex-wrap: wrap; gap: 0.55rem; }
.btn-primary {
  background: var(--accent); color: #fff; font-weight: 600; font-size: 0.9rem;
  padding: 0.55rem 1.05rem; border-radius: 7px; display: inline-flex; align-items: center;
}
.btn-primary:hover { opacity: 0.9; text-decoration: none; }
.btn-ghost {
  background: transparent; color: var(--ink); border: 1px solid var(--rule);
  font-size: 0.85rem; padding: 0.52rem 0.85rem; border-radius: 7px;
}
.btn-ghost:hover { border-color: var(--accent); color: var(--accent); text-decoration: none; }
.home-footer {
  max-width: 72rem; margin: 0 auto; padding: 1.5rem; text-align: center;
  border-top: 1px solid var(--rule); color: var(--muted); font-size: 0.86rem;
}

/* 三栏阅读器布局 */
.reader-shell {
  max-width: 92rem; margin: 0 auto;
  display: grid; grid-template-columns: 276px minmax(0, 1fr) 236px;
  min-height: calc(100vh - 57px);
}
.sidebar-left {
  position: sticky; top: 57px; height: calc(100vh - 57px); height: calc(100dvh - 57px);
  overflow-y: auto; overscroll-behavior: contain; border-right: 1px solid var(--rule);
  background: var(--bg-elev); padding: 1rem 0.85rem 2.5rem;
}
.drawer-head { display: none; }
.drawer-backdrop {
  position: fixed; inset: 0; z-index: 85; background: rgba(0,0,0,0.42);
  opacity: 0; visibility: hidden; transition: opacity 0.22s ease, visibility 0.22s;
}
.drawer-backdrop.open { opacity: 1; visibility: visible; }
.chapter-outline { display: none; list-style: none; margin: 0.2rem 0 0.4rem 0.9rem; padding: 0 0 0 0.6rem; border-left: 1px solid var(--rule); }
.chapter-outline a { font-size: 0.8rem; padding: 0.26rem 0.5rem; color: var(--muted); }
.chapter-outline li.lv3 a { padding-left: 1.2rem; font-size: 0.77rem; }
.chapter-list .chapter-outline a.active {
  background: none; border-left: none; padding-left: 0.5rem; color: var(--accent); font-weight: 600;
}
.chapter-list .chapter-outline li.lv3 a.active { padding-left: 1.2rem; }
.sidebar-book-head {
  padding: 0.25rem 0.45rem 0.85rem; margin-bottom: 0.7rem;
  border-bottom: 1px solid var(--rule);
}
.sidebar-book-title { font-weight: 700; font-size: 0.95rem; line-height: 1.38; }
.sidebar-downloads {
  display: flex; gap: 0.45rem; margin-top: 0.55rem; flex-wrap: wrap;
}
.sidebar-downloads a {
  font-size: 0.76rem; padding: 0.16rem 0.5rem; border-radius: 5px;
  border: 1px solid var(--rule); color: var(--muted);
}
.sidebar-downloads a:hover { border-color: var(--accent); color: var(--accent); text-decoration: none; }
.nav-group-label {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; color: var(--muted);
  margin: 0.95rem 0.45rem 0.35rem; text-transform: uppercase;
}
.chapter-list { list-style: none; margin: 0; padding: 0; }
.chapter-list li { margin: 0.12rem 0; }
.chapter-list a {
  display: block; padding: 0.36rem 0.55rem; border-radius: 6px;
  font-size: 0.86rem; line-height: 1.45; color: var(--ink);
}
.chapter-list a:hover { background: var(--accent-soft); text-decoration: none; }
.chapter-list a.active {
  background: var(--accent-soft); color: var(--accent); font-weight: 700;
  border-left: 3px solid var(--accent); padding-left: calc(0.55rem - 3px);
}

/* 正文区 */
.reader-main {
  padding: 2.2rem clamp(1.2rem, 4vw, 3.4rem) 4rem;
  min-width: 0;
}
.article-wrap {
  max-width: var(--reader-max); margin: 0 auto;
  font-family: var(--font-serif); font-size: var(--reader-size);
  line-height: 1.85; overflow-wrap: break-word;
}
.article-wrap a { overflow-wrap: anywhere; }
.article-wrap p {
  margin: 0.72em 0; text-indent: 2em; text-align: justify;
}
.article-wrap header.chap {
  margin: 0 0 1.8rem; padding-bottom: 0.75rem; border-bottom: 1.5px solid var(--rule);
}
.article-wrap header.chap .kicker {
  font-family: var(--font-sans); font-size: 0.82rem; font-weight: 700;
  letter-spacing: 0.14em; color: var(--accent); margin-bottom: 0.35rem;
}
.article-wrap header.chap h1 {
  font-family: var(--font-sans); font-size: clamp(1.55rem, 2.5vw, 2.05rem);
  line-height: 1.3; margin: 0; text-indent: 0;
}
.article-wrap h2, .article-wrap h3, .article-wrap h4 {
  font-family: var(--font-sans); text-indent: 0; scroll-margin-top: 76px;
  line-height: 1.38;
}
.article-wrap h2 { margin: 2.1em 0 0.75em; font-size: 1.32em; border-bottom: 1px dashed var(--rule); padding-bottom: 0.25em; }
.article-wrap h3 { margin: 1.65em 0 0.55em; font-size: 1.12em; color: var(--muted); }
.article-wrap h4 { margin: 1.3em 0 0.4em; font-size: 1em; }

/* 版权页与 MAGE 导览框 */
.copyright-page p { text-indent: 0 !important; text-align: left !important; font-size: 0.94em; }
.copyright-en { color: var(--muted); }
.copyright-sub { color: var(--accent); margin-bottom: 1.2em !important; }
aside.mage-opener {
  font-family: var(--font-sans); margin: 0 0 1.6rem; padding: 1rem 1.2rem;
  border-left: 3.5px solid var(--accent); background: var(--bg-elev); border-radius: 0 8px 8px 0;
}
aside.mage-opener .mage-opener-progress { font-size: 0.82rem; font-weight: 700; color: var(--muted); margin-bottom: 0.35rem; }
aside.mage-opener .mage-opener-label { font-size: 0.76rem; font-weight: 700; letter-spacing: 0.08em; color: var(--accent); margin-bottom: 0.3rem; }
aside.mage-opener .mage-opener-q { font-size: 1.03rem; font-weight: 600; }

/* 语义框 */
aside.hb-callout {
  margin: 1.4rem 0; padding: 0.9rem 1.15rem; border-radius: 0 8px 8px 0;
  border-left: 3.5px solid var(--muted); background: var(--bg-elev);
}
aside.hb-callout-definition { border-left-color: #1f6fae; background: rgba(31,111,174,0.07); }
aside.hb-callout-decision   { border-left-color: #9a3f12; background: rgba(154,63,18,0.07); }
aside.hb-callout-key-idea,
aside.hb-callout-example    { border-left-color: #15803d; background: rgba(21,128,61,0.07); }
aside.hb-callout-case-study { border-left-color: #2f5169; background: rgba(47,81,105,0.08); }
aside.hb-callout-warning    { border-left-color: #b23b3b; background: rgba(178,59,59,0.08); }
.hb-callout-title { font-family: var(--font-sans); font-size: 0.9rem; font-weight: 700; margin-bottom: 0.45rem; }
.hb-callout-kind { margin-right: 0.55rem; color: var(--accent); }
aside.hb-callout-definition .hb-callout-kind { color: #1f6fae; }
aside.hb-callout-key-idea .hb-callout-kind,
aside.hb-callout-example .hb-callout-kind    { color: #15803d; }
aside.hb-callout-case-study .hb-callout-kind { color: #2f5169; }
aside.hb-callout-warning .hb-callout-kind    { color: #b23b3b; }
aside.hb-callout p { text-indent: 0; font-size: 0.95em; }

aside.hb-read-further {
  margin: 2rem 0 1.2rem; padding: 1rem 1.2rem; border-left: 3px solid var(--muted);
  background: var(--bg-elev); border-radius: 0 8px 8px 0;
}
.hb-read-further-title {
  font-family: var(--font-sans); font-size: 0.8rem; font-weight: 700;
  letter-spacing: 0.1em; color: var(--muted); margin-bottom: 0.55rem;
}
aside.hb-read-further p {
  font-size: 0.9rem; padding-left: 1.5em; text-indent: -1.5em; text-align: left; margin: 0.45em 0;
}

/* 引用、代码、列表 */
blockquote {
  margin: 1.25rem 0; padding: 0.6rem 1.1rem;
  border-left: 3px solid var(--accent); background: var(--bg-elev); border-radius: 0 6px 6px 0;
}
blockquote p { text-indent: 0; }
blockquote footer.quote-attribution {
  font-family: var(--font-sans); text-align: right; font-size: 0.88rem; color: var(--muted); margin-top: 0.4rem;
}
ul, ol { margin: 0.75em 0; padding-left: 1.7em; }
li p { text-indent: 0; }
pre {
  font-family: var(--font-mono); font-size: 0.84rem; line-height: 1.55;
  background: var(--code-bg); border: 1px solid var(--rule); border-radius: 7px;
  padding: 0.85rem 1rem; overflow-x: auto;
}
code {
  font-family: var(--font-mono); font-size: 0.86em;
  background: var(--code-bg); padding: 0.1em 0.3em; border-radius: 4px;
}
pre code { background: none; padding: 0; }
hr { border: none; border-top: 1px solid var(--rule); width: 38%; margin: 1.8rem auto; }

/* 矢量插图 + 暗黑模式暖白底板 + 灯箱交互 */
figure.epub-image-figure { margin: 1.7rem 0; text-align: center; }
figure.epub-image-figure img {
  max-width: 100%; height: auto; display: block; margin: 0 auto;
  background: var(--plate-bg); padding: 0.55rem; border: 1px solid var(--rule);
  border-radius: 8px; cursor: zoom-in;
}
figure.epub-image-figure figcaption {
  font-family: var(--font-sans); margin-top: 0.6rem; font-size: 0.88rem;
  line-height: 1.6; text-align: left; color: var(--muted);
}

/* 现代出版级三线表 */
figure.epub-table-figure { margin: 1.7rem 0; }
figure.epub-table-figure figcaption.table-caption {
  font-family: var(--font-sans); font-size: 0.9rem; line-height: 1.55;
  margin-bottom: 0.55rem; color: var(--ink);
}
.caption-label { font-weight: 700; color: var(--accent); margin-right: 0.45rem; }
.table-wrap { width: 100%; overflow-x: auto; }
table {
  width: 100%; border-collapse: collapse; font-family: var(--font-sans);
  font-size: 0.88rem; line-height: 1.6;
  border-top: 2px solid var(--accent); border-bottom: 2px solid var(--accent);
}
table thead tr { background: var(--accent-soft); border-bottom: 1.2px solid var(--accent); }
table tbody tr { border-bottom: 1px solid var(--rule); }
table tbody tr:last-child { border-bottom: none; }
table tbody tr:nth-child(even) { background: rgba(128,128,128,0.035); }
table th, table td { padding: 0.58rem 0.72rem; text-align: left; vertical-align: top; }
table td:first-child, table th:first-child { min-width: 6em; font-weight: 600; }
table p { text-indent: 0 !important; text-align: left !important; margin: 0.15em 0; }

/* 行内公式与矢量块级公式 */
span.math-inline { font-family: Georgia, "Times New Roman", var(--font-serif); white-space: nowrap; }
div.epub-math-block {
  margin: 1.35rem 0; padding: 0.7rem 0.9rem; text-align: center;
  background: var(--plate-bg); border: 1px solid var(--rule); border-radius: 8px;
  overflow-x: auto;
}
div.epub-math-block img { display: inline-block; vertical-align: middle; }

/* 脚注与参考文献 */
sup[role="doc-noteref"] a {
  font-family: var(--font-sans); font-size: 0.76em; font-weight: 700;
  padding: 0 0.15em; scroll-margin-top: 84px;
}
section.epub-footnotes {
  margin-top: 2.6rem; padding-top: 1rem; border-top: 1px solid var(--rule);
  font-size: 0.9rem;
}
section.epub-footnotes h2 { font-size: 1rem; margin: 0 0 0.7rem; border: none; }
section.epub-footnotes ol { list-style: none; padding: 0; }
section.epub-footnotes li { margin: 0.55rem 0; scroll-margin-top: 84px; }
section.epub-footnotes sup[role="doc-backlink"] { margin-right: 0.5rem; font-weight: 700; }
section.epub-footnotes p { text-indent: 0; display: inline; }
section[role="doc-bibliography"] ul { list-style: none; padding: 0; }
section[role="doc-bibliography"] li {
  font-size: 0.88rem; margin: 0.5rem 0; padding-left: 1.5em; text-indent: -1.5em; text-align: left;
}
.idx-page p { text-indent: 0 !important; text-align: left !important; margin: 0.25rem 0; font-size: 0.9rem; }
.idx-sub { margin-left: 1.4rem; color: var(--muted); }

/* 上下章翻页 */
.chapter-pager {
  max-width: var(--reader-max); margin: 3rem auto 0; padding-top: 1.4rem;
  border-top: 1px solid var(--rule);
  display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;
  font-family: var(--font-sans);
}
.pager-card {
  display: block; padding: 0.85rem 1rem; border: 1px solid var(--rule);
  border-radius: 8px; background: var(--bg-elev);
}
.pager-card:hover { border-color: var(--accent); text-decoration: none; }
.pager-card.next { text-align: right; }
.pager-dir { font-size: 0.76rem; color: var(--muted); display: block; margin-bottom: 0.2rem; }
.pager-title { font-size: 0.92rem; font-weight: 600; color: var(--ink); }

/* 右侧本页大纲 */
.sidebar-right {
  position: sticky; top: 57px; height: calc(100vh - 57px);
  overflow-y: auto; border-left: 1px solid var(--rule);
  padding: 1.2rem 0.9rem 2rem; font-size: 0.82rem;
}
.toc-title {
  font-size: 0.74rem; font-weight: 700; letter-spacing: 0.1em; color: var(--muted);
  margin-bottom: 0.6rem; text-transform: uppercase;
}
.toc-list { list-style: none; margin: 0; padding: 0; }
.toc-list li { margin: 0.28rem 0; }
.toc-list li.lv3 { padding-left: 0.85rem; font-size: 0.78rem; }
.toc-list a { color: var(--muted); display: block; line-height: 1.42; }
.toc-list a.active, .toc-list a:hover { color: var(--accent); font-weight: 600; text-decoration: none; }

/* 脚注悬停气泡 + 搜索弹窗 + 灯箱 */
.fn-tooltip {
  position: fixed; z-index: 90; max-width: 24rem; padding: 0.7rem 0.9rem;
  background: var(--bg-header); color: var(--fg-header); font-family: var(--font-sans);
  font-size: 0.84rem; line-height: 1.55; border-radius: 8px;
  box-shadow: 0 12px 30px rgba(0,0,0,0.3); pointer-events: none; display: none;
}
.modal-backdrop {
  position: fixed; inset: 0; z-index: 100; background: rgba(0,0,0,0.55);
  display: none; align-items: flex-start; justify-content: center; padding: 8vh 1rem;
}
.modal-backdrop.open { display: flex; }
.search-box {
  width: min(40rem, 100%); display: flex; flex-direction: column; background: var(--bg); color: var(--ink);
  border: 1px solid var(--rule); border-radius: 12px; box-shadow: var(--shadow); overflow: hidden;
}
.search-input-wrap {
  display: flex; align-items: center; gap: 0.6rem; padding: 0.8rem 1rem; border-bottom: 1px solid var(--rule);
}
.search-input-wrap svg { width: 18px; height: 18px; color: var(--muted); flex: none; }
.search-close {
  border: none; background: none; color: var(--accent); cursor: pointer;
  font-size: 0.92rem; padding: 0.2rem 0.1rem; flex: none;
}
.search-input-wrap input {
  flex: 1; border: none; outline: none; background: transparent;
  color: var(--ink); font-size: 16px; font-family: var(--font-sans); min-width: 0;
}
.search-input-wrap input::-webkit-search-cancel-button { display: none; }
.search-results { max-height: 58vh; overflow-y: auto; overscroll-behavior: contain; padding: 0.5rem; }
.search-empty { padding: 1rem; color: var(--muted); font-size: 0.88rem; }
.search-hit {
  display: block; padding: 0.65rem 0.8rem; border-radius: 7px; color: var(--ink);
}
.search-hit:hover { background: var(--bg-elev); text-decoration: none; }
.search-hit-meta { font-size: 0.75rem; color: var(--accent); font-weight: 600; }
.search-hit-title { font-size: 0.94rem; font-weight: 700; margin: 0.1rem 0; }
.search-hit-snip { font-size: 0.83rem; color: var(--muted); }
.search-hit-snip mark { background: var(--accent-soft); color: var(--accent); font-weight: 700; padding: 0 2px; border-radius: 2px; }
.lightbox {
  position: fixed; inset: 0; z-index: 110; background: rgba(0,0,0,0.86);
  display: none; align-items: center; justify-content: center; padding: 2rem; cursor: zoom-out;
  overflow: auto; touch-action: pinch-zoom;
}
.lightbox.open { display: flex; animation: fade-in 0.18s ease; }
.lightbox img { max-width: 95vw; max-height: 92vh; background: #fdfcf9; padding: 0.8rem; border-radius: 8px; }
@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
.modal-backdrop.open { animation: fade-in 0.15s ease; }

/* 响应式 */
@media (max-width: 1160px) {
  .reader-shell { grid-template-columns: 256px minmax(0, 1fr); }
  .sidebar-right { display: none; }
  .chapter-list li.has-outline > .chapter-outline { display: block; }
}
@media (max-width: 960px) {
  .btn-label, .icon-btn kbd { display: none; }
  .icon-btn { padding: 0 0.5rem; }
}
@media (max-width: 820px) {
  .book-switch { display: none; }
  .sp-books { display: block; }
  .menu-toggle { display: inline-flex; }
  .topbar-inner { gap: 0.5rem; height: 52px; }
  .topbar.is-hidden { transform: translateY(-100%); }
  .brand { font-size: 0.92rem; gap: 0.45rem; }
  .reader-shell { grid-template-columns: minmax(0, 1fr); min-height: 0; }
  .sidebar-left {
    position: fixed; left: 0; top: 0; bottom: 0; height: auto; z-index: 90;
    width: min(86vw, 320px); padding: 0 0.85rem calc(2rem + env(safe-area-inset-bottom));
    padding-left: max(0.85rem, env(safe-area-inset-left));
    transform: translateX(-102%); transition: transform 0.25s cubic-bezier(0.22, 0.61, 0.36, 1);
    box-shadow: 0 0 40px rgba(0,0,0,0.25); border-right: none;
  }
  .sidebar-left.open { transform: translateX(0); }
  .drawer-head {
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 1; margin: 0 -0.85rem 0.6rem; padding: 0.7rem 0.85rem;
    padding-top: calc(0.7rem + env(safe-area-inset-top));
    background: var(--bg-elev); border-bottom: 1px solid var(--rule);
    font-weight: 700; font-size: 0.9rem;
  }
  .drawer-close {
    border: 1px solid var(--rule); background: var(--bg); border-radius: 8px;
    width: 34px; height: 34px; cursor: pointer; font-size: 1.1rem; line-height: 1;
  }
  .chapter-list a { padding: 0.5rem 0.6rem; font-size: 0.9rem; }
  .chapter-outline a { padding: 0.36rem 0.5rem; font-size: 0.83rem; }

  .reader-main { padding: 1.5rem 1.1rem 3rem; padding-left: max(1.1rem, env(safe-area-inset-left)); padding-right: max(1.1rem, env(safe-area-inset-right)); }
  .article-wrap { line-height: 1.8; }
  .article-wrap p { margin: 0.65em 0; }
  .article-wrap header.chap { margin-bottom: 1.3rem; }
  .article-wrap header.chap h1 { font-size: 1.5rem; }
  .article-wrap h2 { font-size: 1.22em; margin-top: 1.8em; }
  .article-wrap h2, .article-wrap h3, .article-wrap h4 { scroll-margin-top: 16px; }
  aside.mage-opener, aside.hb-callout, aside.hb-read-further, blockquote {
    padding: 0.8rem 0.9rem; margin-left: 0; margin-right: 0;
  }
  aside.mage-opener .mage-opener-label { letter-spacing: 0.03em; }
  ul, ol { padding-left: 1.4em; }
  figure.epub-image-figure, figure.epub-table-figure { margin: 1.3rem 0; }
  figure.epub-image-figure img { padding: 0.35rem; }
  .table-wrap { margin: 0 -1.1rem; padding: 0 1.1rem; width: auto; }
  table { font-size: 0.82rem; }
  table th, table td { padding: 0.5rem 0.55rem; }
  table td:first-child, table th:first-child { min-width: 5em; }
  pre { font-size: 0.8rem; margin-left: -0.3rem; margin-right: -0.3rem; }
  span.math-inline { white-space: normal; }
  div.epub-math-block { padding: 0.6rem 0.5rem; }
  .chapter-pager { margin-top: 2.2rem; gap: 0.6rem; }
  .pager-card { padding: 0.7rem 0.85rem; }

  .settings-panel { position: fixed; top: calc(60px + env(safe-area-inset-top)); right: 0.6rem; width: min(300px, calc(100vw - 1.2rem)); }

  .modal-backdrop { padding: 0; align-items: stretch; background: var(--bg); }
  .search-box { width: 100%; height: 100%; height: 100dvh; border: none; border-radius: 0; box-shadow: none; padding-top: env(safe-area-inset-top); }
  .search-results { max-height: none; flex: 1; padding-bottom: calc(1rem + env(safe-area-inset-bottom)); }
  .lightbox { padding: 0.6rem; }
  .lightbox img { max-width: 100%; max-height: 100%; padding: 0.4rem; }

  .home-hero { padding: 2rem 1.1rem 1rem; }
  .home-kicker { font-size: 0.7rem; letter-spacing: 0.08em; }
  .home-hero h1 { font-size: 1.55rem; }
  .home-hero p { font-size: 0.9rem; }
  .shelf-grid { padding: 0 1rem; gap: 1.25rem; margin-bottom: 2.5rem; }
  .book-card-cover { padding: 1.1rem; }
  .book-card-cover img { width: min(180px, 52vw); }
  .book-card-body { padding: 1.1rem 1.1rem 1.25rem; }
  .book-card h2 { font-size: 1.22rem; }
  .card-actions .btn-primary { flex: 1 1 100%; justify-content: center; padding: 0.7rem 1rem; }
  .card-actions .btn-ghost { flex: 1; text-align: center; padding: 0.6rem 0.85rem; }
  .home-footer { padding: 1.25rem 1rem calc(1.25rem + env(safe-area-inset-bottom)); font-size: 0.8rem; line-height: 1.9; }
  .home-footer .sep { display: none; }
  .home-footer a { display: block; overflow-wrap: anywhere; }
}
@media (max-width: 400px) {
  .brand-text { font-size: 0.86rem; }
  .brand-badge { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { transition: none !important; animation: none !important; }
}
"""

SITE_JS = r"""/* zh-web-reader client script */
(function () {
  const root = document.documentElement;
  const body = document.body;
  const themes = ["light", "sepia", "dark"];
  const themeColors = { light: "#1c1917", sepia: "#2c241b", dark: "#0f0e0d" };
  const sizes = [15, 16, 17, 19, 21];
  const store = {
    get(k, d) { try { return localStorage.getItem(k) || d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };
  const isMobile = () => window.matchMedia("(max-width: 820px)").matches;

  function applyTheme(t) {
    if (!themes.includes(t)) t = "light";
    root.setAttribute("data-theme", t);
    store.set("zh_web_theme", t);
    document.querySelectorAll("[data-set-theme]").forEach((b) =>
      b.classList.toggle("active", b.getAttribute("data-set-theme") === t));
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", themeColors[t]);
  }
  function currentSize() {
    const n = Number(store.get("zh_web_size", "17"));
    return sizes.includes(n) ? n : 17;
  }
  function applySize(n) {
    if (!sizes.includes(n)) n = 17;
    root.style.setProperty("--reader-size", n + "px");
    store.set("zh_web_size", String(n));
    const v = document.getElementById("fontVal");
    if (v) v.textContent = n + "px";
  }
  applyTheme(store.get("zh_web_theme", "light"));
  applySize(currentSize());

  document.querySelectorAll("[data-set-theme]").forEach((b) =>
    b.addEventListener("click", () => applyTheme(b.getAttribute("data-set-theme"))));
  const fontDown = document.getElementById("fontDown");
  const fontUp = document.getElementById("fontUp");
  if (fontDown) fontDown.addEventListener("click", () => applySize(sizes[Math.max(0, sizes.indexOf(currentSize()) - 1)]));
  if (fontUp) fontUp.addEventListener("click", () => applySize(sizes[Math.min(sizes.length - 1, sizes.indexOf(currentSize()) + 1)]));

  // 阅读设置弹层
  const settingsBtn = document.getElementById("settingsBtn");
  const settingsPanel = document.getElementById("settingsPanel");
  function setSettings(open) {
    if (!settingsBtn || !settingsPanel) return;
    settingsPanel.classList.toggle("open", open);
    settingsBtn.setAttribute("aria-expanded", String(open));
  }
  if (settingsBtn && settingsPanel) {
    settingsBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      setSettings(!settingsPanel.classList.contains("open"));
    });
    document.addEventListener("click", (e) => {
      if (!settingsPanel.contains(e.target) && !settingsBtn.contains(e.target)) setSettings(false);
    });
  }

  // 移动端目录抽屉
  const menuBtn = document.getElementById("menuBtn");
  const drawer = document.getElementById("sidebarLeft");
  const backdrop = document.getElementById("drawerBackdrop");
  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle("open", open);
    if (backdrop) backdrop.classList.toggle("open", open);
    if (menuBtn) menuBtn.setAttribute("aria-expanded", String(open));
    body.classList.toggle("no-scroll", open && isMobile());
    if (open) {
      const active = drawer.querySelector(".chapter-list a.active");
      if (active) active.scrollIntoView({ block: "center" });
    }
  }
  if (menuBtn && drawer) {
    menuBtn.addEventListener("click", () => setDrawer(!drawer.classList.contains("open")));
    if (backdrop) backdrop.addEventListener("click", () => setDrawer(false));
    const closeBtn = document.getElementById("drawerClose");
    if (closeBtn) closeBtn.addEventListener("click", () => setDrawer(false));
    drawer.addEventListener("click", (e) => {
      if (e.target.closest("a") && isMobile()) setDrawer(false);
    });
    window.addEventListener("resize", () => { if (!isMobile()) setDrawer(false); });
  }

  // 未包裹的表格补充横向滚动容器
  document.querySelectorAll(".article-wrap table").forEach((t) => {
    if (t.parentElement && !t.parentElement.classList.contains("table-wrap")) {
      const w = document.createElement("div");
      w.className = "table-wrap";
      t.parentNode.insertBefore(w, t);
      w.appendChild(t);
    }
  });

  // 阅读进度条 + 大纲滚动高亮 + 移动端顶栏随滚动隐藏
  const bar = document.getElementById("progressBar");
  const topbar = document.getElementById("topbar");
  const tocLinks = Array.from(document.querySelectorAll(".toc-list a, .chapter-outline a"));
  const headingIds = Array.from(new Set(tocLinks.map((a) => a.getAttribute("href").slice(1))));
  const headings = headingIds.map((id) => document.getElementById(id)).filter(Boolean);
  let lastY = window.scrollY;
  let ticking = false;
  function onScroll() {
    ticking = false;
    const y = window.scrollY;
    if (bar) {
      const h = root.scrollHeight - window.innerHeight;
      bar.style.width = h > 0 ? Math.min(100, (y / h) * 100) + "%" : "0%";
    }
    if (topbar) {
      const hide = isMobile() && y > 120 && y > lastY + 4 && !(settingsPanel && settingsPanel.classList.contains("open"));
      if (hide) topbar.classList.add("is-hidden");
      else if (y < lastY - 4 || y <= 120) topbar.classList.remove("is-hidden");
    }
    lastY = y;
    if (headings.length) {
      let activeId = headings[0].id;
      for (const el of headings) {
        if (el.getBoundingClientRect().top <= 110) activeId = el.id;
      }
      tocLinks.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === "#" + activeId));
    }
  }
  window.addEventListener("scroll", () => {
    if (!ticking) { ticking = true; window.requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();

  // 脚注悬浮即时预览（仅限可悬停的桌面设备；触屏直接跳到脚注）
  const tip = document.getElementById("fnTooltip");
  if (tip && window.matchMedia("(hover: hover)").matches) {
    document.querySelectorAll("a[data-footnote]").forEach((a) => {
      a.addEventListener("mouseenter", () => {
        tip.textContent = a.getAttribute("data-footnote");
        tip.style.display = "block";
        const r = a.getBoundingClientRect();
        tip.style.left = Math.min(window.innerWidth - tip.offsetWidth - 16, Math.max(12, r.left)) + "px";
        tip.style.top = Math.min(window.innerHeight - tip.offsetHeight - 16, r.bottom + 8) + "px";
      });
      a.addEventListener("mouseleave", () => { tip.style.display = "none"; });
    });
  }

  // SVG 插图灯箱放大
  const lb = document.getElementById("lightbox");
  const lbImg = document.getElementById("lightboxImg");
  function closeLightbox() {
    if (lb && lb.classList.contains("open")) { lb.classList.remove("open"); body.classList.remove("no-scroll"); }
  }
  if (lb && lbImg) {
    document.querySelectorAll("figure.epub-image-figure img").forEach((img) => {
      img.addEventListener("click", () => {
        lbImg.src = img.src;
        lbImg.alt = img.alt;
        lb.classList.add("open");
        body.classList.add("no-scroll");
      });
    });
    lb.addEventListener("click", closeLightbox);
  }

  // 客户端全文中文搜索
  const searchModal = document.getElementById("searchModal");
  const searchBtn = document.getElementById("searchBtn");
  const searchClose = document.getElementById("searchClose");
  const searchInput = document.getElementById("searchInput");
  const searchResults = document.getElementById("searchResults");
  const basePrefix = root.getAttribute("data-base") || "./";
  const hintHtml = searchResults ? searchResults.innerHTML : "";
  let indexCache = null;

  async function ensureIndex() {
    if (indexCache) return indexCache;
    const res = await fetch(basePrefix + "search-index.json");
    indexCache = await res.json();
    return indexCache;
  }
  function openSearch() {
    if (!searchModal) return;
    setSettings(false);
    setDrawer(false);
    searchModal.classList.add("open");
    body.classList.add("no-scroll");
    if (searchInput) { searchInput.focus(); searchInput.select(); }
    ensureIndex().catch(() => {});
  }
  function closeSearch() {
    if (searchModal && searchModal.classList.contains("open")) {
      searchModal.classList.remove("open");
      body.classList.remove("no-scroll");
    }
  }
  if (searchBtn) searchBtn.addEventListener("click", openSearch);
  if (searchClose) searchClose.addEventListener("click", closeSearch);
  if (searchModal) {
    searchModal.addEventListener("click", (e) => { if (e.target === searchModal) closeSearch(); });
  }
  const typing = () => ["INPUT", "TEXTAREA"].includes(document.activeElement.tagName);
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openSearch(); }
    else if (e.key === "/" && !typing()) { e.preventDefault(); openSearch(); }
    else if (e.key === "Escape") { closeSearch(); closeLightbox(); setSettings(false); setDrawer(false); }
    else if (!typing() && !(searchModal && searchModal.classList.contains("open")) && !e.altKey && !e.ctrlKey && !e.metaKey) {
      const prev = document.querySelector("a.pager-card.prev");
      const next = document.querySelector("a.pager-card.next");
      if (e.key === "ArrowLeft" && prev) window.location.href = prev.href;
      if (e.key === "ArrowRight" && next) window.location.href = next.href;
    }
  });

  function escHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  if (searchInput && searchResults) {
    let timer = null;
    searchInput.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(runSearch, 120);
    });
    async function runSearch() {
      const q = searchInput.value.trim();
      if (!q) { searchResults.innerHTML = hintHtml; return; }
      let idx;
      try { idx = await ensureIndex(); }
      catch (e) { searchResults.innerHTML = '<div class="search-empty">搜索索引加载失败，请检查网络后重试</div>'; return; }
      const ql = q.toLowerCase();
      const re = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
      const hits = [];
      for (const doc of idx) {
        const tl = doc.title.toLowerCase();
        const bl = doc.text.toLowerCase();
        const pos = bl.indexOf(ql);
        if (tl.includes(ql) || pos >= 0) {
          const start = Math.max(0, (pos >= 0 ? pos : 0) - 36);
          const rawSnip = doc.text.slice(start, start + 110);
          const safeSnip = escHtml(rawSnip).replace(re, (m) => "<mark>" + m + "</mark>");
          hits.push({ doc, score: (tl.includes(ql) ? 10 : 0) + (pos >= 0 ? 5 : 0), snip: (start > 0 ? "…" : "") + safeSnip + "…" });
        }
      }
      hits.sort((a, b) => b.score - a.score);
      if (!hits.length) {
        searchResults.innerHTML = '<div class="search-empty">未找到匹配结果</div>';
        return;
      }
      searchResults.innerHTML = hits.slice(0, 20).map((h) =>
        `<a class="search-hit" href="${basePrefix}${h.doc.url}">` +
        `<div class="search-hit-meta">${escHtml(h.doc.book)}</div>` +
        `<div class="search-hit-title">${escHtml(h.doc.title)}</div>` +
        `<div class="search-hit-snip">${h.snip}</div></a>`
      ).join("");
    }
  }
})();
"""


def _esc(s: str) -> str:
    return html_mod.escape(s, quote=True)


ICON_MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>'
ICON_SEARCH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
ICON_TYPE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19 9 5l5 14M5.8 14h6.4M15 19l3-8 3 8M15.9 16.6h4.2"/></svg>'

# 在 <head> 中尽早应用主题与字号，避免页面加载时闪烁
HEAD_BOOT = """<meta name="theme-color" content="#1c1917"/>
  <script>try{var t=localStorage.getItem("zh_web_theme");if(t)document.documentElement.setAttribute("data-theme",t);var z=localStorage.getItem("zh_web_size");if(z)document.documentElement.style.setProperty("--reader-size",z+"px");}catch(e){}</script>"""


def _render_topbar(base_prefix: str, active_book: str | None) -> str:
    hb_cls = ' class="active"' if active_book == "se-handbook" else ""
    mg_cls = ' class="active"' if active_book == "mage" else ""
    menu_btn = (
        f'<button class="icon-btn menu-toggle" id="menuBtn" type="button" aria-label="打开目录" '
        f'aria-controls="sidebarLeft" aria-expanded="false">{ICON_MENU}</button>'
        if active_book else ""
    )
    hb_href = f"{base_prefix}se-handbook/front-01.html"
    mg_href = f"{base_prefix}mage/front-01.html"
    return f"""<div class="progress-bar" id="progressBar"></div>
<header class="topbar" id="topbar">
  <div class="topbar-inner">
    {menu_btn}
    <a class="brand" href="{base_prefix}index.html">
      <span class="brand-badge">中文版</span>
      <span class="brand-text">MAGE &amp; 软件工程手册</span>
    </a>
    <nav class="book-switch">
      <a href="{hb_href}"{hb_cls}>软件工程手册</a>
      <a href="{mg_href}"{mg_cls}>MAGE 案例研究</a>
    </nav>
    <div class="topbar-spacer"></div>
    <div class="toolbar">
      <button class="icon-btn" id="searchBtn" type="button" title="搜索 (Ctrl+K 或 /)" aria-label="搜索">{ICON_SEARCH}<span class="btn-label">搜索</span><kbd>Ctrl K</kbd></button>
      <div class="settings">
        <button class="icon-btn" id="settingsBtn" type="button" title="阅读设置" aria-label="阅读设置" aria-haspopup="true" aria-expanded="false" aria-controls="settingsPanel">{ICON_TYPE}<span class="btn-label">阅读设置</span></button>
        <div class="settings-panel" id="settingsPanel" role="dialog" aria-label="阅读设置">
          <div class="sp-label">主题</div>
          <div class="seg">
            <button type="button" data-set-theme="light">日间</button>
            <button type="button" data-set-theme="sepia">护眼</button>
            <button type="button" data-set-theme="dark">夜间</button>
          </div>
          <div class="sp-label">正文字号</div>
          <div class="seg">
            <button type="button" id="fontDown" aria-label="缩小字号">A−</button>
            <span class="font-val" id="fontVal">17px</span>
            <button type="button" id="fontUp" aria-label="放大字号">A+</button>
          </div>
          <div class="sp-books">
            <div class="sp-label">切换书籍</div>
            <a href="{hb_href}"{hb_cls}>软件工程手册</a>
            <a href="{mg_href}"{mg_cls}>MAGE 案例研究</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</header>"""


def _render_modals() -> str:
    return f"""<div class="fn-tooltip" id="fnTooltip"></div>
<div class="modal-backdrop" id="searchModal" role="dialog" aria-label="全文搜索">
  <div class="search-box">
    <div class="search-input-wrap">
      {ICON_SEARCH}
      <input type="search" id="searchInput" placeholder="搜索两本书全文…" autocomplete="off" enterkeyhint="search"/>
      <button class="search-close" id="searchClose" type="button">取消</button>
    </div>
    <div class="search-results" id="searchResults">
      <div class="search-empty">输入关键词搜索两本中文书全文（如：治理转化、预言机、对齐内核、DocAble）</div>
    </div>
  </div>
</div>
<div class="lightbox" id="lightbox"><img id="lightboxImg" src="" alt=""/></div>"""


def build_web_custom(out_dir: pathlib.Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "assets").mkdir(parents=True, exist_ok=True)
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    (out_dir / "assets" / "style.css").write_text(SITE_CSS, encoding="utf-8")
    (out_dir / "assets" / "app.js").write_text(SITE_JS, encoding="utf-8")

    search_index: list[dict] = []
    book_cards_html: list[str] = []

    for book_key in ("se-handbook", "mage"):
        print(f"== 构建自建静态书站: {book_key} ==")
        data = ext.extract_book_for_web(book_key)
        cfg = data["cfg"]
        slug = cfg["url_slug"]
        book_dir = out_dir / slug
        (book_dir / "assets").mkdir(parents=True, exist_ok=True)

        # 写入封面与全部高清矢量 SVG
        (book_dir / "assets" / "cover.jpg").write_bytes(data["cover_jpg"])
        for rel, content in data["assets"].items():
            dest = book_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)

        chapters = data["chapters"]
        pdf_url = f"{cfg['release_base']}/{cfg['pdf_filename']}"
        epub_url = f"{cfg['release_base']}/{cfg['epub_filename']}"
        start_href = next((c["href"] for c in chapters if c["kind"] == "frontmatter"), chapters[0]["href"])

        # 首页书架卡片
        book_cards_html.append(f"""<article class="book-card">
  <a class="book-card-cover" href="{slug}/{start_href}">
    <img src="{slug}/assets/cover.jpg" alt="{_esc(cfg['title'])} 封面"/>
  </a>
  <div class="book-card-body">
    <h2>{_esc(cfg['short_title'])}</h2>
    <div class="book-en">{_esc(cfg['en_title'])} · {_esc(cfg['en_subtitle'])}</div>
    <p class="book-desc">{_esc(cfg['summary'])}</p>
    <div class="card-actions">
      <a class="btn-primary" href="{slug}/{start_href}">开始在线阅读 →</a>
      <a class="btn-ghost" href="{pdf_url}">PDF</a>
      <a class="btn-ghost" href="{epub_url}">EPUB</a>
    </div>
  </div>
</article>""")

        # 左侧目录分组
        def _build_left_nav(active_slug: str, outline: list[dict]) -> str:
            groups = [
                ("扉页与导读", [c for c in chapters if c["kind"] in ("copyright", "frontmatter")]),
                ("正文各章", [c for c in chapters if c["kind"] == "chapter"]),
                ("附录与后记", [c for c in chapters if c["kind"] in ("appendix-a", "appendix-b", "backmatter")]),
            ]
            parts = [
                '<div class="drawer-head"><span>目录</span>'
                '<button class="drawer-close" id="drawerClose" type="button" aria-label="关闭目录">×</button></div>',
                f'<div class="sidebar-book-head">'
                f'<div class="sidebar-book-title">{_esc(cfg["short_title"])}</div>'
                f'<div class="sidebar-downloads">'
                f'<a href="{pdf_url}">PDF</a>'
                f'<a href="{epub_url}">EPUB</a>'
                f'<a href="../index.html">书架</a>'
                f'</div></div>'
            ]
            for gname, items in groups:
                if not items:
                    continue
                parts.append(f'<div class="nav-group-label">{gname}</div><ul class="chapter-list">')
                for c in items:
                    is_active = c["slug"] == active_slug
                    cls = ' class="active" aria-current="page"' if is_active else ""
                    sub = ""
                    if is_active and outline:
                        sub = '<ul class="chapter-outline">' + "".join(
                            f'<li class="lv{h["level"]}"><a href="#{_esc(h["id"])}">{_esc(h["text"])}</a></li>'
                            for h in outline
                        ) + "</ul>"
                    li_cls = ' class="has-outline"' if sub else ""
                    parts.append(f'<li{li_cls}><a href="{c["href"]}"{cls}>{_esc(c["toc_label"])}</a>{sub}</li>')
                parts.append("</ul>")
            return "\n".join(parts)

        # 生成每一章 HTML
        for i, ch in enumerate(chapters):
            prev_ch = chapters[i - 1] if i > 0 else None
            next_ch = chapters[i + 1] if i + 1 < len(chapters) else None
            pager_parts = []
            if prev_ch:
                pager_parts.append(
                    f'<a class="pager-card prev" href="{prev_ch["href"]}">'
                    f'<span class="pager-dir">← 上一章</span>'
                    f'<span class="pager-title">{_esc(prev_ch["toc_label"])}</span></a>'
                )
            else:
                pager_parts.append("<div></div>")
            if next_ch:
                pager_parts.append(
                    f'<a class="pager-card next" href="{next_ch["href"]}">'
                    f'<span class="pager-dir">下一章 →</span>'
                    f'<span class="pager-title">{_esc(next_ch["toc_label"])}</span></a>'
                )

            toc_lis = "\n".join(
                f'<li class="lv{h["level"]}"><a href="#{_esc(h["id"])}">{_esc(h["text"])}</a></li>'
                for h in ch["toc_headings"]
            )
            right_aside = (
                f'<aside class="sidebar-right"><div class="toc-title">本页大纲</div>'
                f'<ul class="toc-list">{toc_lis or "<li style=color:var(--muted)>本章无子节</li>"}</ul></aside>'
            )

            page_html = f"""<!DOCTYPE html>
<html lang="zh-CN" data-base="../">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{_esc(ch["toc_label"])} — {_esc(cfg["short_title"])}</title>
  {HEAD_BOOT}
  <link rel="stylesheet" href="../assets/style.css"/>
</head>
<body>
{_render_topbar("../", book_key)}
<div class="reader-shell">
  <aside class="sidebar-left" id="sidebarLeft">
    {_build_left_nav(ch["slug"], ch["toc_headings"])}
  </aside>
  <main class="reader-main">
    <article class="article-wrap">
      {ch["body_html"]}
    </article>
    <nav class="chapter-pager">
      {"".join(pager_parts)}
    </nav>
  </main>
  {right_aside}
</div>
<div class="drawer-backdrop" id="drawerBackdrop"></div>
{_render_modals()}
<script src="../assets/app.js"></script>
</body>
</html>
"""
            (book_dir / ch["href"]).write_text(page_html, encoding="utf-8")
            search_index.append({
                "book": cfg["short_title"],
                "title": ch["toc_label"],
                "url": f"{slug}/{ch['href']}",
                "text": ch["plain_text"],
            })

        # 书本目录默认跳转到首篇前言
        (book_dir / "index.html").write_text(
            f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"/>'
            f'<meta http-equiv="refresh" content="0; url={start_href}"/></head>'
            f'<body><a href="{start_href}">正在跳转…</a></body></html>',
            encoding="utf-8",
        )
        print(
            f"  {book_key} 完成: 章节={data['stats']['chapters']} | "
            f"矢量插图={data['stats']['figures']} | 矢量公式={data['stats']['equations']}"
        )

    # 写入全文检索索引 JSON
    (out_dir / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False), encoding="utf-8"
    )

    # 写入书架首页 index.html
    home_html = f"""<!DOCTYPE html>
<html lang="zh-CN" data-base="./">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>MAGE &amp; 软件工程手册 — 中文在线阅读</title>
  {HEAD_BOOT}
  <link rel="stylesheet" href="assets/style.css"/>
</head>
<body>
{_render_topbar("./", None)}
<section class="home-hero">
  <div class="home-kicker">UNOFFICIAL CHINESE EDITION · 非官方中文译本</div>
  <h1>基于模型的智能体工程 &amp; 软件工程手册</h1>
  <p>原著作者：James C. Davis（普渡大学 · MIT License）</p>
</section>
<section class="shelf-grid">
  {"".join(book_cards_html)}
</section>
<footer class="home-footer">
  <div>
    上游原著仓库：<a href="https://github.com/davisjam/model-based-agentic-software-engineering">davisjam/model-based-agentic-software-engineering</a>
    <span class="sep">&nbsp;·&nbsp;</span>
    中文翻译仓库：<a href="https://github.com/ReShweiCi/model-based-agentic-software-engineering-zh-cn">ReShweiCi/model-based-agentic-software-engineering-zh-cn</a>
    <span class="sep">&nbsp;·&nbsp;</span>
    <a href="https://github.com/ReShweiCi/model-based-agentic-software-engineering-zh-cn/releases/tag/zh-pdf-latest">PDF &amp; EPUB 下载</a>
  </div>
</footer>
{_render_modals()}
<script src="assets/app.js"></script>
</body>
</html>
"""
    (out_dir / "index.html").write_text(home_html, encoding="utf-8")
    print(f"== 全部构建完成: {out_dir} ==")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the static Chinese online reader site.")
    ap.add_argument("--out-dir", type=pathlib.Path, default=REPO_ROOT / "dist" / "web-custom")
    args = ap.parse_args()
    build_web_custom(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
