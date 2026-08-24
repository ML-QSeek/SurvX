# SurvX Developer Guide

Note: This document adopts the SurvX unified analysis and design paradigm. See docs/paradigm-as-solution-framework.md for details.

This document is intended for **source code readers, secondary developers, and module contributors**. It guides external contributors in understanding the project structure, following the architectural paradigm, and correctly developing new modules.

## 1. Core Design Principles (Development Red Lines)

All code, modules, and logic extensions must comply with four underlying principles:

1. **Paradigm uniformity**: All modules are either Field static entities or lightweight Ego evolutionary entities. Custom structures that deviate from the seven-layer/five-layer model are not permitted.
2. **Static-dynamic separation**: Runtime dynamic logic (Energy, iteration, deviation validation) is strictly separated from static structure code (structure, capability, dependencies).
3. **Convergence and solidification**: All iterative optimizations must ultimately be solidified into stable structures. Infinite expansion of temporary logic is prohibited.
4. **Unidirectional stability**: The main branch must always be usable, compilable, and runnable. Merging of destructive, incomplete code is prohibited.

## 2. Core Architectural Understanding (Required for Development)

The entire SurvX architecture consists of only three systems. All code falls within these three entity types:

### 1. Field Five-Layer Static Entity (Solidified Module)

Used for stable, goal-free, reusable, and standardizable underlying components/tools/basic capabilities.

Fixed structure: S Structure → C Capability → R Dependency → O Constraint → F Feature

Development characteristic: stable once written, rarely undergoes structural changes, only parameter fine-tuning.

### 2. Ego Seven-Layer Evolutionary Entity (Business/Core Module)

Used for core modules requiring **goal decomposition, iterative optimization, self-correction, and decision deduction**.

Adds two layers on top of Field: G Goal system, L Cognitive deviation approximation system.

Development characteristic: iterable, refactorable, capable of self-correction based on Energy data.

### 3. Energy Dynamic Runtime System

Carries all dynamic data, runtime states, temporal records, and constraint thresholds across the entire system.

All Ego iterations and Field state changes are driven by real Energy data.

## 3. Source Code Directory Development Conventions

Subsequent new code must strictly follow the layering philosophy below:

- **/core/field**: All static five-layer entity modules
- **/core/ego**: All iterable seven-layer core modules
- **/core/energy**: Dynamic data, state, records, runtime rules
- **/service**: Business assembly, upper-layer services
- **/utils**: Pure utility classes (all lightweight Field entities)
- **/docs**: Formal architecture/paradigm/development documentation

## 4. Standard New Module Development Process (Mandatory)

Any new module must complete this process. Directly writing code and piling up logic is not allowed.

### 1. Determine Attribute First: Field or Ego

- No goal, no iteration needed, pure capability output → **Field**
- Has a goal, requires iterative optimization, needs to adapt to environmental deviations → **Ego**

### 2. Documentation Before Code

Small tools may be simplified; core modules must produce a module specification document first:

- Field: describe structure and constraints clearly according to the S/C/R/O/F five layers
- Ego: describe goals and iteration logic clearly according to the G/S/C/R/O/F/L seven layers

### 3. Code Implementation and Solidification

After the document has converged, proceed with coding implementation, ensuring that **code and paradigm document are fully isomorphic**.

### 4. Self-Test and Convergence

Ensure the module's capability is closed-loop, dependencies are clear, constraints are effective, and there are no destructive compatibility issues.

## 5. Module Development Paradigm Constraints (Key Red Lines)

### Field Module Development Constraints

- Prohibited from autonomously adding iteration logic
- State changes are uniformly driven by Energy or upper-layer scheduling
- Structure is stable; frequent structural refactoring is not permitted

### Ego Module Development Constraints

- Must have a clear G goal; aimless iteration is prohibited
- All optimizations must be based on real Energy deviations; hardcoded empirical logic is prohibited
- Local optimizations must be arbitrable and converged by the top-level Ego

## 6. Branch and Merge Conventions

- **main branch is permanently stable**; direct code push is prohibited
- All features, fixes, and refactoring must be developed on newly created temporary branches
- Must pass self-testing before merging
- Changes involving architecture, paradigm, or top-level structure must first be discussed and confirmed via Issue

## 7. Documentation Development Conventions

- All formal module documentation is placed in /docs
- All documents must carry a paradigm declaration comment at the top
- Personal essays, drafts, and thought fragments are not committed to the repository
- Document descriptions must strictly align with code structure

## 8. Developer Core Understanding Summary

1. Code always serves the **paradigm structure**, not writing logic at will.
2. Static modules go through Field, dynamic iteration goes through Ego, all runtime goes through Energy.
3. Design first, then documentation, then code — this is the only development order in this project.
4. The ultimate goal of all contributions: **make the system more structured, more convergent, more iterable, and more maintainable**.

> (Note: some content may be AI-generated)
