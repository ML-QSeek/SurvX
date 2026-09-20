# SurvX Engine Core Context: Instance Meta-Model Definition
## Document Purpose
This is built-in foundational context for the SurvX engine, intended for **human developers and AI agents**.
It defines the underlying instance structure, four core components, layer semantics and strict boundary rules. This is the base meta-model for all reasoning, execution and evolution.
Do not modify primitive definitions unless the paradigm itself is revised.

## Core Design Principles (AI-first comprehension rules)
1. **Separate rule definition from runtime state**: Matter encapsulates structure, capability, constraints and relationships; Energy holds runtime state, snapshots and temporal changes.
2. **Dual relationship isolation**: External interaction relationships (for communication and invocation) are fully separated from internal cognitive relationships (for reasoning).
3. **Compositional instance architecture**: A fully operational Instance consists of four orthogonal parts: problem entity, self-evolution agent, environment container and dedicated data stream.
4. **Isolated semantics for identical layer names**: S/C/R/O/F share the same naming tokens, but their meanings depend on which Matter type they belong to.

## 1. Instance Structural Formula
```
Instance = Cat + (Cat)<egoname> + [Cat]<envname> + {Cat}<energyname>
```

### Native Base Shorthand Convention
Base primitives are provided by default and may be abbreviated:
- `(Cat)base` → `()Cat`
- `[Cat]base` → `[]Cat`
- `{Cat}base` → `{}Cat`

## 2. Overview of Four Core Components (AI Quick Reference Table)
| Component Label | Entity Type | Layer Structure | Core Role | Core Capability |
|---|---|---|---|---|
| Cat | Field Matter | S-C-R-O-F 5 layers | **Problem Entity** | Business structure, executable capabilities, external interactions |
| (Cat) | Ego Matter | S-C-R-O-F-G-L 7 layers | **Reasoning & Evolution Agent** | Goal decomposition, cognitive reasoning, self-evolution, solution evaluation |
| [Cat] | Env Field Matter | S-C-R-O-F 5 layers | **Runtime Environment Container** | Resource provision, runtime context, environmental constraints and feedback |
| {Cat} | Energy Data Stream | No layered structure | **InstanceState Data** | Parameter snapshots, constraint snapshots, time-series history |

---

## 3. Detailed Component Definitions

### 1. Cat (Field Matter): Problem Entity
Uses **S-C-R-O-F five-layer structure**.
Represents the objective problem entity to be solved, operated and reasoned over.

- **S Structure**: Internal components, modules and constituent units; defines static entity topology.
- **C Capability**: Collaboration logic between internal components, executable actions and function set.
- **R External Relation**:
  Stores only **cross-entity connections, interaction interfaces and invocation relationships**.
  ❗ Does NOT store cognition, internal structural links or reasoning knowledge.
- **O Ordinance**: Execution thresholds, preconditions, validation rules and behavioural boundaries.
- **F Feature**: Multiple execution branches, scenario adaptation strategies, alternative plans under the same objective.

> Behaviour: Passive and invocable. It has capabilities and interfaces, **no autonomous reasoning**.

---

### 2. (Cat)<egoname> (Ego Matter): Self-Evolution Reasoning Entity
Uses **S-C-R-O-F-G-L seven-layer structure**.
Represents the reasoning, evaluation, decomposition and evolution subject of the Instance.

Extends the 5 Field layers with **G Goal layer and L Logic layer**.

- **S Structure**: Internal component composition of Ego’s reasoning mechanism.
- **C Capability**: Internal collaborative capabilities for reasoning, decomposition, evaluation and iteration.
- **R Cognitive Relation (Ego exclusive)**:
  Stores Ego’s private cognitive knowledge graph.
  Contents: recognized entities, concept associations, reasoning history, subproblem decomposition links and experience traces.
  ✅ This is Ego’s internal memory and reasoning knowledge base. It is not used for external communication; it serves internal thinking only.
- **O Ordinance**: Reasoning boundaries, evaluation criteria, hard logical limits that cannot be violated.
- **F Feature**: Reasoning bias, thinking style, optimization strategy traits.
- **G Goal**: Externally supplied objective; the sole starting point for all reasoning, iteration and decomposition.
- **L Logic**: Standardizes internal reasoning concepts and semantics into normalized symbols for cross-entity communication and output.

### ✅ Critical Distinction (AI Must Read, No Confusion Allowed)
1. **Field.R (Cat / Env) = External Interface Relation**
   Purpose: Entity invocation, data exchange, system collaboration.
2. **Ego.R = Internal Cognitive Knowledge Graph**
   Purpose: Self reasoning, problem decomposition, solution assessment, memory-based inference.

---

### 3. [Cat]<envname> (Env Field Matter): Environment Entity
Uses **S-C-R-O-F five-layer structure**.
Represents the runtime field and resource environment of the Instance, supporting multiple resident agents.

- **S Structure**: Environment resources, compute units, data assets and composition.
- **C Capability**: Resource supply, data services and runtime support provided by the environment.
- **R External Relation**: Interaction links and feedback channels between the environment, internal entities and external systems.
- **O Ordinance**: Resource caps, environmental rules and global boundary conditions.
- **F Feature**: Inherent environmental traits, fluctuation patterns and scenario properties.

> Behaviour: Provides runtime context. **No autonomous cognition, does not participate in reasoning**.

---

### 4. {Cat}<energyname> (Instance-specific Energy Data Stream)
**Not a Matter type. No layered structure, no behavioural capabilities.**
Only carries all data changes and state deposits generated during instance execution.

Contains three fixed data categories:
1. **Parameter Snapshot**: Instant runtime parameters and configuration snapshots of all components.
2. **Constraint Snapshot**: Current active constraint thresholds and rule parameters.
3. **Time-series Experience**: Full event history, state transitions, reasoning traces and timeline records.

> Core function: Drives Matter execution, records evolution trajectory and supplies evidence for reasoning.

---

## 4. AI Mandatory Anti-Misconception Rules
1. **Do NOT conflate the two types of R**
   R on standard Field (Cat/Env) is communication interface; only Ego.R is cognitive knowledge graph.
2. **Do NOT treat Energy as an entity**
   Energy holds data only. It has no structure, no capabilities and cannot execute actions.
3. **Do NOT assume identical semantics for shared layer names**
   Ego’s S/C/O/F serve reasoning; Cat’s S/C/O/F serve business execution. Meanings differ.
4. **Do NOT allow Field to perform autonomous reasoning**
   All decomposition, evaluation, optimisation and iteration actions **must originate from Ego**.
5. **Do NOT assign self-awareness to the Environment**
   Env only supplies resources and environmental rules; it has no goals or cognition.

## 5. Concise Runtime Summary (AI Global Workflow Understanding)
- **Cat**: Performs work, executes actions and provides business capabilities.
- **Ego**: Thinks, decomposes, evaluates, iterates and evolves.
- **Env**: Provides runtime environment and resource constraints.
- **Energy**: Tracks state changes, drives execution and preserves history.
