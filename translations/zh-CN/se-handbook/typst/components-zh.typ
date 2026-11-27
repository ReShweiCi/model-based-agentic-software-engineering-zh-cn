// components-zh.typ — 中文版语义组件（定义框、决策框、核心理念框、图表、延伸阅读）

#import "typography-zh.typ": palette, font-display, callout-style

#let is-epub = sys.inputs.at("target", default: "pdf") == "epub"

#let hb-frontmatter(title: "", body) = {
  if is-epub {
    html.elem("div", attrs: (class: "epub-split", "data-kind": "frontmatter", "data-title": title))[]
    html.elem("header", attrs: (class: "chap"))[
      #html.elem("h1")[#title]
    ]
    body
  } else {
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
}

#let hb-callout(kind: "note", title: none, body) = {
  let style = callout-style.at(kind, default: (palette.muted, palette.panel, "注"))
  let rule-color = style.at(0)
  let fill-color = style.at(1)
  let label-text = style.at(2)
  if is-epub {
    html.elem("aside", attrs: (class: "hb-callout hb-callout-" + kind))[
      #html.elem("div", attrs: (class: "hb-callout-title"))[
        #html.elem("span", attrs: (class: "hb-callout-kind"))[#label-text]
        #if title != none and title != "" and title != label-text [
          #html.elem("span", attrs: (class: "hb-callout-heading"))[#title]
        ]
      ]
      #html.elem("div", attrs: (class: "hb-callout-body"))[#body]
    ]
  } else {
    block(
      width: 100%,
      fill: fill-color,
      stroke: (left: 2.5pt + rule-color),
      radius: (right: 3pt),
      inset: (left: 12pt, right: 12pt, top: 10pt, bottom: 10pt),
      above: 1.15em, below: 1.15em,
      breakable: true,
    )[
      #set par(leading: 0.8em, spacing: 0.7em, first-line-indent: 0em)
      #text(
        font: font-display, weight: 700, size: 9pt, fill: rule-color,
        tracking: 0.08em,
      )[#label-text#if title != none and title != "" and title != label-text [#h(0.6em)#text(fill: palette.ink, tracking: 0em)[#title]]]
      #v(0.4em, weak: true)
      #set text(size: 10pt)
      #body
    ]
  }
}

#let hb-read-further(body) = {
  if is-epub {
    html.elem("aside", attrs: (class: "hb-read-further"))[
      #html.elem("div", attrs: (class: "hb-read-further-title"))[延伸阅读 · READ FURTHER]
      #body
    ]
  } else {
    block(
      width: 100%,
      fill: palette.panel,
      stroke: (left: 2.5pt + palette.muted),
      radius: (right: 3pt),
      inset: (left: 12pt, right: 12pt, top: 10pt, bottom: 10pt),
      above: 1.5em, below: 1.1em,
      breakable: true,
    )[
      #text(font: font-display, weight: 700, size: 8.5pt, fill: palette.muted, tracking: 0.14em)[延伸阅读 · READ FURTHER]
      #v(0.55em, weak: true)
      #set text(size: 9.2pt, fill: palette.ink)
      #set smartquote(enabled: false)
      #set par(hanging-indent: 1.4em, first-line-indent: 0em, leading: 0.75em, spacing: 0.75em, justify: true)
      #body
    ]
  }
}

#let hb-figure(img, caption: none, numbered: true) = {
  if numbered {
    figure(
      img,
      caption: caption,
      kind: image,
      supplement: [图],
    )
  } else {
    figure(
      img,
      caption: caption,
      kind: image,
      supplement: [图],
      numbering: none,
    )
  }
}
