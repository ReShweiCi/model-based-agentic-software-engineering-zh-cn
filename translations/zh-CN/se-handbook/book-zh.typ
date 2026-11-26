#import "typst/handbook-full-zh.typ": handbook-full, hb-begin-backmatter

#show: handbook-full.with(
  title: "软件工程手册",
  en-title: "The Software Engineering Handbook",
  subtitle: "一种判断与决策的方法（A Judgment and Decision-Making Approach）",
  author: "James C. Davis",
  edition: "第 1 版",
  copyright-years: "2026–present",
  first-published: "2026-09-12",
  last-modified: "2026-11-25",
  frontmatter: {
    include "chapters-zh/00-frontmatter.typ"
  },
)

#include "chapters-zh/01-software-engineering.typ"
#include "chapters-zh/02-process.typ"
#include "chapters-zh/03-teamwork.typ"
#include "chapters-zh/04-engineering-knowledge.typ"
#include "chapters-zh/05-requirements.typ"
#include "chapters-zh/06-specification.typ"
#include "chapters-zh/07-architecture.typ"
#include "chapters-zh/08-design.typ"
#include "chapters-zh/09-validation.typ"
#include "chapters-zh/10-research-and-development.typ"
#include "chapters-zh/11-failure-aware-engineering.typ"

#hb-begin-backmatter()
#include "chapters-zh/12-conclusion.typ"
