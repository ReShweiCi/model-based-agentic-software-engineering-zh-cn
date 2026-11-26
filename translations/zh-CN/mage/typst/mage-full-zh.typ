// mage-full-zh.typ — 《基于模型的智能体工程（MAGE）》完整中文版排版模板（段首缩进两字符）

#import "../../se-handbook/typst/typography-zh.typ": palette, font-body, font-display, font-mono
#import "../../se-handbook/typst/components-zh.typ": hb-callout, hb-figure, hb-read-further, hb-frontmatter

#let mage-mode = state("mage-mode", "chapter") // "chapter" | "backmatter" | "appendix-a" | "appendix-b"
#let mage-set-mode(m) = mage-mode.update(m)
#let mage-chapter = counter("mage-chapter")

#let mage-page-setup = (
  paper: "us-letter",
  margin: (top: 1.0in, bottom: 1.0in, inside: 1.2in, outside: 1.05in),
  fill: palette.paper,
  numbering: "1",
  number-align: center,
  footer-descent: 0.5em,
)

#let mage-styles(body) = {
  set text(font: font-body, size: 10.5pt, fill: palette.ink, lang: "zh", region: "cn")
  set par(justify: true, leading: 0.82em, first-line-indent: (amount: 2em, all: true), spacing: 0.72em)
  show link: set text(fill: palette.accent)

  show heading: set text(font: font-display)
  show heading.where(level: 1): it => {
    if it.has("label") and it.label == <hb-fore> {
      none
    } else {
      pagebreak(weak: true)
      block(above: 0pt, below: 1.15em)[
        #set par(first-line-indent: 0em)
        #context {
          let m = mage-mode.get()
          if m == "chapter" {
            mage-chapter.step()
            context text(size: 9pt, tracking: 0.18em, fill: palette.accent, weight: 700)[第 #mage-chapter.display() 章]
            v(0.35em, weak: true)
          } else if m == "appendix-a" {
            text(size: 9pt, tracking: 0.18em, fill: palette.accent, weight: 700)[附录 A]
            v(0.35em, weak: true)
          } else if m == "appendix-b" {
            text(size: 9pt, tracking: 0.18em, fill: palette.accent, weight: 700)[附录 B]
            v(0.35em, weak: true)
          }
        }
        #text(size: 23pt, weight: 700, fill: palette.ink)[#it.body]
        #v(0.3em, weak: true)
        #line(length: 100%, stroke: 0.8pt + palette.rule)
      ]
    }
  }
  show heading.where(level: 2): it => {
    set text(size: 14pt, weight: 700, fill: palette.ink)
    block(above: 1.5em, below: 0.55em, sticky: true)[#set par(first-line-indent: 0em); #it.body]
  }
  show heading.where(level: 3): it => {
    set text(size: 11.5pt, weight: 700, fill: palette.muted)
    block(above: 1.1em, below: 0.45em, sticky: true)[#set par(first-line-indent: 0em); #it.body]
  }
  show heading.where(level: 4): it => {
    set text(size: 10.5pt, weight: 700, fill: palette.ink)
    block(above: 0.9em, below: 0.35em, sticky: true)[#set par(first-line-indent: 0em); #it.body]
  }

  set list(indent: 1.2em, body-indent: 0.5em, spacing: 0.55em)
  set enum(indent: 1.2em, body-indent: 0.5em, spacing: 0.55em)
  show list: set par(first-line-indent: 0em)
  show enum: set par(first-line-indent: 0em)

  // 引用块
  show quote: it => block(
    width: 100%,
    fill: palette.panel,
    stroke: (left: 2pt + palette.rule),
    inset: (left: 11pt, right: 11pt, top: 8pt, bottom: 8pt),
    above: 0.9em, below: 0.9em,
    {
      set par(first-line-indent: 0em, leading: 0.78em)
      set text(size: 10pt, fill: palette.muted)
      it.body
    }
  )

  // 三线表
  set table(stroke: none, inset: (x: 0.65em, y: 0.55em))
  set table.hline(stroke: 0.5pt + palette.muted)
  show table.cell.where(y: 0): set text(font: font-display, weight: 700, size: 9pt)
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: table): set block(breakable: true)
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
      set par(justify: false, first-line-indent: 0em, leading: 0.7em)
      set text(size: 9.2pt)
      it
    },
  )

  // 代码块
  show raw.where(block: true): it => block(
    width: 100%, fill: palette.code-bg, inset: 8pt, radius: 3pt,
    breakable: true,
    {
      set par(first-line-indent: 0em, leading: 0.62em)
      text(font: font-mono, size: 8.5pt)[#it]
    },
  )
  show raw.where(block: false): it => box(
    fill: palette.code-bg, inset: (x: 3pt, y: 0pt), outset: (y: 2pt), radius: 2pt,
    text(font: font-mono, size: 8.8pt)[#it],
  )

  // 图表题注（左对齐）
  show figure.caption: it => align(left, block(width: 100%)[
    #set par(justify: true, leading: 0.75em, first-line-indent: 0em)
    #text(size: 9pt, fill: palette.muted)[
      #if it.numbering == none [#it.body] else [
        #text(font: font-display, weight: 700, fill: palette.accent)[#it.supplement #context it.counter.display(it.numbering).] #it.body
      ]
    ]
  ])

  body
}

#let mage-full(
  title: "基于模型的智能体工程（MAGE）",
  en-title: "Model-Based Agentic Engineering",
  subtitle: "软件工程案例研究（A Case Study in Software Engineering）",
  author: "James C. Davis",
  edition: "第 1 版",
  copyright-years: "2026–present",
  first-published: "2026-07-22",
  last-modified: "2026-11-25",
  frontmatter: none,
  body,
) = {
  set document(title: title, author: author)
  set page(..mage-page-setup)
  show: mage-styles

  // 封面页
  page(numbering: none, header: none, footer: none)[
    #v(1.9in)
    #set par(justify: false, first-line-indent: 0em)
    #text(font: font-display, size: 10.5pt, tracking: 0.2em, fill: palette.accent, weight: 700)[THE MAGE METHOD · 完整中文译本 · #edition]
    #v(0.7em)
    #text(font: font-display, size: 30pt, weight: 700, fill: palette.ink)[#title]
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

  // 前言与导览（罗马数字页码）
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
      v(0.4em, weak: true); strong(it)
    } else if it.level == 1 {
      v(0.4em, weak: true)
      box(inset: (left: 0.4em), strong(context {
        let m = mage-mode.at(el.location())
        let pre = if m == "chapter" {
          [第 #(mage-chapter.at(el.location()).first() + 1) 章#h(0.6em)]
        } else if m == "appendix-a" {
          [附录 A#h(0.6em)]
        } else if m == "appendix-b" {
          [附录 B#h(0.6em)]
        } else { [] }
        link(el.location(), pre + it.inner())
      }))
    } else {
      box(inset: (left: 1.8em), it)
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
