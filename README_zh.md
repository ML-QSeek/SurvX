# SurvX
> 📖 阅读 [English](README.md)
> 本仓库为 SurvX 范式对应的参考架构与原型代码实现。

## 当前状态：理念验证原型，而非开箱即用的框架，不具备生产能力。
SurvX 是一套用于构建智能系统的范式，既可适配各类 AI 底座，也可脱离 AI 独立使用。本项目旨在长期探索未来开发形态与智能系统的组织方式，不预设明确的开发进度规划。

它的一个前沿探索方向为 **XGI——Xenogenic General Intelligence**，一种不预设起源与形态、能够依靠自演化实现长期存续的智能。
（XGI 概念与 AGI 相近，当下 AGI 通常偏向指代类人智能，因此使用 Xenogenic 来做概念上的区分）

## 快速开始
> ⚠️ 本项目为理念验证原型，尚未发布 PyPI 包，请克隆完整仓库进行本地运行。

**1. 获取代码**
```bash
git clone https://github.com/ML-QSeek/SurvX
cd SurvX
```

**2. 安装依赖**
确保本地已安装 Python（推荐 >=3.10）。项目依赖分散在各个子实例中，按需安装。

**3. 启动 studio**
```bash
cd instances/survx_studio
python main.py
```

**4. 打开浏览器**
访问 `http://localhost:8090`，在 studio 中可以：
- 运行内置 demo
- 创建、开发你自己的项目

> 如果你不需要 studio，也可以直接使用引擎开发项目。
> 详见 [developer-guide.md](docs/developer-guide.md)。

🧪 原型仅供研究探索，不建议直接投入生产环境。

## 文档

版本变更记录：[CHANGELOG.md](CHANGELOG.md)

参与贡献指南：[CONTRIBUTING.md](CONTRIBUTING.md)

框架设计说明：[design.md](docs/design.md)

开发者指南：[developer-guide.md](docs/developer-guide.md)

范式即解法框架：[paradigm-as-solution-framework.md](docs/paradigm-as-solution-framework.md)

XGI：泛生命智能的数学模型：[XGI-A-Mathematical-Model-of-Pan-Life-Intelligence.md](docs/XGI-A-Mathematical-Model-of-Pan-Life-Intelligence.md)

SurvX-XGI 长期研究策略：[SurvX-XGI-AI-Research-Longterm-Strategy.md](docs/SurvX-XGI-AI-Research-Longterm-Strategy.md)

以下是引擎核心上下文文档：

核心语义：[core-context.md](survx/survx_engine/prompts/core-context.md)

建模流程：[modeling-flow.md](survx/survx_engine/prompts/modeling-flow.md)

生命周期：[lifecycle.md](survx/survx_engine/prompts/lifecycle.md)

语法规范：[syntax.md](survx/survx_engine/prompts/syntax.md)

## 工程结构
```
├── survx/               # 核心模块
│   └── survx_engine/    # 引擎
├── models/              # 开发目录
├── works/               # 工作工场，承载迭代、改进与灰度验证
│   ├── solutions/       # 解决方案
│   ├── tools/           # 工具
│   └── examples/        # 开发示例
├── instances/           # 可运行实例
│   └── survx_studio/    # 开发管理工具
└── docs/                # 设计文档
```

## 许可证
- 根目录及大部分子目录：**MIT**，详见 [LICENSE](LICENSE)
- `works/solutions`：其中部分子项目采用 **AGPL-3.0**，详见对应子目录内的 LICENSE 文件
