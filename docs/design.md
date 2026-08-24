# SurvX Technical Design Document Outline

This document serves as the low-level engineering implementation supplement to the **README paradigm architecture**. It covers only implementation details, source code rules, engineering structure, tool descriptions, and storage implementation — it does not reiterate top-level paradigm concepts.

Adaptation phase: concept validation prototype (non-production)

---

## 1. Project Positioning and Boundary Definition

- **Paradigm layer (README)**: pure abstract models, architecture rules, entity definitions, workflows
- **Engineering layer (this document)**: implementation, code organization, tool structure, storage solutions, runtime mechanisms
- Clarification: the paradigm is not bound to any technology stack, storage, or engine implementation. This project is a **reference prototype implementation**.

---

## 2. Repository Engineering Structure (Core Supplement)

Place your complete directory tree + per-directory responsibility descriptions here.

- **core/** — Core architecture implementation (engine, entity kernel, constraint scheduling)
  - **core/engine** — Execution engine implementation details
  - **core/studio** — Underlying support for management tools
  - **core/forge** — Human intervention, review, and workflow paradigm implementation
- **matter/** — Matter entity definition, parsing, and validation module
- **energy/** — Data deposition, temporal recording, parameter snapshot management
- **extensions/** — External component integration adapter layer
- **applications/** — Formal applications built on the framework (AGPL)
- **examples/** — Demonstration cases, minimal demos
- **tools/** — Development auxiliary toolchain
- **tests/** — Unit / entity / workflow tests
- **dist/** — Build artifacts

Key note: **repository structure ≠ user application development structure**. Applications produced by this architecture have their own independent directory conventions.

---

## 3. Developer Tool System Supplement (Engine / Forge / Studio)

The README covers concepts only; this section covers engineering positioning and responsibilities.

- **Engine**: the system runtime core scheduler F, containing dual scheduling logic for the Field engine and Ego engine
- **Forge**: human-intervention workflow paradigm, executable review framework, workflow constraint middleware layer
- **Studio**: entity visualization management, Matter/Energy inspection, contract management tools

---

## 4. Storage Layer Engineering Implementation (SQLite Approach)

The README only mentions the form; this section locks in the concrete implementation (self-imposed constraint).

- Prototype persistence solution: SQLite single-file database
- Parameters/constraints: KV snapshot storage model
- Experience/temporal data: temporal record table structure
- Replaceability note: the paradigm is not bound to SQLite; it is only used for the prototype

---

## 5. Core Module Technical Implementation Details

### 5.1 Matter Entity Parsing and Validation Mechanism

### 5.2 Energy Change Trigger and Drive Chain Implementation

### 5.3 Dual-Engine Scheduling Logic (Field / Ego)

### 5.4 Six-Dimensional Input/Output Contract Validation Implementation

### 5.5 External F Component Integration Adapter Specification

### 5.6 AI Structure Generation and Constraint Validation Pipeline

---

## 6. Two Workflow Engineering Implementation Rules

- **Evolutionary workflow**: iterative state updates, constraint feasible-domain computation, multi-version candidate management
- **Completion workflow**: contract-driven completion, chain connectivity validation, automatic structure assembly

---

## 7. Development Conventions and Architecture Constraints (Self-Imposed Hard Constraints)

**This is what you need most: mandatory rules to prevent future development from drifting off course.**

- All capabilities must be abstracted as F units; bare business logic is prohibited
- All state must belong to Matter; stray global variables are prohibited
- All behavior must be driven by Energy changes; active polling logic is prohibited
- AI may only modify structure; it may not modify execution flow or bypass the constraint layer
- Ego evolution must be Goal-driven; hardcoded evolution logic is prohibited

---

## 8. Current Prototype Capability List & Unimplemented Capabilities

- **Implemented**: basic F/Matter/Energy model, drive chain, contract validation
- **Partially implemented**: Field engine, external component integration
- **To be implemented**: complete Ego engine, self-evolution, Studio visualization, Forge review workflow

---

## 9. Version Status and Development Notes

- Current status: concept validation prototype, not production-ready
- API status: unstable, under continuous refactoring
- Iteration principle: prioritize paradigm self-consistency first, then add features

---

## 10. License (Engineering Refinement)

Refine the MIT / AGPL-3.0 division of labor, directory constraints, and derivative work rules.

> (Note: some content may be AI-generated)
