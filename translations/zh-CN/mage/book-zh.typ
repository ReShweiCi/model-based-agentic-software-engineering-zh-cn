#import "typst/mage-full-zh.typ": mage-full, mage-set-mode

#show: mage-full.with(
  title: "基于模型的智能体工程（MAGE）",
  en-title: "Model-Based Agentic Engineering",
  subtitle: "软件工程案例研究（A Case Study in Software Engineering）",
  author: "James C. Davis",
  edition: "第 1 版",
  copyright-years: "2026–present",
  first-published: "2026-07-22",
  last-modified: "2026-11-25",
  frontmatter: {
    include "chapters-zh/00-frontmatter.typ"
  },
)

#mage-set-mode("chapter")
#include "chapters-zh/01-part1.typ"
#include "chapters-zh/02a-part2-a.typ"
#include "chapters-zh/02b-part2-b.typ"
#include "chapters-zh/03a-part3-a.typ"
#include "chapters-zh/03b-part3-b.typ"
#include "chapters-zh/04-part4.typ"
#include "chapters-zh/05a-part5-a.typ"
#include "chapters-zh/05b-part5-b.typ"
#include "chapters-zh/06-part6.typ"
#include "chapters-zh/07-part7.typ"

#mage-set-mode("backmatter")
#include "chapters-zh/08-conclusion.typ"

#mage-set-mode("appendix-a")
#include "chapters-zh/09a-appendix-a-a.typ"
#include "chapters-zh/09b-appendix-a-b.typ"

#mage-set-mode("appendix-b")
#include "chapters-zh/10-appendix-b.typ"

#mage-set-mode("backmatter")
#include "chapters-zh/11-backmatter.typ"
#include "chapters-zh/12-index-bib.typ"
