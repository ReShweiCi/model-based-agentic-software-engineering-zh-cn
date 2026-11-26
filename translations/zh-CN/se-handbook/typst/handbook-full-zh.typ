// handbook-full-zh.typ — 《软件工程手册》完整中文版排版模板（段首缩进两字符）

#import "typography-zh.typ": palette, font-body, font-display, font-mono
#import "components-zh.typ": hb-callout, hb-figure, hb-read-further

#let hb-backmatter-mode = state("hb-backmatter-mode", false)
#let hb-begin-backmatter() = hb-backmatter-mode.update(true)
#let hb-chapter = counter("hb-chapter")

#let hb-frontmatter(title: "", body) = {
  pagebreak(weak: true)
  [= #title <hb-fore>]
  block(above: 0pt, below: 1.15em)[
    #set par(first-line-indent: 0em)
    #text(font: font-display, size: 24pt, weight: 700, fill: palette.ink)[#title]
    #v(0.25em, weak: true)
    #line(length: 100%, stroke: 0.8pt + palette.rule)
  ]
  body
}

#let hb-page-setup = (
  paper: "us-letter",
  margin: (top: 1.0in, bottom: 1.0in, inside: 1.2in, outside: 1.05in),
  fill: palette.paper,
  numbering: "1",
  number-align: center,
  footer-descent: 0.5em,
)

#let hb-styles(body) = {
  set text(font: font-body, size: 10.5pt, fill: palette.ink, lang: "zh", region: "cn")
  set par(justify: true, leading: 0.82em, first-line-indent: (amount: 2em, all: true), spacing: 0.72em)
  show link: set text(fill: palette.accent)

  show heading: set text(font: font-display)
  show heading.where(level: 1): it => {
    if it.has("label") and it.label == <hb-fore> {
      none
    } else {
      pagebreak(weak: true)
      block(above: 0pt, below: 1.6em)[
        #set par(first-line-indent: 0em)
        #context if not hb-backmatter-mode.get() {
          hb-chapter.step()
          context text(size: 9pt, tracking: 0.18em, fill: palette.accent, weight: 700)[第 #hb-chapter.display() 章]
          v(0.35em, weak: true)
        }
        #text(size: 24pt, weight: 700, fill: palette.ink)[#it.body]
        #v(0.3em, weak: true)
        #line(length: 100%, stroke: 0.8pt + palette.rule)
      ]
    }
  }
  show heading.where(level: 2): it => {
    set text(size: 14pt, weight: 700, fill: palette.ink)
    block(above: 2.2em, below: 0.95em, sticky: true)[#set par(first-line-indent: 0em); #it.body]
  }
  show heading.where(level: 3): it => {
    set text(size: 11.5pt, weight: 700, fill: palette.muted)
    block(above: 1.75em, below: 0.8em, sticky: true)[#set par(first-line-indent: 0em); #it.body]
  }
  show heading.where(level: 4): it => {
    set text(size: 10.5pt, weight: 700, fill: palette.ink)
    block(above: 1.45em, below: 0.65em, sticky: true)[#set par(first-line-indent: 0em); #it.body]
  }

  set list(indent: 1.2em, body-indent: 0.5em, spacing: 0.55em)
  set enum(indent: 1.2em, body-indent: 0.5em, spacing: 0.55em)
  show list: set par(first-line-indent: 0em)
  show enum: set par(first-line-indent: 0em)

  // 三线表
  set table(stroke: none, inset: (x: 0.75em, y: 0.6em))
  set table.hline(stroke: 0.5pt + palette.muted)
  show table.cell.where(y: 0): set text(font: font-display, weight: 700, size: 9.5pt)
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: table): set block(breakable: false)
  show figure.where(kind: table): it => if it.caption == none {
    counter(figure.where(kind: table)).update(n => n - 1)
    it.body
  } else { it }
  show table: it => block(
    width: 100%,
    above: 0.7em, below: 0.4em,
    stroke: (top: 0.9pt + palette.ink, bottom: 0.9pt + palette.ink),
    {
      set align(left + top)
      set par(justify: false, first-line-indent: 0em, leading: 0.72em)
      set text(size: 9.6pt)
      it
    },
  )

  // 代码块
  show raw.where(block: true): it => block(
    width: 100%, fill: palette.code-bg, inset: 9pt, radius: 3pt,
    {
      set par(first-line-indent: 0em, leading: 0.65em)
      text(font: font-mono, size: 9pt)[#it]
    },
  )
  show raw.where(block: false): it => box(
    fill: palette.code-bg, inset: (x: 3pt, y: 0pt), outset: (y: 2pt), radius: 2pt,
    text(font: font-mono, size: 9pt)[#it],
  )

  // 图表题注（左对齐）
  show figure.caption: it => align(left, block(width: 100%)[
    #set par(justify: true, leading: 0.75em, first-line-indent: 0em)
    #text(size: 9.2pt, fill: palette.muted)[
      #if it.numbering == none [#it.body] else [
        #text(font: font-display, weight: 700, fill: palette.accent)[#it.supplement #context it.counter.display(it.numbering).] #it.body
      ]
    ]
  ])

  body
}

#let handbook-full(
  title: "",
  en-title: "",
  subtitle: "",
  author: "",
  edition: "第 1 版",
  copyright-years: "2026–present",
  first-published: "2026-09-12",
  last-modified: "2026-11-25",
  frontmatter: none,
  body,
) = {
  set document(title: title, author: author)
  set page(..hb-page-setup)
  show: hb-styles

  // 封面页
  page(numbering: none, header: none, footer: none)[
    #v(2.0in)
    #set par(justify: false, first-line-indent: 0em)
    #text(font: font-display, size: 10.5pt, tracking: 0.2em, fill: palette.accent, weight: 700)[完整中文译本 · #edition]
    #v(0.7em)
    #text(font: font-display, size: 32pt, weight: 700, fill: palette.ink)[#title]
    #v(0.35em)
    #text(font: font-display, size: 13pt, fill: palette.muted)[#en-title]
    #v(0.7em)
    #line(length: 40%, stroke: 1.5pt + palette.accent)
    #v(0.9em)
    #text(size: 12.5pt, fill: palette.ink)[#subtitle]
    #v(1.8in)
    #text(font: font-display, size: 12pt, weight: 700, fill: palette.ink)[原著：#author]
    #v(0.35em)
    #text(size: 9.5pt, fill: palette.muted)[© #author, #copyright-years · 英文初版 #first-published · 最近修订 #last-modified]
  ]

  // 版权页
  page(numbering: none, header: none, footer: none)[
    #v(0.4in)
    #set par(justify: false, leading: 0.75em, first-line-indent: 0em)
    #text(size: 11pt, fill: palette.ink)[© #author, #copyright-years]
    #v(0.4em)
    #text(size: 9.5pt, fill: palette.muted)[#edition — 英文初版于 #first-published · 最近修订于 #last-modified]
    #v(0.6em)
    #text(size: 9pt, fill: palette.muted)[原著研究受美国国家科学基金会（U.S. National Science Foundation）项目 \#2541917、\#2452533 与 \#2343596 资助。]
    #v(0.8em)
    #text(size: 9pt, fill: palette.muted)[本中文版为非官方社区译本，基于作者在 MIT License 下开源的仓库（davisjam/model-based-agentic-software-engineering）全文翻译并采用原书 Typst 视觉规范重排。原仓库版权归 James C. Davis 所有。]
  ]

  // 前言与导言（罗马数字页码）
  set page(numbering: "i", header: none)
  counter(page).update(1)
  if frontmatter != none {
    frontmatter
    pagebreak()
  }

  // 目录
  block[
    #set par(first-line-indent: 0em)
    #text(font: font-display, size: 20pt, weight: 700)[目录]
    #v(0.3em)
    #line(length: 100%, stroke: 0.8pt + palette.rule)
    #v(0.5em)
  ]
  show outline.entry: it => {
    set par(first-line-indent: 0em)
    let el = it.element
    let lbl = if el.func() == heading and el.has("label") { el.label } else { none }
    if lbl == <hb-fore> {
      v(0.45em, weak: true); strong(it)
    } else if it.level == 1 {
      v(0.35em, weak: true)
      box(inset: (left: 0.6em), strong(context {
        let pre = if not hb-backmatter-mode.at(el.location()) {
          [第 #(hb-chapter.at(el.location()).first() + 1) 章#h(0.65em)]
        } else { [] }
        link(el.location(), pre + it.inner())
      }))
    } else {
      box(inset: (left: 2.0em), it)
    }
  }
  outline(title: none, depth: 2)
  pagebreak()

  // 正文页眉与页码
  set page(
    numbering: "1",
    header: context {
      let n = counter(page).get().first()
      if n > 1 {
        set text(font: font-display, size: 8.5pt, fill: palette.muted)
        grid(columns: (1fr, auto), align: (left, right), [#title], [#subtitle])
        v(-0.45em)
        line(length: 100%, stroke: 0.4pt + palette.rule)
      }
    },
  )
  counter(page).update(1)
  body
}
