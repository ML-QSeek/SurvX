# SurvX Technical Design Document

## Document Overview
This document supplements the **README paradigm architecture** with concrete engineering implementation details.
It covers project structure, source rules, toolchains, storage implementation, and runtime mechanics.
High-level paradigm concepts are not repeated here.

Stage: **Concept Validation Prototype (Non-production)**

Paradigm Statement:
The top-level SurvX paradigm is **technology-agnostic**.
This document describes only the **reference prototype implementation**.

---

# Core Paradigm Philosophy
> Note: This paradigm is best understood from a functional programming perspective.
> The conceptual model does not enforce any specific programming stack or implementation.

The paradigm defines **one fundamental unit** and **two core roles**.

## Fundamental Unit: Q
**Q** is the minimal atomic capability unit.
- No complex internal structure
- Carries only **one single feature/responsibility**
- Acts as an empty container for code, algorithms, models, parameters, or external services

In SurvX:
**Native logic / algorithms / AI models / third-party systems are treated equally** and scheduled under one unified rule set.

## Two Core Roles

### Matter
A structured, stateful entity with layered internal architecture, constraints, capabilities and relationships.
A Matter can contain multiple F units and nested sub-Matters.

### Energy
Energy represents **data change events**, the **only driving force** of the entire system.
- All system behaviors are triggered by data changes
- Static persisted data is deposited Energy
- System execution is a chain reaction driven by state perturbation

---

# Three Perspectives of Matter

| Perspective | Concept | Essence |
|---|---|---|
| External | Entity | Callable functional entity, abstracted as `y=f(x)` |
| Internal | Field | Stateful, scoped operational field with rules and constraints |
| Self-referential | Ego | Self-iterable, self-evolvable entity |

An Ego is formed by attaching a **self-driving mechanism (also a Matter)** to a Field.

---

# Field & Ego Layered Architecture

## Field 5-Layer Structure (S-C-R-O-F)
- **S – Structure**: Module composition and internal architecture
- **C – Capability**: Internal functions, combinable behaviors
- **R – Relation**: External dependencies, collaborations, interfaces
- **O – Ordinance**: Rules, thresholds, constraints, boundaries
- **F – Feature**: Entity traits, exposed capabilities, non-functional attributes

## Ego 7-Layer Structure (S-C-R-O-F-G-L)
Extends Field with two additional layers:
- **G – Goal**: Self-direction, multi-objective driving (required)
- **L – Symbol**: Self-representation, self-cognition state (optional)

Architectural detail:
Ego self-cognition data is stored in a dedicated partition of the **Relation layer**.

---

# Energy System Design

All data in the system falls into three engineering categories:

1. **Parameters**
Snapshot configuration: weights, coefficients, adjustable settings.

2. **Constraints**
Runtime boundaries, thresholds, validation rules, hard limits.

3. **Experience (History)**
Time-series evolution records: logs, iteration traces, state trajectories.

## Trigger Sources
- Initial perturbation from the engine’s built-in F unit
- External input data
- Changes to deposited static data

## Core Runtime Characteristic
**All execution is data-driven. No active polling, no spontaneous logic execution.**

---

# Engine Runtime Mechanism

The Engine itself is a standard **F unit**.
Two engine types serve different Matter types.

## Field Engine
- Drives fixed, deterministic Field entities
- Starts from the Feature(F) layer
- Activates relations and capabilities
- Executes under Ordinance constraints
- For static, target-specified applications

## Ego Engine
- Drives self-evolvable Ego entities
- Starts from the Goal(G) layer
- Dynamically adjusts internal structure based on feedback
- Supports multi-objective optimization

### Engine Positioning
The engine is an **execution manager**, not a decision-maker.
Lifecycle and behavior boundaries are governed by the **Ordinance layer**.

---

# Language & Contract System

## Language Form
- **F units**: Implementable in any host language
- **Matter / Ego**: Declarative descriptive syntax with structural rules and contracts

## Six-Dimensional I/O Contract
All entity interfaces are defined by six orthogonal contract dimensions:

1. **Structure State**: Data schema and format definition
2. **Value State**: Numeric range and valid value constraints
3. **Logic State**: Execution status tags and business results
4. **Temporal State**: Timing, frequency, timeout and rhythm rules
5. **Environment State**: Data source, destination, external interaction tracing
6. **Metadata State**: Descriptive attributes, versioning and annotations

### Contract Purpose
- Enables automatic system-level linkage and validation
- Serves as the primary specification for AI structural generation
- Standardizes all internal and external component integration

---

# External Component Integration

Any external program, framework or service can join the SurvX system:

1. **Basic Integration**
Wrap external capability into an **F unit** for immediate data-driven scheduling.

2. **Advanced Evolution**
Gradually add Structure, Capability, Relation, Ordinance, and Goal layers
to upgrade an F into a full **Matter entity**, supporting full lifecycle management and self-evolution.

---

# AI Positioning & Constraints

In SurvX:
- AI **does not execute logic directly**
- AI **does not control runtime flow**
- AI only generates and modifies **Matter structural blueprints**

## AI Boundaries
- **Goal layer** defines optimization direction
- **Ordinance layer** enforces hard boundaries
- All AI-generated structures pass through constraint validation pipelines

AI acts purely as a **structure creator and optimizer**, never an executor.

---

# Two Fundamental Workflows

All development and evolution in SurvX relies on two workflow paradigms:

## 1. Evolution Workflow
Iterative state update within feasible constraint domains.
Generates multiple candidate states and selects optimal results via global evaluation.

## 2. Completion Workflow
Contract-driven structural completion.
Fills missing capabilities and links to form complete input-output pipelines.

Most practical scenarios use **hybrid completion + evolution**.

---

# Project Positioning & Boundaries

- **Paradigm Layer (README)**: Abstract rules, universal models, conceptual workflows
- **Engineering Layer (This Document)**: Concrete implementation, code structure, storage, runtime logic

The paradigm is generic and stack-independent.
This repository is an **official reference prototype**.

---

# Repository Structure


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

Important:
**Repo structure ≠ end-user application structure**
Built SurvX applications have independent lightweight structures.

---

# Developer Tool System

## Engine
Core runtime dispatcher for all data-driven execution.

## Forge
Human intervention framework: configurable review, audit, compliance middleware.

## Studio
Visual management platform:
Matter/Energy inspection, contract management, topology visualization.

---

# Storage Implementation (SQLite Prototype)

Prototype fixed storage strategy:

1. **Snapshot Data (Params / Constraints)**
Key-Value storage for instantaneous state.

2. **Time-Series Data (Experience)**
Structured time-series table for evolution history.

Note:
SQLite is only for prototype validation.
The paradigm supports arbitrary database replacement in production.

---

# Core Module Implementation Details

## 13.1 Matter Parsing & Validation
Structural validation, nested rule checking, registration lifecycle control.

## 13.2 Energy Trigger & Driving Pipeline
Full data-change propagation chain:
Perturbation → Dispatch → Execution → State Deposit.

## 13.3 Dual-Engine Scheduling Logic
Deterministic Field scheduling + goal-based Ego scheduling.

## 13.4 Six-Dimension Contract Validation
Unified validator for all entity input/output.

## 13.5 External F Component Adaptation
Standard wrapping, registration, constraint and access rules.

## 13.6 AI Generation & Constraint Pipeline
Blueprint generation → contract check → ordinance filtering → deployment.

---

# Development Rules & Architecture Constraints (Strict)

1. All capabilities must be abstracted as **F units**. No bare business logic.
2. All states must belong to **Matter**. No global floating state.
3. All behaviors must be driven by **Energy changes**. No active polling.
4. AI can only modify **structure**, never execution flow or constraints.
5. Ego evolution must be **goal-driven**. No hardcoded evolution logic.

---

# Prototype Capability Status

## Implemented
- Basic F / Matter / Energy models
- Data-driven driving links
- Core contract validation

## Partially Implemented
- Field engine scheduling
- Basic external component integration

## Pending
- Complete Ego self-evolution engine
- Studio visualization system
- Forge review workflow
- Full AI constraint pipeline

---

# Version Status

- Current: Concept verification prototype (non-production)
- API: Unstable & under refactoring
- Iteration Priority: Paradigm consistency > feature completeness

---

# License Engineering Specification

- **MIT**: Core architecture, kernel engine, paradigm primitives
- **AGPL-3.0**: Applications layer, integrated scenario projects

Derived works must comply with corresponding directory license rules.
