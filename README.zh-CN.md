# Model-Based Agentic Software Engineering（非官方中文译本）

> **声明**：本仓库是普渡大学 James C. Davis 教授开源项目 [davisjam/model-based-agentic-software-engineering](https://github.com/davisjam/model-based-agentic-software-engineering) 的**非官方中文翻译 Fork**。原项目采用 **MIT License** 开源，原著版权归 James C. Davis 所有。

---

## 中文版 PDF 下载

仓库本身不提交编译生成的 PDF 二进制文件。每次推送更新后，GitHub Actions 会自动使用 Typst 编译并发布最新中文 PDF 到 **[Releases 页面](https://github.com/ReShweiCi/model-based-agentic-software-engineering-zh-cn/releases/tag/zh-pdf-latest)**：

1. **《软件工程手册：一种判断与决策的方法》**（*The Software Engineering Handbook: A Judgment and Decision-Making Approach*）
   - 完整中文版（前言/导言/致谢、目录、全 11 章、结语及全部汉化矢量图）
   - 下载链接：[`software-engineering-handbook-zh.pdf`](https://github.com/ReShweiCi/model-based-agentic-software-engineering-zh-cn/releases/download/zh-pdf-latest/software-engineering-handbook-zh.pdf)
2. **《基于模型的智能体工程（MAGE）：软件工程案例研究》**（*Model-Based Agentic Engineering: A Case Study in Software Engineering*）
   - 完整中文版（前言/导读/术语表、全 7 章、结语、附录 A 工程蓝图、附录 B 实践指南、后记及全套插图）
   - 下载链接：[`mage-book-zh.pdf`](https://github.com/ReShweiCi/model-based-agentic-software-engineering-zh-cn/releases/download/zh-pdf-latest/mage-book-zh.pdf)

> 译本基于上游仓库 **2026-11-25** 修订版（Edition 1）翻译。

---

## 中文源码目录结构

所有中文翻译文件独立存放在 `translations/zh-CN/` 目录下，不修改上游英文原稿，便于后续同步上游更新：

```text
translations/zh-CN/
├── glossary.md              # 两本书共用的统一中英文术语表
├── se-handbook/             # 《软件工程手册》中文 Typst 源码与汉化 SVG
│   ├── book-zh.typ
│   ├── chapters-zh/
│   ├── figures/
│   └── typst/
└── mage/                    # 《MAGE》中文 Typst 源码与插图资源
    ├── book-zh.typ
    ├── chapters-zh/
    ├── assets/
    └── typst/
```

---

## 本地自行编译 PDF

只需安装 [Typst](https://github.com/typst/typst)（0.15+）与思源中文字体（`fonts-noto-cjk`）：

```bash
# Ubuntu / Debian 安装字体
sudo apt-get update && sudo apt-get install -y fonts-noto-cjk

# 编译《软件工程手册》中文版
typst compile --root translations/zh-CN \
  translations/zh-CN/se-handbook/book-zh.typ \
  software-engineering-handbook-zh.pdf

# 编译《MAGE》中文版
typst compile --root translations/zh-CN \
  translations/zh-CN/mage/book-zh.typ \
  mage-book-zh.pdf
```

---

## 版权与许可

- 原著及上游仓库：`Copyright (c) 2026 James C. Davis, PhD (davisjam@purdue.edu)`，详见根目录 [LICENSE](LICENSE)（MIT License）。
- 欢迎通过 Issue / PR 指正翻译中的术语或错漏，参考 [统一术语表](translations/zh-CN/glossary.md)。
