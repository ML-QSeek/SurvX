# SurvX
> 📖 Read [中文](README_zh.md)
> Reference architecture and prototype implementation for the SurvX paradigm.

## Status
This is a conceptual verification prototype, not an out-of-the-box framework and **not ready for production**.

SurvX is a paradigm for building intelligent systems. It can work with various AI backends or run independently without an AI base. The project explores the organizational form of intelligent systems under evolving states, without predefining a fixed development roadmap.

One cutting-edge direction is **XGI — Xenogenic General Intelligence**, an intelligent form that can sustain long-term evolution without predefined origins or morphology.
(XGI shares conceptual overlaps with AGI. Unlike mainstream AGI, Xenogenic focuses on evolved intelligence with emergent origins.)

## Quick Start
> ⚠️ This is a research prototype. Clone the full repository to run locally.

**1. Clone repository**
```bash
git clone https://github.com/ML-QSeek/SurvX
cd SurvX
```

**2. Install dependencies**
Make sure Python is installed (>=3.10 recommended). Dependencies are scattered across sub-instances and installed on demand.

**3. Launch studio**
```bash
cd instances/survx_studio
python main.py
```

**4. Open browser**
Visit `http://localhost:8090`. In studio you can:
- Run built-in demos
- Create and develop your own projects

> You can work directly with the engine without studio.
> See [developer-guide.md](docs/developer-guide.md).

🧪 For research and exploration only, not for production use.

## Documents

Changelog: [CHANGELOG.md](CHANGELOG.md)

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

Design Spec: [design.md](docs/design.md)

Developer Guide: [developer-guide.md](docs/developer-guide.md)

Paradigm as Solution Framework: [paradigm-as-solution-framework.md](docs/paradigm-as-solution-framework.md)

SurvX-XGI Long-Term Research Strategy: [survx-xgi-ai-research-longterm-strategy.md](docs/survx-xgi-ai-research-longterm-strategy.md)

Lifecycle: [lifecycle.md](docs/lifecycle.md)

Core engine context documents:

Core Semantics: [core-context.md](survx/survx_engine/prompts/core-context.md)

Modeling Flow: [modeling-flow.md](survx/survx_engine/prompts/modeling-flow.md)

Syntax Spec: [syntax.md](survx/survx_engine/prompts/syntax.md)

## Project Structure
```
├── survx/               # Core module
│   └── survx_engine/    # Engine
├── models/              # Model workspace
├── works/               # Workspace for iteration, improvement and grey testing
│   ├── solutions/       # Solution modules
│   ├── tools/           # Utility tools
│   └── examples/        # Example projects
├── instances/           # Runnable instances
│   └── survx_studio/    # Studio tooling
└── docs/                # Design documentation
```

## License
- Root directory and most subdirectories: **MIT**, see [LICENSE](LICENSE)
- `works/solutions`: Some subprojects are under **AGPL-3.0**, see LICENSE file inside the corresponding subdirectory.
