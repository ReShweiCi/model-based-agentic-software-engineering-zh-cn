// typography-zh.typ — 中文版视觉规范（沿用原书 Umber Monograph 配色体系）

#let palette = (
  ink:         rgb("#1c1917"),
  paper:       rgb("#fdfcf9"),
  panel:       rgb("#f6f4ef"),
  rule:        rgb("#e4e0d8"),
  muted:       rgb("#57534e"),
  accent:      rgb("#9a3f12"), // burnt umber
  accent-tint: rgb("#faf1e6"),
  code-bg:     rgb("#f3efe7"),
  def-rule:    rgb("#1f6fae"), def-fill:   rgb("#eef4fb"),
  good-rule:   rgb("#15803d"), good-fill:  rgb("#eef7ee"),
  inset-rule:  rgb("#7c6bb0"), inset-fill: rgb("#f2effb"),
  warn-rule:   rgb("#b23b3b"), warn-fill:  rgb("#fbeaea"),
  case-rule:   rgb("#2f5169"), case-fill:  rgb("#e7edf3"),
)

#let font-body    = ("Noto Serif CJK SC", "WenQuanYi Micro Hei")
#let font-display = ("Noto Sans CJK SC", "WenQuanYi Micro Hei")
#let font-mono    = ("Noto Sans Mono CJK SC", "WenQuanYi Micro Hei Mono")

#let callout-style = (
  definition:     (palette.def-rule,   palette.def-fill,   "定义"),
  decision:       (palette.accent,     palette.accent-tint,"决策"),
  tradeoff:       (palette.inset-rule, palette.inset-fill, "权衡"),
  "key-idea":     (palette.good-rule,  palette.good-fill,  "核心理念"),
  example:        (palette.good-rule,  palette.good-fill,  "示例"),
  "code-example": (palette.muted,      palette.code-bg,    "代码示例"),
  "case-study":   (palette.case-rule,  palette.case-fill,  "案例研究"),
  warning:        (palette.warn-rule,  palette.warn-fill,  "警示"),
  note:           (palette.muted,      palette.panel,      "注"),
  exercise:       (palette.accent,     palette.accent-tint,"练习"),
  quotation:      (palette.muted,      palette.panel,      "引语"),
)
