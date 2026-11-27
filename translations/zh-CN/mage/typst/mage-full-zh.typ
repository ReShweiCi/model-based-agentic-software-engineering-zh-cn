// mage-full-zh.typ — 《基于模型的智能体工程（MAGE）》完整中文版排版模板（段首缩进两字符）

#import "../../se-handbook/typst/typography-zh.typ": palette, font-body, font-display, font-mono
#import "../../se-handbook/typst/components-zh.typ": hb-callout, hb-figure, hb-read-further, hb-frontmatter, is-epub

#let mage-mode = state("mage-mode", "frontmatter") // "frontmatter" | "chapter" | "backmatter" | "appendix-a" | "appendix-b"
#let mage-set-mode(m) = mage-mode.update(m)
#let mage-chapter = counter("mage-chapter")
#let mage-section = counter("mage-section")
#let mage-subsection = counter("mage-subsection")

// 与原版一致的 7 点章节进度条 + 本章回答的核心问题组件
#let mage-chapter-short-titles = (
  "核心问题",
  "工程建模",
  "模型对齐",
  "演进与实践",
  "软件工厂",
  "理论体系",
  "工程职业",
)

#let mage-chapter-full-titles = (
  "新的工程问题",
  "建模",
  "对齐与治理",
  "运转中的 MAGE：通过模型开展工程",
  "众多软件工厂中的 DocAble",
  "理论",
  "软件工程职业",
)

#let mage-chapter-opener(chapter-num, question) = {
  let full-title = mage-chapter-full-titles.at(chapter-num - 1, default: "")
  if is-epub {
    html.elem("aside", attrs: (class: "mage-opener"))[
      #html.elem("div", attrs: (class: "mage-opener-progress"))[
        第 #chapter-num / 7 章 · #full-title
      ]
      #html.elem("div", attrs: (class: "mage-opener-label"))[本章回答的核心问题 · QUESTION THIS CHAPTER ANSWERS]
      #html.elem("div", attrs: (class: "mage-opener-q"))[#question]
    ]
  } else {
    block(width: 100%, above: 0.2em, below: 1.4em)[
      #set par(first-line-indent: 0em)
      #align(center)[
        #text(font: font-display, size: 9.5pt, weight: 700, fill: palette.ink)[第 #chapter-num 章 · #full-title]
      ]
      #v(0.75em)
      #layout(size => {
        let n = 7
        let w = size.width * 0.88
        let step = w / (n - 1)
        align(center)[
          #box(width: w, height: 34pt)[
            #place(top + left, dy: 4.5pt)[
              #line(length: w, stroke: 0.7pt + palette.muted)
            ]
            #for i in range(n) {
              let active = (i + 1) == chapter-num
              let x = i * step
              place(top + left, dx: x - 4.5pt, dy: 0pt)[
                #if active {
                  circle(radius: 4.5pt, fill: palette.ink, stroke: 1pt + palette.ink)
                } else {
                  circle(radius: 3.5pt, fill: palette.paper, stroke: 0.9pt + palette.muted)
                }
              ]
              place(top + left, dx: x - 28pt, dy: 14pt)[
                #box(width: 56pt)[
                  #align(center)[
                    #text(
                      font: font-display,
                      size: 7.8pt,
                      weight: if active { 700 } else { 400 },
                      fill: if active { palette.ink } else { palette.muted },
                    )[#mage-chapter-short-titles.at(i)]
                  ]
                ]
              ]
            }
          ]
        ]
      })
      #v(0.7em)
      #text(font: font-display, size: 8.8pt, weight: 700, tracking: 0.1em, fill: palette.ink)[本章回答的核心问题]
      #h(0.6em)
      #text(font: font-display, size: 7.8pt, tracking: 0.08em, fill: palette.muted)[QUESTION THIS CHAPTER ANSWERS]
      #v(0.3em)
      #text(size: 10.2pt, fill: palette.ink)[#question]
    ]
  }
}

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

  // 图表按章编号：前言连续（1, 2），正文第 1-7 章（1.1, 2.1...），附录 A/B（A.1, B.1...）
  let mage-fig-numbering(n) = context {
    let m = mage-mode.get()
    if m == "chapter" {
      [#mage-chapter.display().#n]
    } else if m == "appendix-a" {
      [A.#n]
    } else if m == "appendix-b" {
      [B.#n]
    } else {
      [#n]
    }
  }
  set figure(numbering: mage-fig-numbering)
  set figure(supplement: [表])
  show figure.where(kind: image): set figure(supplement: [图])
  show figure.where(kind: table): set figure(supplement: [表])

  show heading: set text(font: font-display)
  show heading.where(level: 1): it => {
    if it.has("label") and it.label == <hb-fore> {
      none
    } else {
      pagebreak(weak: true)
      block(above: 0pt, below: 1.6em)[
        #set par(first-line-indent: 0em)
        #context {
          let m = mage-mode.get()
          if m == "chapter" {
            mage-chapter.step()
            mage-section.update(0)
            mage-subsection.update(0)
            counter(figure.where(kind: image)).update(0)
            counter(figure.where(kind: table)).update(0)
            context text(size: 9pt, tracking: 0.18em, fill: palette.accent, weight: 700)[第 #mage-chapter.display() 章]
            v(0.35em, weak: true)
          } else if m == "appendix-a" {
            mage-section.update(0)
            mage-subsection.update(0)
            counter(figure.where(kind: image)).update(0)
            counter(figure.where(kind: table)).update(0)
            text(size: 9pt, tracking: 0.18em, fill: palette.accent, weight: 700)[附录 A]
            v(0.35em, weak: true)
          } else if m == "appendix-b" {
            mage-section.update(0)
            mage-subsection.update(0)
            counter(figure.where(kind: image)).update(0)
            counter(figure.where(kind: table)).update(0)
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
    context {
      let m = mage-mode.get()
      if m == "chapter" or m == "appendix-a" or m == "appendix-b" {
        mage-section.step()
        mage-subsection.update(0)
      }
    }
    block(above: 2.2em, below: 0.95em, sticky: true)[#set par(first-line-indent: 0em); #it.body]
  }
  show heading.where(level: 3): it => {
    set text(size: 11.5pt, weight: 700, fill: palette.muted)
    block(above: 1.75em, below: 0.8em, sticky: true)[
      #set par(first-line-indent: 0em)
      #context {
        let m = mage-mode.get()
        let sec = mage-section.get().first()
        if sec > 0 {
          if m == "chapter" {
            mage-subsection.step()
            context [#mage-chapter.display().#mage-section.display().#mage-subsection.display()#h(0.55em)]
          } else if m == "appendix-a" {
            mage-subsection.step()
            context [A.#mage-section.display().#mage-subsection.display()#h(0.55em)]
          } else if m == "appendix-b" {
            mage-subsection.step()
            context [B.#mage-section.display().#mage-subsection.display()#h(0.55em)]
          }
        }
      }#it.body
    ]
  }
  show heading.where(level: 4): it => {
    set text(size: 10.5pt, weight: 700, fill: palette.ink)
    block(above: 1.45em, below: 0.65em, sticky: true)[#set par(first-line-indent: 0em); #it.body]
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

  if is-epub {
    set text(lang: "zh", region: "cn")
    show align: it => it.body
    show line: it => html.elem("hr")
    show quote: it => html.elem("blockquote")[
      #it.body
      #if it.attribution != none {
        html.elem("footer", attrs: (class: "quote-attribution"))[—— #it.attribution]
      }
    ]
    show math.equation.where(block: true): it => html.elem("div", attrs: (class: "epub-math-block"))[
      #html.frame(block(inset: (x: 10pt, y: 6pt), fill: palette.paper)[
        #set text(font: ("Noto Serif CJK SC", "Noto Sans CJK SC"), size: 11pt, fill: palette.ink, lang: "zh", region: "cn")
        #it
      ])
    ]
    let mage-fig-numbering(n) = context {
      let m = mage-mode.get()
      if m == "chapter" {
        [#mage-chapter.display().#n]
      } else if m == "appendix-a" {
        [A.#n]
      } else if m == "appendix-b" {
        [B.#n]
      } else {
        [#n]
      }
    }
    set figure(numbering: mage-fig-numbering)
    set figure(supplement: [表])
    show figure.where(kind: image): set figure(supplement: [图])
    show figure.where(kind: table): set figure(supplement: [表])
    show figure.where(kind: table): it => if it.caption == none {
      counter(figure.where(kind: table)).update(n => n - 1)
      it.body
    } else { it }

    show heading.where(level: 1): it => {
      if it.has("label") and it.label == <hb-fore> {
        none
      } else {
        context {
          let m = mage-mode.get()
          if m == "chapter" {
            mage-chapter.step()
            mage-section.update(0)
            mage-subsection.update(0)
            counter(figure.where(kind: image)).update(0)
            counter(figure.where(kind: table)).update(0)
          } else if m == "appendix-a" or m == "appendix-b" {
            mage-section.update(0)
            mage-subsection.update(0)
            counter(figure.where(kind: image)).update(0)
            counter(figure.where(kind: table)).update(0)
          }
          context {
            let kicker = if m == "chapter" {
              "第 " + mage-chapter.display() + " 章"
            } else if m == "appendix-a" {
              "附录 A"
            } else if m == "appendix-b" {
              "附录 B"
            } else { "" }
            let attrs = (class: "epub-split", "data-kind": m, "data-kicker": kicker)
            if it.has("label") { attrs.insert("id", str(it.label)) }
            html.elem("div", attrs: attrs)[]
            html.elem("header", attrs: (class: "chap"))[
              #if kicker != "" {
                html.elem("div", attrs: (class: "kicker"))[#kicker]
              }
              #html.elem("h1")[#it.body]
            ]
          }
        }
      }
    }
    show heading.where(level: 2): it => {
      context {
        let m = mage-mode.get()
        if m == "chapter" or m == "appendix-a" or m == "appendix-b" {
          mage-section.step()
          mage-subsection.update(0)
        }
      }
      let attrs = (:)
      if it.has("label") { attrs.insert("id", str(it.label)) }
      html.elem("h2", attrs: attrs)[#it.body]
    }
    show heading.where(level: 3): it => {
      context {
        let m = mage-mode.get()
        let sec = mage-section.get().first()
        let attrs = (:)
        if it.has("label") { attrs.insert("id", str(it.label)) }
        if sec > 0 and (m == "chapter" or m == "appendix-a" or m == "appendix-b") {
          mage-subsection.step()
          context {
            let num = if m == "chapter" {
              [#mage-chapter.display().#mage-section.display().#mage-subsection.display() ]
            } else if m == "appendix-a" {
              [A.#mage-section.display().#mage-subsection.display() ]
            } else {
              [B.#mage-section.display().#mage-subsection.display() ]
            }
            html.elem("h3", attrs: attrs)[#num#it.body]
          }
        } else {
          html.elem("h3", attrs: attrs)[#it.body]
        }
      }
    }
    show heading.where(level: 4): it => {
      let attrs = (:)
      if it.has("label") { attrs.insert("id", str(it.label)) }
      html.elem("h4", attrs: attrs)[#it.body]
    }

    // 版权页（EPUB 扉页）
    html.elem("div", attrs: (class: "epub-split", "data-kind": "copyright", "data-title": "版权信息"))[]
    html.elem("section", attrs: (class: "copyright-page"))[
      #html.elem("h1", attrs: (class: "copyright-title"))[#title]
      #html.elem("p", attrs: (class: "copyright-en"))[#en-title]
      #html.elem("p", attrs: (class: "copyright-sub"))[#subtitle]
      #html.elem("p")[© #author, #copyright-years]
      #html.elem("p")[#edition — 英文初版于 #first-published · 最近修订于 #last-modified]
      #html.elem("p")[原著研究受美国国家科学基金会（U.S. National Science Foundation）项目 \#2541917、\#2452533 与 \#2343596 资助。]
      #html.elem("p")[本中文版为非官方社区译本，基于作者在 MIT License 下开源的仓库（davisjam/model-based-agentic-software-engineering）全文翻译。原仓库版权归 James C. Davis 所有。]
    ]

    if frontmatter != none {
      frontmatter
    }
    body
  } else {
    set page(..mage-page-setup)
    show: mage-styles

    // 封面页（沿用原版封面插画构图）
    page(margin: 0pt, numbering: none, header: none, footer: none, fill: palette.paper)[
      #place(top + left)[
        #block(width: 100%, height: 88.5%, clip: true)[
          #align(bottom)[
            #image("../assets/cover-artwork.png", width: 100%)
          ]
        ]
      ]
      #place(top + center, dy: 0.4in)[
        #block(width: 86%)[
          #set align(center)
          #set par(justify: false, first-line-indent: 0em, leading: 0.52em)
          #text(font: font-display, size: 38pt, weight: 800, tracking: 0.08em, fill: palette.ink)[MAGE]
          #v(0.25em)
          #text(font: font-display, size: 17pt, weight: 700, fill: palette.ink)[基于模型的智能体工程]
          #v(0.2em)
          #text(font: font-display, size: 9.5pt, tracking: 0.14em, fill: palette.muted)[MODEL-BASED AGENTIC ENGINEERING]
          #v(0.3em)
          #text(size: 11.5pt, fill: palette.accent)[软件工程案例研究 · A Case Study in Software Engineering]
          #v(0.5em)
          #line(length: 0.45in, stroke: 1.2pt + palette.accent)
          #v(0.42em)
          #text(font: font-display, size: 10.5pt, tracking: 0.14em, weight: 700, fill: palette.ink)[#upper(author)]
        ]
      ]
      #place(bottom + left, dx: 0.6in, dy: -0.45in)[
        #set par(first-line-indent: 0em)
        #text(font: font-display, size: 8.5pt, tracking: 0.08em, fill: palette.muted)[#edition · 非官方中文译本 #h(1.2em) © #author, #copyright-years]
      ]
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
}
