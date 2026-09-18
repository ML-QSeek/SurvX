# FORGE · SurvX Embedded AI Engineering Forging System (Core Engine Perspective)
## 1. Core Overview & Engine Positioning
**Core Positioning**: FORGE and GOV are natively built-in engineering discipline modules of the SurvX engine. They have no independent architecture, do not rely on external governance systems, and fully operate on SurvX native entity models (Instance / Cat / Ego / Env / Energy).

**Design Origin**: The SurvX paradigm inherently embeds the engineering kernel of paradigm constraint, process tracing, state controllability, and asset normalization. FORGE standardizes this kernel for **incremental development scenarios**; GOV serves as the supporting closed-loop module for **legacy asset transformation scenarios**.

**Module Division (Engine Boundary)**
- **FORGE (Incremental Guard Module)**: Enforces rule constraints, process validation, evidence retention and routine auditing for all new code changes, eliminating newly introduced technical debt at engine level.
- **GOV (Legacy Transformation & Paradigm Onboarding Module)**: Not a general-purpose engineering governance tool. It is SurvX’s dedicated legacy asset processing unit. It handles governance of native engine legacy assets, as well as paradigm modeling onboarding, minimally invasive refactoring and asset normalization ingestion for external code assets.

**Engine Closed-loop Logic**: After risk remediation, paradigm modeling and state normalization via GOV, all legacy assets are converted into standardized SurvX entity assets and incorporated into FORGE’s routine protection system, realizing full lifecycle closed-loop control of assets.

## 2. FORGE Incremental Guard Module (Built-in Engine)
Scope of application: All new code changes (AI-generated, manual iteration, requirement commits). Leverages native SurvX capabilities: **Ego stores static baseline rules, Energy persists full sequential event streams, custom validation scripts enforce blocking and auditing**.

### F Fortify | Heartbeat Zone Hardening
**Module Capability**: Defines core baseline assets of the system, locks architectural invariants of heartbeat code regions and prohibits unauthorized invasive modifications.
**Engine Implementation Mechanism**
- **Ego Metadata**: Stores heartbeat zone scope, interface contracts, business invariants, baseline hashes, review admission rules (static baseline configuration).
- **Energy Event Log**: Persists hit judgments, review outcomes, change traces and responsible parties for every commit (auditable and traceable).
- **Engine Validation Logic**: Changes targeting heartbeat zones automatically escalate review levels. Violating changes trigger engine interception to prevent architecture baseline drift.

### O Observe | Decision Evidence Explicitation
**Module Capability**: Standardizes decision factors for code changes, eliminates logic black boxes of AI and manual modifications to make all changes interpretable and traceable.
**Engine Implementation Mechanism**
- **Ego Metadata**: Solidifies evidence templates, mandatory constraints for five core factors, retention specifications for AI reasoning fragments.
- **Energy Event Log**: Binds to code commit entities, recording rationale, solution, basis, risk scope and reasoning process completely.
- **Engine Validation Logic**: The engine automatically blocks merge workflows when evidence is missing or fields are non-compliant.

### R Refine | Code Archaeology & Paradigm Convergence
**Module Capability**: Periodically normalizes fragmented AI outputs, unifies project paradigms and removes ad-hoc, redundant and non-standard implementations.
**Engine Implementation Mechanism**
- **Ego Metadata**: Stores project coding paradigms, forbidden rules, redundancy criteria and convergence baselines.
- **Energy Event Log**: Retains scan results, issue lists, convergence plans and governance progress of each archaeological round.
- **Engine Validation Logic**: Identifies fragmented code, duplicate implementations and temporary hacks automatically per paradigm baselines and drives iterative convergence.

### G Gather | Engineering Asset Knowledge Base Persistence
**Module Capability**: Accumulates reusable project engineering assets to form engine-recognizable, verifiable and enforceable technical baselines.
**Engine Implementation Mechanism**
- **Ego Metadata**: Stores module paradigms, development templates, terminology dictionaries, forbidden checklists and best practices.
- **Energy Event Log**: Records full lifecycle states of asset creation, iteration, deprecation and reuse.
- **Engine Validation Logic**: New developments match knowledge base baselines preferentially and must comply with paradigm asset constraints.

### E Enforce | Routine Engineering Discipline Execution
**Module Capability**: Converts all soft paradigm rules into engine-executable CI validation and periodic auditing capabilities.
**Engine Implementation Mechanism**
- **Ego Metadata**: Defines audit checklists, validation rules, violation judgment standards and remediation closed-loop specifications.
- **Energy Event Log**: Retains all validation results, violation records, responsible persons, remediation progress and acceptance status.
- **Engine Validation Logic**: Violating changes are forcibly blocked; unresolved issues trigger persistent alerts to enforce routine engineering discipline.

## 3. GOV Legacy Transformation & Paradigm Onboarding Module (Built-in Engine)
**Core Positioning**: SurvX’s native pipeline for legacy asset processing. It executes risk mapping, reverse profiling, paradigm modeling, minimally invasive refactoring and normalization ingestion for legacy code. **It does not implement general engineering governance; it solely serves the closed-loop normalization of SurvX assets.**

**Safety Mechanism**: High-risk legacy modules can activate engine temporary isolation markers for runtime risk mitigation. Markers are lifted automatically once transformation completes.

### Two Categories of Legacy Asset Processing Specification within Engine
#### 1. Native SurvX Legacy Assets
Assets already carry complete Instance, Cat, Ego and time-series models. Remodeling is not required.
**Standard Pipeline**: Gauge → Outline → Verify&Vault Normalization Ingestion

#### 2. External Black-box Projects without Predefined Paradigms
No engine entity models, no module boundaries and no dependency definitions. **Preemptive blind modeling is prohibited**. Modeling must be built upon scanning and reverse engineering insights.
**Engine Standard Onboarding Workflow**
**G Gauge | Survey**: Full scan of raw source code. Performs risk identification, debt ranking and coarse-grained asset partitioning to generate risk baseline datasets. No modeling or business code modification.

**O Outline | Profile (Core Modeling Phase)**: Reverse-parses module responsibilities, data flows, dependency graphs and implicit constraints. **Complete SurvX paradigm modeling is finished within this stage**:
- Generate credible Instance entities aligned with business boundaries
- Bind Cat tags for risk and classification
- Construct complete Ego profiles and metadata for modules
- Establish Env context and dependency relationships
- Attach read-only lock states to high-risk modules

**V Verify&Vault | Validation & Ingestion**: Execute minimally invasive paradigm repair, logic reorganization and naming normalization based on standardized engine entities. After validation, update entity baselines, remove isolation marks. **External assets are formally normalized as SurvX standard assets and integrated into the FORGE protection system.**

## 4. Module Core Capability Glossary (Engine Perspective)
- **Gauge**: Engine-layer risk detection capability that outputs raw risk datasets of legacy assets.
- **Outline**: Engine-layer asset digital modeling capability, delivering paradigm onboarding for external assets and profile calibration for native assets.
- **Verify&Vault**: Engine-layer asset normalization and closed-loop capability for legacy debt remediation, state transition and baseline refresh.

## 5. Global Engine Closed-loop Logic
1. **Incremental Side**: FORGE leverages Ego baseline rules + Energy sequential tracing + engine validation scripts to constrain all new code and prevent new technical debt.
2. **Legacy Side**: Native legacy assets directly enter the governance pipeline; external black-box assets gain cognition and modeling through G+O before paradigm normalization via V.
3. **Final Closed-loop**: All remediated assets become standard SurvX entities and join FORGE routine protection, enabling controllable and evolvable engineering assets at engine level.

## 6. Final Core Boundary Definition
- **FORGE**: SurvX engine incremental engineering discipline module, responsible for upstream constraint, rule enforcement and continuous prevention.
- **GOV**: SurvX engine legacy asset governance and paradigm onboarding module, responsible for legacy debt elimination, external asset modeling normalization and legacy closed-loop processing.
- **Overall Core Value**: Built upon SurvX native entity and time-series engine, it constructs an endogenous AI engineering governance closed-loop of **incremental prevention + legacy remediation**. All rules, states, workflows and assets are natively controllable within the engine.
