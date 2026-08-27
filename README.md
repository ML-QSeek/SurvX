# SurvX

> 📖 Read this in [简体中文](./README_zh.md)

> This repository contains the reference architecture and prototype code implementation for the SurvX paradigm.
## Current Status: Concept-verification prototype, not an out-of-the-box framework, not production-ready.
See [docs/design.md](docs/design.md) for detailed design.

SurvX is a paradigm for building intelligent systems, adaptable to various AI backends and usable independently of AI. This project aims for long-term exploration of future development forms and the organization of intelligent systems, with no predefined development schedule.

One of its frontier exploration directions is XGI — Xenogenic General Intelligence: an intelligence that presupposes no origin or form, capable of achieving long-term persistence through self-evolution.

(The XGI concept is close to AGI; currently AGI typically tends to refer to human-like intelligence, hence Xenogenic is used to make a conceptual distinction.)

---

## Core Idea
> Note: This section opens with functional programming ideas as the preferred lens for understanding this paradigm; the paradigm itself does not mandate an implementation approach.

This paradigm uses functional programming ideas as its lens for understanding.

Conceptually, everything is data, and everything persists and is managed as data. Under this premise, to facilitate structural design, the paradigm defines one basic unit and two primary roles.

The basic unit is **F**: a functional block with no complex internal structure, carrying only a single characteristic. Formally a blank container, it can hold programs, algorithms, models, specific parameters, or encapsulate external programs and third-party applications as capability units. Within this paradigm, programs, algorithms, models, and encapsulated external components etc. sit at the same level, are treated equally, and are organized and operated by the same set of rules.

The two primary roles are **Matter** and **Energy**.

- **Matter**: an entity possessing multiple characteristics, with relatively complex internal structure and collaboration mechanisms; may contain F, and may also contain other Matter.
- **Energy**: represents changes in data, used to drive the operation of Matter; manifests as sequential data, parameters, etc. outside of Matter, represented in data form.

Under this paradigm, the initiation of any behavior is necessarily triggered by a data change, forming a chain reaction.

---

## Matter

Three perspectives of Matter:

| Perspective | Concept | Essence |
|---|---|---|
| From the outside | Entity | An entity; based on its characteristics, one obtains y=f(x) |
| From the inside | Field | A field with state, internal mechanisms, scope of action, behavior and constraints |
| When it self-refers | Ego | Possesses the ability for self-iteration and self-evolution |

The outside world treats Matter uniformly as Entity; this Entity possesses specific mechanisms that transform input into corresponding output.

If one explores its internal structure, it is a Field with complete structure and operational mechanisms; endowing a Field with self-evolution capability transforms it into an Ego.

The actual action of transforming into an Ego is to add a self-driving mechanism to the Field, and this mechanism itself is also Matter.

Logically, Ego is the superimposed combination of two Matters.

**Naming convention (example)**

Entity and Field use the same name, e.g.: Cat.

When transformed into Ego, the identifier of the self-driving mechanism adds "()" before the name, i.e.: ()Cat.

At this point `Cat = Cat + ()Cat`.

---

## Field Five-Layer Structure and Ego Seven-Layer Structure

### Field: S-C-R-O-F

| Layer | Abbrev. | Name | Meaning |
|---|---|---|---|
| S | S | Structure | The constituent modules and components of Matter |
| C | C | Capability | The operational modes of internal modules, composable collaboration functions |
| R | R | Relation | Associations with external entities, collaboration, and usage relationships |
| O | O | Ordinance | Thresholds, behavioral rules, and various constraint limits corresponding to all mechanisms and characteristics |
| F | F | Feature | The overall characteristics of the entity; may register functions and relation chains, or declare non-functional characteristics such as performance and timeliness |

### Ego: S-C-R-O-F-G-L

| Layer | Abbrev. | Name | Meaning |
|---|---|---|---|
| G | G | Goal | Self-directedness, carrying multiple goals, used for self-driving and self-optimization |
| L | L | Symbol | Self-representation, used by []Cat to record its own cognition; cognition is allowed to deviate from objective existence |

**Field lives within the table; Ego attempts to rewrite the table.**

The five layers of Field need not all be complete. Unlike the basic unit F, Field is a multi-characteristic entity and necessarily possesses a clear Structure.

For Ego: Goal (G) is a required component; Symbol (L) is an optional component.

> Supplement (architectural detail): Within Ego, the self-driving mechanism []Cat has a special use for its Relation layer — it stores self-cognition.

---

## Energy

**Energy**: a sequence of data changes, representing the reality of change; static data is the sedimented form of Energy.

Data includes numbers, text, and other forms; at the architectural level it is divided into three categories — parameters, constraints, and experiences — each corresponding to different engineering semantics:

- **Parameters**: descriptive data, including weight coefficients etc., belonging to cross-sectional snapshot values.
- **Constraints**: various operational thresholds and boundary conditions, belonging to cross-sectional snapshot values.
- **Experiences**: the evolution records of an entity, belonging to time-series values, e.g. operation logs, financial historical market data, etc.

> Note: The system's operational chain needs an initiation source; the engine itself is a fixed F that produces the initial Energy change; external input and sedimented data can also become disturbance triggers.

> This paradigm inverts the data flow model of traditional programs: rather than programs actively seeking data as raw material for computation, data changes (Energy) drive Field execution — a model better suited to the operational characteristics of AI and algorithmic models.

Energy₁ --drives--> Field₁ --changes--> Energy₂ --drives--> Field₂ --changes--> Energy₃ --drives--> ...

---

## Engine

The engine itself is a basic unit F, divided into two major types:

| Engine Type | Drives | Characteristics |
|---|---|---|
| Field Engine | Fixed application | Specific goal, deterministic application |
| Ego Engine | True Ego | Multi-goal, self-evolving |

The Field Engine starts from the Feature (F) layer, activates Relation and Capability, organizes external resources (Energy, external Matter) and internal modules (internal Structure), and completes operation under the constraints of Ordinance (O).

The Ego Engine starts from the G (Goal) layer, combining algorithmic models and external feedback to dynamically organize and adjust the entity's internal structure.

**The engine is the steward that maintains order, not the brain that issues commands. Lifecycle is still managed by the constraint layer (O); the engine only executes.**

---

## Language Form

This paradigm can theoretically be implemented as a low-level programming language; at this stage it is positioned as an API-style description layer built on top of other host languages.

- **F**: can be implemented in any programming language, with no mandatory binding to the host language.
- **Matter and Ego**: use descriptive syntax, supporting relational expressions, capability pseudocode, and complete input-output contract definitions.

The input-output contract encompasses six dimensions:

- **Data Type (structural state)**: defines the shell structure of output data.
- **Value Range (value state)**: defines the magnitude and boundary conditions of data values.
- **Status Identifier (logical state)**: labels the business result tag after execution completes.
- **Time and Frequency (temporal state)**: specifies the rhythm at which input and output occur.
- **Environment Interaction (environmental state)**: records the source and flow of data, tracking the entity's interaction trajectory with the external environment.
- **Metadata (descriptive state)**: describes additional information about the data itself.

The input-output contract serves a dual purpose: it is both the basis for the system to identify an Entity's functional capabilities, and the core reference for AI-generated work under Ego's goal-driven mode. AI completes code or model adjustments for capability units based on the contract, produces an initial implementation version, and then the constraint layer (O) completes validation and iterative correction.

> Engineering implementation note: Energy commonly takes two storage forms in prototypes, which does not represent a paradigm-mandated storage scheme:
> - Cross-sectional snapshot data (parameters, constraints): stored as Key-Values pairs;
> - Time-series evolution records (experiences): stored as time-series tables.

---

## External Component Integration

External programs, third-party frameworks, and external applications can be integrated into the SurvX system.

The simplest integration method is to encapsulate them as **F**, participating directly in system collaboration as independent capability units.

As business and evolution needs grow, one can progressively supplement state, constraints, relations, goals, and other structures on this basis, evolving from F into a complete Matter (Entity), thereby gaining the full capabilities of a complete entity and participating in the system's data-flow driving, self-evolution, and constraint management.

---

## AI in SurvX

Matter is essentially also data, merely special data carrying structured blueprint semantics.

Under this system, AI no longer directly generates executable scripts, but is responsible for generating and modifying Matter blueprints; the entire system is driven to run by the Energy data flow.

The Goal layer (G) provides the direction of evolution, and the constraint layer (O) delineates behavioral boundaries, confining generative AI to the role of structural creation, not allowing it to directly control execution logic.

---

## Evolutionary and Complementary Workflows

Under this system, whether for application development or Ego's self-evolution, there are primarily two basic workflows, and in practice the two are usually used in combination.

- **Evolutionary**: based on the existing entity state from the previous step, iteratively generate the next state within the feasible region delineated by constraints; multiple rounds of deduction accumulate to form an overall candidate feasible space; then, through global constraints and result evaluation, the final solution is selected.
- **Complementary**: based on goals and current status, first clarify the input-output contract, then have AI or human design fill in the intermediate structure and capability units, building a complete pathway from input to output.

Goal decomposition combined with step-by-step evolution is a common combination pattern, and the overall operational logic of this paradigm is also built on the synergy of the two workflows.

---

## Engineering Structure

```
├── core/
│   ├── engine/   # Execution engine
│   ├── studio/   # Management tools
│   └── forge/    # Human intervention paradigm
├── matter/       # Matter library
├── energy/       # Data sediment
├── extensions/   # External dependencies
├── docs/         # Design documents
├── applications/ # Complete applications
├── tools/        # Tool development
├── examples/     # Examples
└── tests/        # Tests
```

> Applications developed under this architecture follow their own engineering structure and are not forced to align with the repository root directory.

---

## Some Extended Reflections

Returning to the practical problems of current AI-assisted programming. Current AI-assisted programming has several structural problems: directly generating executable processes, high unit coupling, strong dependence on model version changes, and a lack of audit handles during the runtime and generation phases.

SurvX's approach: let the model generate composable structural units rather than one-off execution processes. **The model is a variable; the intermediate-layer blueprint is a constant.**

This is not the entirety of SurvX's goals, merely a natural extension of the paradigm under the current technological environment.

---

## License

- Root directory and most subdirectories: **MIT**, see [LICENSE](LICENSE) for details
- `/applications`: **AGPL-3.0**, see [applications/LICENSE](applications/LICENSE) for details
