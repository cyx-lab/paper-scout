# 每日论文速览（简短摘要 + Takeaway）— 2026-11-04

- 总论文数：**5**
- 已完成 LLM 摘要：**5**
- 排序：**rule_score（降序）**

> 注：本报告强调快速筛读，突出问题、方法、结论与 takeaway。


---

## Anomalous Hall Response and Real-Space Current Correlations in Rhombohedral Graphene

### 基本信息

- **arXiv:** `2611.04312v1`
- **rule_score:** `3.0`
- **authors:** Zhen Bi, Chandra M. Varma
- **categories:** cond-mat.mes-hall
- **pdf_path:** `data/pdfs/2026-11-04/3_Anomalous Hall Response and Real-Space Current Correlations in Rhombohedral Graphene__2611.04312v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2611.04312v1
- **summarized_at:** `2026-11-04T11:51:08`

### 相关主题

quantum_geometry:berry curvature · quantum_geometry:wilson loop

### 一句话摘要

通过真实空间计算研究了菱形石墨烯中的反常霍尔效应，发现它源于谷极化下电流算符闭合路径的干涉，而非平衡环流。

### 研究问题

菱形石墨烯中观测到的反常霍尔效应和磁化现象，究竟是伴随着平衡状态下的环流（类似于Haldane模型），还是源于闭合电流关联中不同传播路径之间的干涉。

### 采用方法

将多层哈密顿量投影到表面轨道上，在真实空间中展开内部传播子，并计算不同近似模型下的电流关联和霍尔电导。

### 核心 takeaway

谷极化的菱形石墨烯在均匀态下没有平衡键电流，其反常霍尔效应是由跨层传播路径构成的Wilson圈式电流关联干涉导致的。

### 为什么值得看

它澄清了近期受关注的菱形石墨烯多层体系中反常霍尔响应的微观机制，并为区分正常态与超导态的轨道响应提供了理论基础。

### 价值等级评估

- **机制澄清**
- 该工作通过真实空间路径分析，澄清了菱形石墨烯中反常霍尔效应的微观来源并非平衡环流，而是路径干涉。

### 文章类型

理论+数值

### 可能投稿去向

- **Physical Review B** `confidence=high`
- 该论文深入探讨了石墨烯多层体系的电子结构、微观电流和反常霍尔效应机制，非常符合PRB的物理范畴。

### 关键词

- Anomalous Hall effect
- Rhombohedral graphene
- Wilson loops
- Orbital magnetization
- Current correlations


---

## LaQX: A JAX Toolkit for Neural Quantum State Simulations of Lattice Quantum Many-Body Models

### 基本信息

- **arXiv:** `2611.04333v1`
- **rule_score:** `3.0`
- **authors:** Yuntian Gu, Chaohui Fan, Ruichen Li, Haoxiang Chen, Weizhong Fu, Yixiao Chen, Dingshun Lv, Weiluo Ren, Tao Xiang, Liwei Wang, Mingpu Qin, Xiang Li
- **categories:** cond-mat.str-el
- **pdf_path:** `data/pdfs/2026-11-04/3_LaQX A JAX Toolkit for Neural Quantum State Simulations of Lattice Quantum Many-Body Models__2611.04333v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2611.04333v1
- **summarized_at:** `2026-11-04T11:51:15`

### 相关主题

altermagnetism:altermagnetic

### 一句话摘要

本文介绍了 LaQX，一个基于 JAX 的开源神经量子态模拟工具包，用于研究格子量子多体模型。

### 研究问题

传统数值方法在处理高维格点费米子和自旋系统的量子多体问题时，往往受到希尔伯特空间指数级增长或量子蒙特卡洛符号问题的严重限制。

### 采用方法

利用 JAX 构建函数式的软件架构，结合神经网络变分波函数（如卷积反流、CNN-MPS 等）、变分蒙特卡洛采样、随机重构优化算法，并支持激发态、投影、绝热演化和实时动力学计算。

### 核心 takeaway

LaQX 通过模块化和函数式设计，将多种高精度的神经网络量子态算法与物理工作流集成在统一的 JAX 框架中，支持高效的并行计算和本地化扩展。

### 为什么值得看

它为强关联格子系统（如掺杂哈伯德模型、受挫磁体和 Hofstadter 模型）提供了一个开源、高性能且易于扩展和维护的计算工具库。

### 价值等级评估

- **新模型或新方法**
- 本文提出并开源了一个功能全面且高度模块化的神经量子态模拟软件框架，整合了多项前沿算法。

### 文章类型

理论+数值

### 可能投稿去向

- **SciPost Physics Codebases** `confidence=high`
- 论文明确标注为向 SciPost Physics Codebases 提交的软件介绍文章。

### 关键词

- Neural quantum states
- Variational Monte Carlo
- JAX
- Lattice models
- Hubbard model


---

## Emergence of Berry curvature dipole and nonlinear Hall effect in a novel hexagonal borophosphene allotrope

### 基本信息

- **arXiv:** `2611.04335v1`
- **rule_score:** `3.0`
- **authors:** Ranjan Kumar Tung, Dimple, Venkatesan Subramanian, Vijay Singh
- **categories:** cond-mat.mtrl-sci, physics.app-ph
- **pdf_path:** `data/pdfs/2026-11-04/3_Emergence of Berry curvature dipole and nonlinear Hall effect in a novel hexagonal borophosphene allotrope__2611.04335v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2611.04335v1
- **summarized_at:** `2026-11-04T11:51:24`

### 相关主题

quantum_geometry:berry curvature · quantum_geometry:nonlinear Hall · quantum_geometry:nonlinear Hall effect

### 一句话摘要

通过砷原子取代硼磷烯底物打破空间反演对称性，在无自旋轨道耦合的情况下实现了显著的非线性霍尔效应和可调控的贝里曲率偶极矩。

### 研究问题

二维材料中的非线性霍尔效应通常需要打破空间反演对称性并依赖贝里曲率偶极矩，但许多候选材料受限于环境稳定性和强自旋轨道耦合的依赖性，缺乏轻元素、无自旋轨道耦合且性能可调的平台。

### 采用方法

采用基于密度泛函理论的第一性原理计算、最大局域化万尼尔函数构建紧束缚模型，系统研究了砷取代硼磷烯衍生物（As@MBP和As@AMBP）的电子结构、局域轨道耦合以及单轴压缩应变对非线性霍尔响应的调控。

### 核心 takeaway

砷取代破坏了反演对称性，在不依赖自旋轨道耦合的情况下使系统打开了远超室温热涨落的能隙，并产生了有限的贝里曲率偶极矩和显著的非线性霍尔电导率；施加机械应变可使贝里曲率偶极矩增大十倍以上并实现符号翻转。

### 为什么值得看

该研究为无需强自旋轨道耦合的轻元素量子材料提供了一个极具前景的平台，展示了通过化学取代和机械应变调控非线性输运和整流器件性能的可行性。

### 价值等级评估

- **机制澄清**
- 文章深入揭示了局域轨道杂化和紧束缚跃迁参数在无自旋轨道耦合体系中驱动非线性霍尔效应的微观机制。

### 文章类型

理论+数值

### 可能投稿去向

- **Physical Review B** `confidence=high`
- 该论文侧重于二维材料的电子结构、对称性分析、紧束缚模型和基于第一性原理的输运性质计算，非常符合该期刊的收稿范围。

### 关键词

- nonlinear Hall effect
- Berry curvature dipole
- borophosphene
- inversion symmetry breaking
- strain engineering


---

## Altermagnetism-induced higher-order topological Dirac semimetals in two-dimensional nonsymmorphic systems

### 基本信息

- **arXiv:** `2611.04347v1`
- **rule_score:** `3.0`
- **authors:** Lizhou Liu, Cheng-Ming Miao, Ying-Tao Zhang, Qing-Feng Sun
- **categories:** cond-mat.mes-hall
- **pdf_path:** `data/pdfs/2026-11-04/3_Altermagnetism-induced higher-order topological Dirac semimetals in two-dimensional nonsymmorphic systems__2611.04347v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2611.04347v1
- **summarized_at:** `2026-11-04T11:52:21`

### 相关主题

altermagnetism:altermagnetism · altermagnetism:altermagnetic

### 一句话摘要

通过在三层非么正Dirac系统中引入外层d波交错磁性（altermagnetism），实现了二维高阶拓扑Dirac半金属。

### 研究问题

如何在二维系统中同时实现受对称性保护的体Dirac点与低维边界态（如高阶角态），克服边界质量项通常会使体Dirac点产生能隙的难题。

### 采用方法

构建包含层间杂化和外层d波交错磁性的三层非么正Dirac模型，利用精确的层空间分块分解分析体能带、边界态及角态的微观来源。

### 核心 takeaway

外层d波交错磁性能选择性地使特定体Dirac点保持无能隙，同时为螺旋边缘态提供交错的质量项并在角部产生零维角态，从而构筑高阶拓扑Dirac半金属。

### 为什么值得看

该研究确立了交错磁性作为在二维非么正系统中设计高阶拓扑的新机制，拓展了对无能隙系统高阶拓扑相的理解。

### 价值等级评估

- **重要进展**
- 该工作首次在二维非么正系统中结合交错磁性实现了高阶拓扑Dirac半金属，通过严格的层空间分解揭示了其微观机制，并证明了其对多种微扰的鲁棒性。

### 文章类型

理论+数值

### 可能投稿去向

- **Physical Review B** `confidence=high`
- 该论文属于凝聚态理论与数值计算范畴，深入探讨了晶格模型、拓扑相变及对称性分析，非常符合该期刊的收稿范围。

### 关键词

- Altermagnetism
- Higher-order topological semimetal
- Dirac semimetal
- Nonsymmorphic symmetry
- Layer-space decomposition


---

## Nonlinearity-Induced Suppression of Dissipation in Bath-Coupled Floquet Topological Insulators

### 基本信息

- **arXiv:** `2611.04752v1`
- **rule_score:** `2.0`
- **authors:** Bhoomija Chaurasia, Sebabrata Mukherjee
- **categories:** cond-mat.mes-hall, nlin.PS, physics.optics, quant-ph
- **pdf_path:** `data/pdfs/2026-11-04/2_Nonlinearity-Induced Suppression of Dissipation in Bath-Coupled Floquet Topological Insulators__2611.04752v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2611.04752v1
- **summarized_at:** `2026-11-04T11:52:29`

### 相关主题

soliton:soliton

### 一句话摘要

本文理论与实验发现在周期性耗散泡利拓扑绝缘体中，克尔非线性可在特定强度下形成局域拓扑边缘孤子，从而显著抑制边界耗散。

### 研究问题

拓扑保护不适用于环境诱导的耗散，如何在开体系和损耗环境中抑制边界态能量耗散是一个挑战。

### 采用方法

利用飞秒激光直写技术制备周期耦合光子晶格，结合离散非线性薛定谔方程进行数值模拟与实验测量，研究不同克尔非线性强度下的传输动力学。

### 核心 takeaway

通过将非线性强度调节至最优值，系统可形成形变保持的边缘孤子，动态抑制向外部光子浴的功率传输，实现近乎无损耗的单向边缘输运。

### 为什么值得看

该研究建立了一种通过工程化系统-浴耦合与非线性相互作用来控制开放拓扑系统中耗散的新途径，对拓扑激光器和非reciprocal光子器件具有潜在应用价值。

### 价值等级评估

- **重要进展**
- 该工作首次在实验和理论上结合了弗洛凯拓扑绝缘体、非厄米耗散系统与光学非线性，展示了利用非线性孤子抑制环境耗散的机制，具有很高的创新性。

### 文章类型

理论 + 实验

### 可能投稿去向

- **Physical Review X** `confidence=high`
- 该论文结合了深度的理论模型、数值模拟与前沿的飞秒激光直写光子实验，研究主题契合该期刊的高标准。

### 关键词

- Floquet topological insulators
- nonlinear optics
- dissipation suppression
- topological edge solitons
- open quantum systems

