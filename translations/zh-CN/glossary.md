# 统一术语表（《软件工程手册》与《MAGE》共用）

所有章节翻译必须严格遵守以下术语译法；核心术语在首次出现或定义/决策框标题中可附英文括号对照，后续行文直接使用中文。

## 核心概念与全书主线
- Software Engineering -> 软件工程
- Engineering Judgment -> 工程判断 / 工程判断力
- Controlled Change -> 受控变更
- Consequential -> 关键的 / 后果重大的（视语境）
- Model-Based Agentic Engineering (MAGE) -> 基于模型的智能体工程（MAGE）
- Governed Engineering Environment (GEE) -> 受治理的工程环境（GEE）
- Alignment Kernel -> 对齐内核
- Software Factory -> 软件工厂
- Commodity Intelligence -> 商品化智能
- Coding Agent / Software Agent -> 编程智能体 / 软件智能体（简称“智能体”）
- Generative AI (GenAI) -> 生成式 AI（GenAI）
- Realization -> 实现 / 实现体（区别于 implementation 代码实现时，可译“实现方案”或“实现体”）
- Artifact -> 工件 / 制品
- Provenance -> 来源 / 溯源信息
- Repertoire -> 经验库 / 认知储备

## 流程与协作
- Plan-driven process -> 计划驱动流程
- Incremental process -> 增量式流程
- Certainty / Changeability / Decomposability -> 确定性 / 可变性 / 可分解性
- Coordination cost -> 协调成本
- Shared context -> 共享上下文
- Emergent property -> 涌现属性
- Topology / Frequency / Cost / Reliability -> 拓扑 / 频率 / 成本 / 可靠性
- Engineering management -> 工程管理
- Entry-rung problem -> 入门阶梯难题
- Tacit knowledge -> 隐性知识
- Engineering memory -> 工程记忆
- Institutional knowledge -> 组织知识 / 机构知识

## 需求、规约、架构与设计
- Requirements engineering -> 需求工程
- Candidate requirement -> 候选需求
- Commitment -> 承诺
- Obligation -> 义务 / 约束义务
- Specification -> 规约
- Environment assumption (E) -> 环境假设（E）
- Degree of freedom -> 自由度
- Overspecification / Underspecification -> 过度规约 / 规约不足
- Property -> 性质 / 属性
- Invariant -> 不变量
- Architecture -> 架构
- Boundary -> 边界
- Coupling -> 耦合
- Affordance -> 供给性 / 支撑能力（或“可用空间”）
- Design -> 设计
- Mechanism -> 机制
- Escalate -> 升级（上报至更高层决策）
- Design probe -> 设计探针
- Brownfield / Greenfield -> 存量项目（棕地）/ 新建项目（绿地）

## 验证、研发与失败学习
- Validation -> 验证
- Assurance -> 保证 / 质量保证
- Claim -> 声明 / 断言（视语境，工程论证中多译“主张”或“声明”）
- Scope -> 作用域 / 范围 / 层级
- Oracle / Oracle problem -> 预言机 / 判定基准（测试预言问题）
- Property-based testing -> 基于属性的测试
- Differential testing -> 差分测试
- Fuzzing -> 模糊测试
- Model checking -> 模型检验
- Mutation testing -> 变异测试
- Coverage / Detection power -> 覆盖率 / 检出能力
- Residual uncertainty -> 残余不确定性
- Margin / Tolerance -> 裕度 / 容差
- Discreteness -> 离散性
- Containment -> 遏制 / 隔离遏制
- Reversibility -> 可逆性
- Essential vs. accidental -> 本质（的）vs. 偶然（的）
- Elbow grease -> 苦工 / 堆人力工程投入
- Failure-aware engineering -> 面向失败的工程
- Slip vs. mistake -> 失误（Slip）vs. 错误（Mistake）
- Blameless postmortem -> 无指责复盘
- Swiss-cheese model -> 瑞士奶酪模型

## MAGE 专有治理机制
- Representation Problem -> 表示问题
- Authority Problem -> 权威问题
- Constraint -> 约束
- Sensor -> 传感器 / 观测器
- Validator -> 验证器
- Gate -> 门禁
- Governance Conversion -> 治理转化
- Structural / Behavioral / Decision Model -> 结构模型 / 行为模型 / 决策模型
- Blueprint -> 蓝图

## 治理机制目录与工程实践扩展术语
- Vibe coding -> 氛围编程（Vibe coding）
- Governance-centric -> 以治理为中心
- Oversight-centric -> 以监督为中心
- Pet tax -> “宠物税”（按变更消耗人工照料的开销）
- Cattle, not pets -> 牲口而非宠物（基础设施化、批量可替换治理）
- Guardrail -> 护栏 / 防护栏
- Move (constraint / sensor / package) -> 作用方式（约束 / 传感器 / 组合包）
- Form / Enforcement (soft / hard) -> 强制形态（软约束·概率性 / 硬约束·确定性）
- Models-bridge -> 模型桥梁（`models-bridge` 角色）
- Agent fleet -> 智能体集群 / 智能体编队
- Substrate -> 基底 / 运行底座
- Dispatch / Brief / Brief-linting -> 派发 / 任务简报 / 简报静态检查
- Worktree / Worktree isolation -> 工作树（worktree）/ 工作树隔离
- Merge train -> 合并列车
- Sentinel commit / Sentinel-first commit -> 哨兵提交 / 哨兵优先提交
- Tombstone commit -> 墓碑提交
- Drift / Drift-parity gate -> 漂移 / 漂移一致性门禁
- Source of truth (SSOT) -> 单一事实来源（SSOT）
- Census -> 普查 / 全量盘点清单
- Orphan coverage -> 孤立覆盖率 / 无归属覆盖
- Seam / Sanctioned seam -> 接缝 / 核准接入点
- Canonical walker -> 规范遍历器
- Remediation verb -> 修复动词
- Codemod-first -> 代码自动迁移优先（Codemod 优先）
- Test onion / Test tiers -> 测试洋葱 / 测试分层
- Blameless / Fault-localization -> 无指责 / 故障定位
- Formative assessment / Oral exam -> 形成性评估 / 口试
- Pod (in course project) -> 工程小组（Pod）
