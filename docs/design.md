# SurvX Technical Design Document

**Document Positioning**: Engineering implementation document supporting the README paradigm architecture. Focuses on source code rules, engineering structure, implementation details and operating mechanisms. It does not repeat top-level paradigm concepts and supplements only implementable technical details.

**Adaptation Stage**: Concept verification prototype (not production-ready)

**Core Description**: The top-level architecture paradigm is independent of tech stack, storage and engine binding. This document serves as the official technical design specification for the paradigm reference prototype implementation.

# Part 1: Concepts & Conventions
## 1.1 Core Concepts
The SurvX paradigm defines **one basic capability unit + two core entity roles**. All system capabilities, operating logic and evolutionary mechanisms are built on this system, enabling standardized unified governance for businesses, algorithms, models and external components.

### 1.1.1 Basic Capability Unit: Q
Q is the minimum functional unit of the system with no complex internal structure. It serves as a blank functional container carrying **single feature and single capability**, acting as the unified abstract standard for all system capabilities.

Q is highly versatile. It can host native programs, business algorithms, AI models and fixed parameter configurations, as well as encapsulate external programs, third-party frameworks and external applications. In the SurvX paradigm, native code, algorithm models and external components stay at the same level and follow unified architectural rules for organization, scheduling and execution.

**Q Classification**:
- **Lightweight Q**: Simple mathematical expressions and conditional judgments
- **Composite Q**: Aggregates and filters multiple sets of data to assemble Matter layered logical views
- **Neural Network Q**: Takes values of a group of entity IDs as input and outputs vector or scalar results

Q supports version binding. New versions of Q will not automatically replace existing references and require explicit manual upgrade to ensure instance stability.

### 1.1.2 Core Entity Roles: Matter & Energy
All system operating behaviors, state changes and iterative evolutions are completed through the collaboration of Matter entities and Energy data changes. There are no independent bare business logics or static fixed execution flows.

- **Matter (Entity Carrier)**: A complex entity with multi-dimensional features, structured internal architecture and autonomous collaboration mechanisms. It can nest Q capability units and sub-level Matter entities, serving as the carrier for all system states, capabilities and constraints.
- **Energy (Driving Source)**: Represents the reality of system data changes and is the exclusive trigger source for all behaviors. It exists in the form of time-series data, parameter snapshots and state change sequences. Static data is the deposited form of Energy.

**Core Rule**: Any system behavior must be triggered by an Energy data change, triggering a global chain reaction.

### 1.1.3 Three Core Perspectives of Matter
A single Matter entity can be defined from external, internal and self-referential dimensions, corresponding to different engineering capabilities and operating forms:

| Perspective | Concept | Core Essence |
| ---- | ---- | ---- |
| External Perspective | Entity | Exhibits standardized input-output entities following the y=f(x) mapping rule. External systems invoke capabilities only through contracts without perceiving internal structures |
| Internal Perspective | Field | A structured field with independent states, internal functions, scopes and behavioral constraints, possessing complete internal collaboration and operating mechanisms |
| Self-referential Perspective | Ego (Self-evolving Entity) | Built on Field with additional self-driving, self-iterating and self-optimizing capabilities, enabling autonomous adjustment of internal structures and operating logic based on goals |

Core Logic: Ego is not an independent new entity, but a composite of **Field + self-driving mechanism (affiliated Matter)**. The self-driving mechanism itself complies with Matter architectural specifications.

### 1.1.4 Five-layer Basic Structure of Field (S-C-R-O-F)
Field is the fundamental structured entity and an essential form of Matter. The five layers do not all need to be complete, but must retain the core Structure layer, distinguishing it from unstructured basic Q units.

| Layer | Abbreviation | English Name | Core Meaning |
| ---- | ---- | ---- | ---- |
| Structure Layer | S | Structure | Defines Matter's constituent modules, basic components and nesting relationships, serving as the fundamental carrier of entity existence |
| Capability Layer | C | Capability | Defines the operating modes, combination rules and reusable collaboration functions of internal modules, supporting the output of core entity capabilities |
| Relation Layer | R | Relation | Defines associations, collaborations, dependencies and invocation relationships between the current entity and external Matter, external components and Q units |
| Ordinance Layer | O | Ordinance | Defines all operating thresholds, behavioral boundaries, execution rules, permission constraints and exception interception mechanisms of entities, serving as the core guarantee of system order |
| Feature Layer | F | Feature | Defines the overall core features of entities, including registrable functions, link associations, performance indicators, aging rules and other non-functional features |

### 1.1.5 Seven-layer Evolution Structure of Ego (S-C-R-O-F-G-L)
Ego is extended from the five-layer Field structure with two additional layers: **Goal layer and Symbol layer**, enabling autonomous evolution capabilities. The Goal (G) layer is mandatory, while the Symbol (L) layer is optional.

| Layer | Abbreviation | English Name | Core Meaning |
| ---- | ---- | ---- | ---- |
| Goal Layer | G | Goal | Bears multi-dimensional autonomous goals, providing core directions for entity self-driving, iterative optimization and structural adjustment, acting as the core power source of Ego evolution |
| Symbol Layer | L | Symbol | Records entity self-cognition, allowing deviations between cognition and objective reality to support self-review and iterative correction |

Architectural Supplement: The Relation layer of the Ego self-driving mechanism has a dedicated purpose, specifically storing entity self-cognition data to support the closed-loop self-evolution logic.

The seven-layer/five-layer structure of Matter is a **logical view** rather than physical tables. The engine aggregates and assembles layered views based on three underlying basic data tables, while the underlying storage is unaware of layered concepts.

### 1.1.6 Data Engineering Semantic Classification
At the architectural level, all data is divided into three categories, corresponding to different storage forms and operating logics:
- **Parameter Data**: Descriptive cross-sectional snapshot data, including weight coefficients, basic configurations and other static parameters without time-series attributes.
- **Constraint Data**: Cross-sectional snapshot data such as operating thresholds, boundary conditions and execution rules, used for global behavior management and control.
- **Experience Data**: Time-series data of entity evolution and operation execution, including running logs, iteration records, interaction trajectories, historical market data and other sequential information.

### 1.1.7 Trigger Source Rules
The initial system driving source is the **engine built-in basic Q unit**, which generates initial Energy disturbances. Meanwhile, external input data, historical deposited data changes and manual interventions can all serve as trigger sources to activate the system operating link.

## 1.2 Terms & Conventions
### 1.2.1 hoc / dbfs Conventions
- **hoc**: Temporary scripting state
- **dbfs**: Official persistent state

All subsequent occurrences of `hoc` and `dbfs` follow this convention without further elaboration.

### 1.2.2 hoc (Temporary Scripting State)
Developed based on independent Python files. All Matter entities and Energy structures are described and declared via Python dictionaries with no database dependencies, supporting rapid iteration, prototype verification and small-scale instance debugging.
- Matter: A top-level dictionary where all sub-Matters are explicitly defined via long keys and values within this dictionary.
- Energy: A standalone dictionary.

### 1.2.3 dbfs (Official Persistent State)
Adopts a multi-media separated storage architecture to decouple structure, functions and data:
- Matter structural definitions: Persisted to SQLite
- Q functional logic: Stored in an independent file system, mapped to database metadata
- Energy time-series data and parameter/threshold snapshots: Stored in DuckDB to support time-series query, state playback and evolution tracing

In dbfs, Matter exists as a standalone structured table stored by fields.

# Part 2: Storage & Operating Rules
## 2.1 Repository Engineering Structure
The repository source code structure is **not equivalent** to the user business application structure. Business applications built on this framework follow an independent lightweight directory specification.

```
Project Root/
├── survx/               # Engine Ontology
│   └── survx_engine/    # Core Engine Module
├── models/              # Development Directory
│   └── survx/           # In-development Engine (source files)
├── works/               # Factory Layer for Iteration & Gray Verification
│   ├── solutions/survx/ # Trial-running Engine (source files)
│   ├── tools/
│   └── examples/
├── instances/           # Runnable Instances
│   └── survx_studio/    # Developer Tool Instance
└── docs/                # Design Documents
```

**Description**
- `models`: Development directory organized by sub-projects, without separate `tools`/`examples` classification
- `works`: Factory layer categorized into `solutions`/`tools`/`examples`
- `instances`: Runnable instances deployed by project, without separate `tools`/`examples` classification
- `models/survx` and `works/survx` represent the development version and trial-running version of the engine. Empty placeholder files are used internally to prevent infinite nesting
- `instances` does not contain the `survx` directory; runtime instances reference the root `survx` module
- Release pipeline: `models → works → instances`; Engine iteration path: `models/survx → works/survx → root survx`

## 2.2 Data Model & Storage
The paradigm is not bound to any storage medium. For unified prototype implementation standards, this prototype adopts **SQLite + DuckDB dual-storage architecture** with separated structure, function and data storage.

### 2.2.1 Storage Media
**SQLite**
- `<app_name>.db`: Matter structure table, storing only ontology structure data
- `_forge.db`: Independent SQLite file storing quality control table `_forge` for transactional operation records, clearly separated from ontology structure

**DuckDB**
- `_<app_name>.duckdb`: Stores all Energy-related tables, including parameters, constraints, relationships, time-series data, experience records, registries and upper-layer observation data

**File System**
- `q/`: Directory for Q functional logic, storing independent `.py` files mapped to database metadata

**Runtime Memory**
- `_state`: Tick window state table maintained by the engine, not persisted to disk

### 2.2.2 Data Classification
**Cross-sectional Snapshot Data**
- Parameter and constraint data
- Stored in DuckDB with multi-version coexistence via the `version` field; the maximum version is adopted as the current valid state

**Time-series Evolution Data**
- Sequence and experience data
- Appended incrementally by `_tick` in DuckDB for trend analysis and historical backtracking

**Structural Data**
- Matter structure data
- Stored in SQLite with flat key paths; new versions are appended instead of in-place overwriting

### 2.2.3 Table List
**<app_name>.db (SQLite)**
- `<app_name>`: Matter structure table

**_forge.db (SQLite)**
- `_forge`: Operation record table for quality control

**_<app_name>.duckdb (DuckDB)**
- `_parameter`: Parameter Table
- `_constraint`: Constraint Table
- `_relation`: Relation Table
- `_sequence`: Sequence Table
- `_experience`: Experience Table
- `_intent`: Intent Table
- `_feedback`: Feedback Table
- `_language`: Language Table
- `_train`: Training Data Table
- `_report`: Report Summary Table
- `_llm`: AI Collaboration Table
- `_register`: Instance-level Registry Table

### 2.2.4 Underlying Storage Model
The prototype adopts a flat dual-dictionary model: `data_store` (main data dictionary) + `tag_index` (tag index dictionary). No deep nesting exists; all nodes are flattened at the top level with hierarchical relationships expressed via string keys.

Persistent data is stored via SQLite/DuckDB tables and loaded into the runtime flat KV model (`data_store` + `tag_index`), with changes synchronized back to the persistent layer.
- **Node ID**: Auto-increment numeric IDs for child nodes, permanently retained after allocation; new nodes are appended to avoid cascading modifications
- **Node Lifecycle**: Nodes are not physically deleted at the business layer. The `active` boolean flag controls activation status. Nodes with `active=True` participate in tick computation; `active=False` nodes are dormant with reserved data. Parent node dormancy does not cascade to child nodes
- **Query Mode**: Only active valid nodes are returned by default; `include_inactive=True` enables reading dormant nodes for historical backtracking
- **Version Mechanism**: Parameters, constraints and relationships carry auto-increment `version` numbers. Updates generate new versions with old versions permanently retained; queries adopt the maximum valid version by default

### 2.2.5 Table Structure
Field definitions are subject to `syntax_zh.md` and will not be repeated here.

### 2.2.6 Replaceability
In production environments, the storage layer can be replaced with MySQL, PostgreSQL, time-series databases and other mainstream databases according to business requirements. The paradigm architecture is fully compatible with zero core logic modifications.

## 2.3 Core Engine Mechanism
The engine itself is a standardized basic Q unit with no independent decision-making capability. Its core responsibilities are **execution scheduling and order maintenance**, without control over system core logic and lifecycle. The full system lifecycle is governed by the Ordinance (O) layer, with the engine serving only as the execution carrier.

### 2.3.1 Dual Engine System
| Engine Type | Driving Object | Core Features | Startup & Operating Logic |
| ---- | ---- | ---- | ---- |
| Field Engine | Fixed Field entities & deterministic applications | Single-goal, deterministic execution, no autonomous evolution | Starts from the Feature (F) layer, activates the relation and capability layers, schedules internal and external resources, and completes fixed process execution under constraint layer rules |
| Ego Engine | Ego self-evolving entities | Multi-goal, dynamic adaptation, autonomous iterative optimization | Starts from the Goal (G) layer, dynamically adjusts internal entity structures and collaboration logic combined with algorithm models and external feedback |

**Core Positioning Summary**: The engine acts as the system's "execution manager" responsible for operational order, rather than the decision-making core. All executions must comply with constraint boundaries and goal directions.

### 2.3.2 Built-in Engine Capabilities
1. Global `Table Name + ID` cross-table parser
2. Tick window switching, state archiving and transaction consistency guarantee
3. Q component scheduling and evaluation, recursive depth interception to prevent infinite Q recursion
4. Dual-dictionary CRUD and version synchronization; all read/write operations are encapsulated in engine interfaces (upper-layer direct manipulation is prohibited); node positioning via key prefix matching to avoid recursive traversal

## 2.4 External Component Access Specification
All external programs, third-party frameworks and external applications can be seamlessly integrated into the SurvX system, supporting an evolutionary adaptation path from **lightweight access to full-capability evolution**.

**Lightweight Access (Basic)**
Encapsulate external components into standardized Q capability units without modifying original logic, enabling participation in system data flow collaboration and capability scheduling.

**Full Evolution (Advanced)**
Incrementally supplement structure, capability, relation, constraint and goal layers based on Q units to evolve into complete Matter entities, acquiring full capabilities including state management, constraint governance, data-driven execution and autonomous evolution.

## 2.5 Validation Rules
### 2.5.1 Engine-level Mandatory Validation Rules
The following rules are enforced at the engine layer. All entities, parameters and Q components must pass validation before warehousing.

**1. No Isolated Nodes**
Newly added entities, parameters and Q components must bind valid scopes, associations and constraints. Validation failure rejects warehousing.

**2. Define Before Reference**
All entity and parameter IDs must be pre-registered before being referenced.

**3. No Bare Strings in Logical Layers**
Logical layers prohibit bare strings for entity positioning (except the Symbol L layer). All operational references must adopt registered IDs.

**4. Allow Bidirectional Q Closed Loops, Forbid Infinite Recursion**
Bidirectional causal Q closed loops are permitted; infinite Q recursion is automatically intercepted by the engine.

### 2.5.2 Development Specifications & Architectural Constraints
Mandatory core development rules to unify iteration standards, prevent architectural deviation and ensure paradigm self-consistency. All source code development, function iteration and component access must comply strictly.

**Hard Constraints**
1. All capabilities must be abstracted as Q units
All system capabilities must be standardized Q units. Bare independent business processes and fragmented logic are prohibited.

2. All states must belong to Matter entities
All runtime and configuration states must be managed by Matter entities. Floating global variables and unowned states are prohibited.

3. All behaviors must be driven by Energy data changes
All business behaviors and entity actions must be triggered by Energy data changes. Active polling and proactive triggering logic are prohibited.

4. AI only operates on Matter structural blueprints
AI is only permitted to generate and modify Matter structural blueprints. Tampering with execution flows, bypassing constraint layers and acquiring system scheduling permissions are prohibited.

5. Ego evolution must be goal-driven
Ego self-evolution logic must be driven by the Goal layer. Hard-coded fixed evolution rules and directional iteration logic are prohibited.

**Implementation Conventions**
- **Component Reuse Strategy**: Read-only reference; modification triggers deep copy to generate independent replicas
- **Blueprint Compilation Mapping**: Final compiled blueprints map to `_parameter / _constraint / _relation`
- **Simple Script Mode Boundary**: Simple scripts can read formal instances; write-back only supports partial merging without complete persistent system maintenance
- **Data Writing Mode**: Single-item appending instead of bulk dictionary writing; supports incremental dynamic updates

# Part 3: Developer Tools
## 3.1 Command Line Quick Reference
| Tool | Command | Function |
| ---- | ---- | ---- |
| register | `python register.py reg <cmd_name> [dir] <script_name>` | Register command-to-script mapping for stable entry and version switching |
| register | `python register.py run <cmd_name> <args...>` | Execute scripts via registered commands |
| createPlugin | `python CreatePlugin.py [dir] <entity_name>` | Generate hoc plugin script skeleton |
| publish | `python publish.py reg <cmd_name> <src_dir> <dst_dir>` | Register source-to-target release mapping |
| publish | `python publish.py <cmd_name> <script_subpath>` | Release single script via registered mapping |
| CreateApp | `python CreateApp.py [dir] <app_name>` | Generate full dbfs application instance skeleton |

## 3.2 register
Command: `python register.py reg <cmd_name> [dir] <script_name>`

Examples:
- Latest floating version: `python register.py reg cplugin CreatePlugin`
- Specified directory: `python register.py reg cplugin src CreatePlugin`
- Fixed version lock: `python register.py reg cplugin CreatePlugin_20260921101000`
- Execution: `python register.py run <cmd_name> <args...>`
- Execution example: `python register.py run cplugin src FinDataFetcher`

**Function**: Maps command names to scripts or specified script versions, providing a unified forwarding execution entry without modifying the system environment.

**Input**: Command name, optional directory, script name

**Output**: Writes mapping records to SQLite mapping table `_register` and supports execution forwarding via registered commands

**Storage**: `.registry.db`, table `_register`, fields: `key / value / version`

**Rules**:
- Script name is mandatory during registration; version is optional
- No version specified: loads the latest script version in the registered directory during execution
- Version specified: strictly uses the fixed version; throws an error if missing
- Search scope is limited to the registered directory, no cross-directory expansion
- Re-registering the same command name overwrites existing records without appending history

**Status**: Under discussion

**Remark**: Implements the SurvX registry mechanism with stable command entries and flexible version switching capabilities.

## 3.3 createPlugin
Command: `python CreatePlugin.py [dir] <entity_name>`

Examples:
- Current directory: `python CreatePlugin.py FinDataFetcher`
- Specified directory: `python CreatePlugin.py src FinDataFetcher`

**Function**: Generates standardized hoc plugin script skeletons based on specified directories and entity names, generating only structural frameworks without business logic.

**Input**: Optional directory, entity name

**Output**: Generates file `<dir>/<entity_name>_<version>.py`

**Storage**: File system, hoc temporary scripting state, no database dependencies

**Generated Content**:
- Header docstring: Chinese & English description, version, author, timestamp and usage
- Part 1: Matter structural blueprint with S / F / Ego / Env comments
- Part 2: Initial Energy values with seven core tables and Ego-specific comments
- Part 3: Placeholder Q function
- Part 4: In-memory table & registry configuration
- Part 5: Startup entry block

**Rules**:
- File name carries Beijing timestamp version: `YYYYMMDDHHMMSS`
- Auto-creates target directory if missing
- Dynamically replaces all template placeholders with the specified entity name
- Q name auto-generated in format `q + random number` (no duplicate checking temporarily)
- Default author: `quruyi`

**Status**: Under discussion

**Remark**: Implements rapid hoc instance skeleton initialization; hoc scripts can be migrated to formal engine Q components after stabilization in dbfs state.

## 3.4 plugin
Command: `python <entity_name>_<version>.py`

Example: `python FinDataFetcher_20260921111003.py`

**Function**: Carries the structural blueprint, initial Energy values, Q functions and startup logic of a single hoc instance.

**Input**: None (the script itself is the instance carrier)

**Output**: Determined by the main Q function pointed to by `f_main` (placeholder with no actual output by default)

**Storage**: Single Python file, hoc temporary scripting state

**Structure**:
- Part 1: Matter structural blueprint with flat key paths, optional S/C/R/O/F layers
- Part 2: Initial Energy values covering `_parameter / _constraint / _relation / _sequence / _experience / _report / _llm`
- Part 3: Q functions with prompt/reason recorded in comments
- Part 4: In-memory state and registry tables (`_state`, `_register`) stored independently, excluded from instance dictionaries
- Part 5: Startup block, dynamically loads and invokes the main Q function via `<entity_name>_f_main`

**Rules**:
- Top-level dictionary name matches the entity name with flat path keys
- Empty structure declaration is prohibited; layers are declared only when required
- Declared S/C/R/O/F layers must contain valid content (no empty layers)
- `f_main` strictly points to the main entry Q function
- Startup block is placed at the file end to ensure full predefinition of all components
- Incremental file growth is normal for hoc scripts; stable scripts will be migrated to dbfs state

**Status**: Under discussion

**Remark**: Standard hoc instance ontology specification; after migrating to dbfs, structures are stored in SQLite, Q logics in independent file systems, and Energy data in DuckDB.

## 3.5 publish
Command: `python publish.py reg <cmd_name> <src_dir> <dst_dir>`

Examples:
- Register publish rule: `python publish.py reg pubw models works`
- Register publish rule: `python publish.py reg pubi works instances`
- Execute publish: `python publish.py pubw tools/xx/yy.py`

**Function**: Maps command names to source-target directory pairs, supporting single-file script release via pure file copying without logic modification.

**Input**: Command name, source directory, target directory for registration; command name and script subpath for release execution

**Output**: Writes mapping records to SQLite table `_publish` and supports single-script release

**Storage**: `.registry.db`, table `_publish`, fields: `key / source / target`

**Rules**:
- Command name, source directory and target directory are mandatory for registration
- Release execution only requires command name and script subpath, with paths automatically spliced
- One target directory maps to exactly one source directory
- Re-registering an existing target directory triggers overwrite confirmation
- Only single-file release is supported (no directory synchronization)
- Aborts and throws errors for non-existent source paths, directory paths and database files
- Directly overwrites existing target files with the same name
- Supports only forward release (no reverse backflow)

**Status**: Under discussion

**Remark**: Implements the SurvX staged release mechanism for controlled single-script deployment; compliance checks can be extended in official versions.

## 3.6 CreateApp
Command: `python CreateApp.py [dir] <app_name>`

Examples:
- Current directory: `python CreateApp.py myapp`
- Specified directory: `python CreateApp.py src myapp`

**Function**: Generates complete standard dbfs application instance skeletons, including SQLite structure library, DuckDB energy library, Q functional directory and startup launcher.

**Input**: Optional directory, application name

**Output**: Generates complete skeleton directory `<dir>/<app_name>/`

**Storage Allocation**:
- `<app_name>.db`: SQLite database storing core Matter structure with table name consistent with the application name
- `_forge.db`: Independent SQLite database storing quality control table `_forge`
- `_<app_name>.duckdb`: DuckDB database storing all Energy-related tables
- `q/`: Independent directory for Q functional scripts
- `<app_name>.py`: Application startup launcher

**Generated Artifact Structure**:
```
<dir>/<app_name>/
├── <app_name>.db          # SQLite: Matter structure table
├── _forge.db           # SQLite: Quality control table _forge
├── _<app_name>.duckdb     # DuckDB: Full Energy data tables
├── <app_name>.py          # Application launcher
└── q/
    └── qxxxxxx.py      # Main entry Q component
```

**Rules**:
- Application name serves as the directory name; the root application directory is created first
- `<app_name>.db` stores only ontology Matter structure with a pre-inserted `<app_name>_f_main` entry pointing to the core Q component
- `_forge.db` is independently stored for quality control management
- `_<app_name>.duckdb` contains all standard Energy tables: `_parameter`, `_constraint`, `_relation`, `_sequence`, `_experience`, `_intent`, `_feedback`, `_language`, `_train`, `_report`, `_llm`, `_register`
- `_register` table supports real-time updates without version locking
- Q components adopt random naming format `q + number` (no duplicate checking temporarily)
- Q file version and timestamp adopt Beijing time at generation
- Default Q function logic: print hello world and return
- Launcher dynamically imports and invokes the core Q component via the Matter table entry
- Entry file name strictly matches the application name

**Status**: Under discussion

**Remark**: Standard dbfs instance initialization specification; extensible with compliance checks, version management and table sharding mechanisms in subsequent iterations.
