# SurvX Syntax Specification (syntax_en.md)
> This document consists of two parts:
> Part I: Syntax Rules Description (what constitutes valid syntax)
> Part II: Block-wise Definition (detailed structure of each block)
> Storage rules, runtime rules and validation rules are documented in design.md.

---

# Part I: Syntax Rules Description
## 1.1 Overall Structural Formula
```
Instance = Cat + (Cat)<egoname> + [Cat]<envname> + {Cat}<energyname>
```
**Supplementary Notes**
- `+` does not represent string concatenation; it denotes component composition relationships.
- Collection notation `[Cat1,Cat2,Cat3]<envname>` indicates multiple entities belonging to the same Env environment. Each entity uses an independent path Key in the Matter table.

## 1.2 Top-level Marker Specification
`()` / `[]` / `{}` are fixed semantic markers for blueprints. They serve as dictionary string Keys instead of program variables, and can be legally stored in dictionary and database text fields.
- `(Cat)`: Ego subject entity marker
- `[Cat]`: Env environment entity marker
- `{Cat}`: Energy parameter entity marker

## 1.3 Native Shorthand Specification (System Default Base)
- `(Cat)base` shorthand: `()Cat`
- `[Cat]base` shorthand: `[]Cat`
- `{Cat}base` shorthand: `{}Cat`

In simulation projects, `[Cat]` and `{Cat}` support multi-entity collection notation `[Cat1,Cat2,Cat3]<envname>`, `{Cat1,Cat2,Cat3}<energyname>`, i.e.:
```
Instance = Cat1 + (Cat1)<egoname> + Cat2 + (Cat2)<egoname> + Cat3 + (Cat3)<egoname> + [Cat1,Cat2,Cat3]<envname> + {Cat1,Cat2,Cat3}<energyname>
```

## 1.4 Two Major Categories
The top layer is divided into two categories: **Matter** and **Energy**.

**Matter**
- Cat, (Cat)<egoname>, [Cat]<envname> all belong to Matter and share identical syntax

**Energy**
- Not organized in hierarchical structures
- Stored in blocks by data type
- Stores parameter snapshots, constraint snapshots and time-series history

## 1.5 Grammatical Status of Q
Q is the fundamental unit for representing relations. It can be code or a model.
There are two types of Q references
- `q:<q_id>`: Reference a registered Q
- ``q:```xxx``` ``: Inline code block for direct expression / code writing

## 1.6 hoc / dbfs Convention
- **hoc**: Temporary script state.
- **dbfs**: Formal persistent state.

All subsequent occurrences of `hoc` and `dbfs` follow this shorthand convention without further expansion.

### 1.6.1 hoc (Temporary Script State)
All Matter entities and Energy structures are declared and described via Python dictionaries. No database dependency, supporting rapid iteration, prototype verification and small-scale instance debugging.
- Matter: A single top-level dictionary. All child matters are written explicitly within this dictionary using long keys and values.
> Schematic example (for comprehension only, not complete syntax)
```python
Instance = {
    "Cat": {...},
    "(Cat)<egoname>": {...},
    "[Cat]<envname>": {...},
    "{Cat}<energyname>": {...}
}
```
- Energy: Split by tables, one dictionary per table.
- Q: Written directly as functions inside scripts.

### 1.6.2 dbfs (Formal Persistent State)
Multi-medium separated storage architecture to decouple structure, functions and data:
- Matter structural definitions: Persisted to SQLite.
- Q functional logic: Stored in independent file systems, mapped to database metadata.
- Energy time-series data, parameter/threshold snapshots: Stored in DuckDB to support time-series queries, state playback and evolution tracing.

## 1.7 Keyword Table
**Entity Types**: `Matter` `Ego` `Field` `Entity` `Q`

**Hierarchical Blocks**: `Structure` `Capability` `Relation` `Ordinance` `Feature` `Goal` `Symbol`

**Hierarchical Label Definitions**
- S = Structure layer
- C = Capability layer
- R = Relation layer
- O = Ordinance layer
- F = Feature layer
- G = Goal layer
- L = Symbol layer

**Reserved Fields**: None

**Special Keys**
The following special keys are common across all tables:
- `_tick`: Records current tick, format `YYYYMMDDHHMMSS`, e.g. `20260918224522`

## 1.8 Naming Rules
### 1.8.1 Entity ID
Format: `[A-Za-z_][A-Za-z0-9_]*`
Applicable to all entities: Matter, Ego, Env
Applicable to all records: parameters, constraints, relations
Applicable to all components: Q
Q allows non-semantic identifiers, may use q_ + random number / auto-increment number

### 1.8.2 Key Format & ID Rules
- Hierarchy nodes use path keys as dictionary keys
- Path key format: `parentpath_hierarchylabel_localID`
- Local ID has two categories:
  - Auto-increment numeric ID: Ordinary nodes, starting from 1 within the same parent path and same layer
  - System reserved keywords: Nodes for special purposes, using keywords instead of numbers
- The combination of parent path + current layer + local ID guarantees global uniqueness

Example:
```
root_s_1_s          # auto-increment numeric ID
root_s_2_s          # auto-increment numeric ID
root_s_self_s       # system reserved keyword
root_s_meta_s       # system reserved keyword
```

### 1.8.3 Versioning Rules
- hoc: Script-level version number written in script header; individual nodes do not carry `version`
- dbfs: Node-level version number; every node carries its own `version`
- Format: `YYYYMMDDHHMMSS`
- Example: `20260918224522`

**Mandatory Version Storage Convention**
When modifying Matter nodes, parameters or constraint records, new version rows are appended instead of in-place overwriting. The system automatically selects the record with the maximum `version` as the latest valid record.

Example:
```
root_s_1_s  version=20260918224522
root_s_1_s  version=20260919093000
```

## 1.9 Reference Rules
1. All references must point to registered IDs. Bare strings are forbidden (except L layer).
2. Cross-table references must carry prefixes.
3. `value` supports literals or Q references.

## 1.10 Value Syntax
value is the core content of a node and permits exactly three types:

### 1. Numeric Literals
- Integer: `1`
- Float: `0.05`, `1.5e-3`

### 2. Q Reference
- Format: `q:<q_id>`
- Example: `q:q3f8a2`

### 3. Inline Q
- Format: ``q:```xxx``` ``
- Only simple function expressions or relational comparisons allowed
- Example: ``q:```val <= 200``` ``

**Mandatory Rules**
- **value must NOT contain nested dictionaries.** All nodes are flattened. Hierarchy information is carried solely by keys.
- Literals are limited to numeric values only.
- Inline Q only allows simple relational comparisons and basic arithmetic expressions; **loops, branches and other complex logic are forbidden inline**. Complex logic must be encapsulated as independently registered Q functions.

---

# Part II: Block-wise Definition
## 2.1 Matter 
### Overview
Matter is the problem ontology structure of an instance, carrying seven-layer definitions for Field, Ego and Env entities. Declared in key-value form. Core runtime block.

### hoc
1. One top-level dictionary, dictionary name = Matter name. E.g. Cat = { ... }.
2. Each key inside the dictionary is a path key in the format: parentpath_hierarchylabel_localID
3. Write the node itself first for each layer; expand internal structure only if needed
   - Node only: `"Cat_s_1": "heart"`
   - Expand inner structure: `"Cat_s_1_s_1": "ventricle"`
4. value directly holds content without nested dictionaries

```python
Cat = {
    "Cat_s_1": "heart",
    "Cat_s_1_s_1": "ventricle",
    "Cat_s_1_s_2": "atrium",
    "Cat_s_2": "lung",
    "Cat_c_1": "q:q97594"
}
```
5. There is no requirement to fill all five/seven layers; define only required layers. Defined layers cannot be empty.
6. Version number resides in script header, nodes do not carry individual versions.

### dbfs
Matter maps to one SQLite table. All Matter nodes are stored in this unified table, no table splitting.
- Database file: `<mattername>.db`
- Table name: `<mattername>`

**Columns**
- key: TEXT, path key e.g. Cat_s_1
- value: TEXT, node content, literal or Q reference
- version: TEXT, version number, format YYYYMMDDHHMMSS

**Table Creation SQL**
```sql
CREATE TABLE Cat (
    key     TEXT,
    value   TEXT,
    version TEXT
);
```

All Matter nodes are stored in table `<mattername>`. Entity type is distinguished by the first segment of key:
- Cat_... : Problem ontology
- ()Cat_... : Ego
- []Cat_... : Env

**Sample Data**
```sql
INSERT INTO Cat (key, value, version) VALUES
('Cat_s_1', 'heart', '20260918224522'),
('Cat_s_1_s_1', 'ventricle', '20260918224522'),
('Cat_s_1_s_2', 'atrium', '20260918224522'),
('Cat_s_2', 'lung', '20260918224522'),
('Cat_c_1', 'q:q787876', '20260918224522'),
('()Cat_g_1', 'g_eat_full', '20260918224522'),
('[]Cat_s_1', 'indoor', '20260918224522');
```

### Special Provision
Root nodes allow empty string value to indicate no extra structural content

### Mandatory Conventions
- value must NOT contain nested dictionaries
- No requirement to fill all five/seven layers, define only required layers
- Structure must be queryable and must have a root structure
- The first segment of key must match the top-level dictionary name
- Table operations are isolated; only one table may be written per operation, no cross-table bulk API
- Multiple rows may be inserted in one INSERT statement for a single table, but multiple tables cannot be merged in one write
- When adding new entity structures, parameter table records must be added at minimum; parameter, constraint and relation tables are recommended to be populated together for a valid entity
- Parameters, relations and constraints of the entity may be appended or modified later

---

## 2.2 Parameter Table (_parameter)
### Overview
Parameter table stores entity parameters, attributes and configurations. Core runtime block.
Parameter table also defines metrics for Energy records, e.g. credibility and confidence of a parameter.

### hoc
Dictionary. Define Matter table first, then parameter table to maintain reference visibility.

```python
# Matter table
matter = {
    "Cat": "",
    "phys_s_1": "height",
    "phys_s_2": "weight"
}
# Parameter table
_parameter = {
    "Cat-phys_s_1": [
        [30, 1, "20260101000000"],
        [32, 1, "20260601000000"],
        [35, 1, "20261201000000"]
    ],
    "Cat-phys_s_2": [
        [4.5, 2, "20260101000000"]
    ]
}
```
- key: id0-id1. id0 and id1 are both path keys from Matter table, joined by hyphen `-`
- value: list of lists. Each sublist contains three elements
  1. parameter value
  2. idx, global auto-increment sequence number
  3. version number

### dbfs
Shared `_parameter` table.

**Columns**
- id0: TEXT, reference of subject or parameter record
- id1: TEXT, semantic or metric label
- value: TEXT, parameter value
- idx: INTEGER, global auto-increment sequence number
- version: TEXT, version number, format YYYYMMDDHHMMSS

**Table Creation SQL**
```sql
CREATE TABLE _parameter (
    id0      TEXT,
    id1      TEXT,
    value    TEXT,
    idx      INTEGER,
    version  TEXT
);
```

**Sample Data**
```sql
INSERT INTO _parameter (id0, id1, value, idx, version) VALUES
('Cat', 'phys_s_1', '30', 1, '20260101000000'),
('Cat', 'phys_s_1', '32', 1, '20260601000000'),
('Cat', 'phys_s_1', '35', 1, '20261201000000'),
('Cat', 'phys_s_2', '4.5', 2, '20260101000000');
```

### Special Provision
- key is formed by joining two Matter path keys to keep semantics non-isolated
- idx is globally auto-incremented and assigned to new objects; idx remains unchanged when updating the same object
- version marks the value of the same object at different timestamps
- One parameter can have multiple version records, sorted by version, maximum version is latest

**Two Declaration Modes**
1. **Subject + Semantic**: `('Cat', 'phys_s_1', '30', 1, '20260101000000')` means Cat's height = 30.
2. **Parameter + Metric**: `('param_1', 'confidence', '0.6', 2, '20260101000000')` means confidence of the 1st parameter (Cat's height) = 0.6.

> Supplementary convention: Derived IDs with prefix like `param_1` may be auto-generated by engine or manually written. **Prefixes are only for reference layer marking and not stored in raw table records.**

### Mandatory Conventions
- When adding new entity structures, parameter table records must be added at minimum
- idx is immutable after allocation
- When updating the same object, idx stays unchanged; only value and version change

---

## 2.3 Constraint Table (_constraint)
### Overview
Constraint table stores entity constraints, thresholds and rules. Core runtime block.
Structure matches parameter table, but value stores constraint expressions or Q references.

### hoc
Dictionary. Define Matter table first, then constraint table.

```python
# Matter table
matter = {
    "Cat": "",
    "phys_s_1": "height",
    "phys_s_2": "weight"
}
# Constraint table
_constraint = {
    "Cat-phys_s_1": [
        ["q:```val <= 200```", 1, "20260101000000"],
        ["q:q3f8a2", 1, "20260101000001"]
    ]
}
```
- key: id0-id1. id0 and id1 are both path keys from Matter table, joined by hyphen `-`
- value: list of lists. Each sublist contains three elements
  1. constraint expression or Q reference
  2. idx, global auto-increment sequence number
  3. version number
- idx remains unchanged for updates on same object, only version changes
- Different constraints use different idx

### dbfs
Shared `_constraint` table.

**Columns**
- id0: TEXT, reference of subject or constraint record
- id1: TEXT, semantic or metric label
- value: TEXT, constraint expression or Q reference
- idx: INTEGER, global auto-increment sequence number
- version: TEXT, version number, format YYYYMMDDHHMMSS

**Table Creation SQL**
```sql
CREATE TABLE _constraint (
    id0      TEXT,
    id1      TEXT,
    value    TEXT,
    idx      INTEGER,
    version  TEXT
);
```

**Sample Data**
```sql
INSERT INTO _constraint (id0, id1, value, idx, version) VALUES
('Cat', 'phys_s_1', 'q:```val <= 200```', 1, '20260101000000'),
('Cat', 'phys_s_1', 'q:q3f8a2', 1, '20260101000001');
```

### Special Provision
- key is formed by joining two Matter path keys to keep semantics non-isolated
- idx is globally auto-incremented and assigned to new objects; idx remains unchanged when updating the same object
- version marks the value of the same object at different timestamps
- One constraint can have multiple version records, sorted by version, maximum version is latest
- value supports two types: inline Q and referenced Q
- Constraint evaluation must return result: True / False / residual value

**Two Declaration Modes**
1. **Constraint Parameter**: `('Cat', 'phys_s_1', 'q:```val <= 200```', 1, '20260101000000')` means constraint for Cat's height parameter: val ≤ 200.
2. **Constraint + Metric**: `('constraint_1', 'severity', 'q:```val > 0.8```', 3, '20260101000000')` means severity judgment for the 1st constraint: val > 0.8.

> Supplementary convention: Derived IDs with prefix like `constraint_1` may be auto-generated by engine or manually written. **Prefixes are only for reference layer marking and not stored in raw table records.**

### Mandatory Conventions
- When adding new entity structures, constraint table records are recommended to be populated
- idx is immutable after allocation
- When updating the same object, idx stays unchanged; only value and version change
- constraint value allows only two types: inline Q and referenced Q

---

## 2.4 Relation Table (_relation)
### Overview
Relation table stores relationships, connections and dependencies between entities. Core runtime block.
Structure matches parameter and constraint tables, value stores relational expressions or Q references. Pairwise relations are expressed via Q functions; inline Q only for simple expressions.
Relation table expresses both internal relations (components within one subject, capability layer) and external relations (between different subjects, relation layer).

### hoc
Dictionary. Define Matter table first, then parameter table, then relation table.

**Internal Relation Example: Cat foreleg and hindleg**
```python
# Matter table
matter = {
    "Cat": "",
    "Cat_s_1": "foreleg",
    "Cat_s_2": "hindleg"
}
# Relation table
_relation = {
    "Cat_s_1-Cat_s_2": [
        ["q:q3f8a2", 1, "20260101000000"]
    ]
}
```

**External Relation Example: Cat food and cat weight**
```python
# Matter table
matter = {
    "Cat": "",
    "phys_s_2": "weight",
    "cat_food": ""
}
# Parameter table
_parameter = {
    "Cat-phys_s_2": [[4.5, 1, "20260101000000"]]
}
# Relation table
_relation = {
    "cat_food-param_1": [
        ["q:q7b2c", 1, "20260101000000"]
    ]
}
```

- key: id0-id1. Both are referenceable IDs joined by hyphen `-`
- id0, id1 can be: Matter path key, parameter record reference
- value: list of lists. Each sublist contains three elements
  1. relational expression or Q reference
  2. idx, relation-table auto-increment number
  3. version number
- idx remains unchanged for updates on same object, only version changes
- Different relations use different idx

### dbfs
Shared `_relation` table.

**Columns**
- id0: TEXT, reference of subject or relation record
- id1: TEXT, semantic or metric label
- value: TEXT, relational expression or Q reference
- idx: INTEGER, relation-table auto-increment sequence number
- version: TEXT, version number, format YYYYMMDDHHMMSS

**Table Creation SQL**
```sql
CREATE TABLE _relation (
    id0      TEXT,
    id1      TEXT,
    value    TEXT,
    idx      INTEGER,
    version  TEXT
);
```

**Sample Data**
```sql
-- Internal relation
INSERT INTO _relation (id0, id1, value, idx, version) VALUES
('Cat_s_1', 'Cat_s_2', 'q:q3f8a2', 1, '20260918224522');
-- External relation
INSERT INTO _relation (id0, id1, value, idx, version) VALUES
('cat_food', 'param_1', 'q:q7b2c', 2, '20260918224522');
```

### Special Provision
- key is formed by joining two referenceable IDs to keep semantics non-isolated
- idx auto-increments within relation table and assigned to new objects; idx remains unchanged when updating the same object
- version marks the state of the same relation at different timestamps
- One relation can have multiple version records, sorted by version, maximum version is latest
- value supports two types: inline Q and referenced Q
- Pairwise relations are implemented via Q functions; inline Q only for simple expressions

> Supplementary convention: Derived IDs with prefix like `rel_1` may be auto-generated by engine or manually written. **Prefixes are only for reference layer marking and not stored in raw table records.**

**Three Declaration Modes**
1. **Relation Function**: `('Cat_s_1', 'Cat_s_2', 'q:q3f8a2', 1, '20260918224522')` means the relation between foreleg and hindleg is described by Q function.
2. **Simple Expression**: `('Cat_s_1', 'Cat_s_2', 'q:```ratio=0.15```', 1, '20260918224523')` means foreleg/hindleg ratio = 0.15.
3. **Relation + Metric**: `('rel_1', 'strength', 'q:```0.9```', 3, '20260918224522')` means strength of the 1st relation = 0.9.

**Internal / External Relation Distinction**
- Both IDs belong to same subject → Internal relation
- Two IDs belong to different subjects → External relation

### Mandatory Conventions
- idx is immutable after allocation
- When updating the same object, idx stays unchanged; only value and version change
- relation value allows only two types: inline Q and referenced Q
- Pairwise relations use Q functions; inline Q only for simple expressions

---

## 2.5 State (_state)
### Overview
State table stores full variables within the current tick window, the sole data source for engine runtime calculation. After tick completes, data is archived and window resets. Core runtime block.
State table resides in engine memory and maintained automatically by engine; no manual declaration, so no hoc/dbfs split.

**Columns**
- `_tick`: special key recording current tick
- path key: consistent with keys in Matter / Energy
- value: value in current tick

### Special Provision
- One instance **supports multiple Ego subjects**, each Ego has independent state table
- Ontology + its affiliated Ego share one state table
- Env has separate state table

### Mandatory Conventions
None

---

## 2.6 Sequence (_sequence)
### Overview
Sequence table stores continuously tracked core time-series metrics. Metrics are computed or fetched from state table and appended per _tick for trend analysis and time-series playback. Core runtime block.
Data source: previous window snapshot from state table, accumulated persistently.

### hoc
Dictionary.
```python
sequence = {
    "_tick": "20260918224522",
    "Cat_c_1": 0.05,
    "()Cat_g_1": 0.8
}
```

### dbfs
Stored in database, appended row by row per _tick.

**Columns**
- _tick: TEXT, record current tick, format YYYYMMDDHHMMSS
- key: TEXT, consistent with keys in Matter / Energy
- value: TEXT, value in current tick

**Table Creation SQL**
```sql
CREATE TABLE sequence (
    _tick   TEXT,
    key     TEXT,
    value   TEXT
);
```

**Sample Data**
```sql
INSERT INTO sequence (_tick, key, value) VALUES
('20260918224522', 'Cat_c_1', '0.05'),
('20260918224522', '()Cat_g_1', '0.8'),
('20260918224523', 'Cat_c_1', '0.06'),
('20260918224523', '()Cat_g_1', '0.8');
```

### Special Provision
- Special key _tick is global
- Data source: previous window snapshot from state table, accumulated persistently

### Mandatory Conventions
None

---

## 2.7 Experience (_experience)
### Overview
Experience table is historical archive of state table. State snapshot of every tick is moved into experience table and stored per _tick for history playback. Core runtime block.
Experience table is lookup-only, not primary operational table. Structure can be extended later to accommodate intent, feedback snapshots differentiated via _TYPE.

### hoc
Three-level nested dictionary.
```python
_experience = {
    "Cat": {
        "20260918224523": {
            "_state": {}
        }
    },
    "[]Cat": {
        "20260918224523": {
            "_state": {}
        }
    }
}
```
- 1st level key: subject name, Cat / []Cat
- 2nd level key: _tick
- 3rd level key: _TYPE, e.g. _state / _intent / _feedback
- innermost: content of corresponding type
- Only one _TYPE per tick record

### dbfs
Shared `_experience` table.

**Columns**
- _from: TEXT, subject name e.g. Cat / []Cat
- _tick: TEXT, record current tick, format YYYYMMDDHHMMSS
- _type: TEXT, record type e.g. _state / _intent / _feedback
- _value: TEXT, content

**Table Creation SQL**
```sql
CREATE TABLE _experience (
    _from   TEXT,
    _tick   TEXT,
    _type   TEXT,
    _value  TEXT
);
```

**Sample Data**
```sql
INSERT INTO _experience (_from, _tick, _type, _value) VALUES
('Cat', '20260918224523', '_state', '{}'),
('Cat', '20260918224524', '_intent', '{}'),
('[]Cat', '20260918224523', '_state', '{}');
```

### Special Provision
- Lookup-only auxiliary table, structure extensible with _TYPE
- Difference from state table: state table = current tick; experience table = historical ticks
- Difference from sequence table: sequence stores one key per row; experience stores full snapshot per tick in one row
- Only one _TYPE per tick record

### Mandatory Conventions
None

---

## 2.8 Register (_register)
### Overview
Register table is the global key-value mapping center for resolving keys, retrieving labels and reverse lookup. Retrieve value by simple key query. Core runtime block.

> Supplementary positioning: Register table is the core dictionary of XGI symbol layer, supporting bidirectional translation between symbols and natural language via `_language` table.

### hoc
Dictionary.
```python
_register = {
    "Cat": "cat",
    "()Cat": "ego of cat",
    "[]Cat": "environment of cat",
    "q3438437": "health calculation"
}
```

### dbfs
Shared `_register` table.

**Columns**
- key: TEXT, entity ID
- value: TEXT, entity label

**Table Creation SQL**
```sql
CREATE TABLE _register (
    key     TEXT,
    value   TEXT
);
```

**Sample Data**
```sql
INSERT INTO _register (key, value) VALUES
('Cat', 'cat'),
('()Cat', 'ego of cat'),
('[]Cat', 'environment of cat'),
('q3438437', 'health calculation');
```

### Special Provision
None

### Mandatory Conventions
None

---

## 2.9 Intent (_intent)
### Overview
Intent table stores feasible paths and execution intents obtained by Ego via goal filtering and constraint solving. Ego exclusive cognitive table.
_tick references tick in state table, indicating which state generated this intent. Multiple intents may be produced under one state, corresponding to multiple goals. Multiple goals are finally synthesized into one executable path marked by special key `_plan`.

> Supplementary rule: Multi-goal merging and conflict resolution logic is natively handled by **engine**.

### hoc
Nested dictionary.
```python
_intent = {
    "Cat": {
        "20260918224523": {
            "g_find_food": "outdoor -> search -> eat",
            "g_avoid_danger": "indoor -> stay",
            "_plan": "outdoor -> search -> eat -> return"
        }
    }
}
```
- 1st level key: subject name e.g. Cat
- 2nd level key: _tick, referencing tick in state table
- 3rd level key: goal ID or synthesized _plan
- value: intent content

### dbfs
Shared `_intent` table.

**Columns**
- _from: TEXT, subject name
- _tick: TEXT, referencing tick in state table
- key: TEXT, goal ID or _plan
- value: TEXT, intent content

**Table Creation SQL**
```sql
CREATE TABLE _intent (
    _from   TEXT,
    _tick   TEXT,
    key     TEXT,
    value   TEXT
);
```

**Sample Data**
```sql
INSERT INTO _intent (_from, _tick, key, value) VALUES
('Cat', '20260918224523', 'g_find_food', 'outdoor -> search -> eat'),
('Cat', '20260918224523', 'g_avoid_danger', 'indoor -> stay'),
('Cat', '20260918224523', '_plan', 'outdoor -> search -> eat -> return');
```

### Special Provision
- Owned exclusively by Ego
- _tick references tick in state table
- Multiple intents may be generated under one state corresponding to multiple goals
- Multiple goals are synthesized into one executable path marked by special key _plan
- Same mechanism as experience table, shared table, differentiated by _from

### Mandatory Conventions
None

---

## 2.10 Feedback (_feedback)
### Overview
Feedback table stores real-time feedback data throughout intent execution for cognitive iteration and goal correction. Ego exclusive cognitive table.
_tick corresponds to tick in intent table, which is also the tick of previous state table. Feedback table only maps to one _plan, since only the synthesized final path gets executed.

### hoc
Nested dictionary.
```python
_feedback = {
    "Cat": {
        "20260918224523": "success"
    }
}
```
- 1st level key: subject name e.g. Cat
- 2nd level key: _tick, corresponding to tick in intent table
- value: feedback content

### dbfs
Shared `_feedback` table.

**Columns**
- _from: TEXT, subject name
- _tick: TEXT, corresponding to tick in intent table
- value: TEXT, feedback content

**Table Creation SQL**
```sql
CREATE TABLE _feedback (
    _from   TEXT,
    _tick   TEXT,
    value   TEXT
);
```

**Sample Data**
```sql
INSERT INTO _feedback (_from, _tick, value) VALUES
('Cat', '20260918224523', 'success');
```

### Special Provision
- Owned exclusively by Ego
- _tick matches tick in intent table
- One feedback maps to exactly one _plan, no multiple entries
- Same mechanism as experience table, shared table, differentiated by _from

### Mandatory Conventions
None

---

## 2.11 Language (_language)
### Overview
Language table supports symbol layer and parameter constraint parsing, storing sentence paradigms, symbol representations and feature combinations. Ego exclusive cognitive table.
Used for bidirectional translation between L symbol layer and natural language.

### hoc
Dictionary.
```python
_language = {
    "sym_risk": "risk level",
    "sym_profit": "profit level",
    "g_find_food": "find food",
    "g_avoid_danger": "avoid danger"
}
```

### dbfs
Shared `_language` table.

**Columns**
- key: TEXT, symbol ID
- value: TEXT, natural language expression

**Table Creation SQL**
```sql
CREATE TABLE _language (
    key     TEXT,
    value   TEXT
);
```

**Sample Data**
```sql
INSERT INTO _language (key, value) VALUES
('sym_risk', 'risk level'),
('sym_profit', 'profit level'),
('g_find_food', 'find food'),
('g_avoid_danger', 'avoid danger');
```

### Special Provision
- Owned exclusively by Ego
- Handles bidirectional translation between symbols and natural language
- Not involved in internal deduction computation

### Mandatory Conventions
None

---

## 2.12 Training Data (_train)
### Overview
Training table aggregates internal and external data for model training, Ego reflection and cognitive upgrade. Ego exclusive cognitive table.
Data is summarized from other tables for dedicated training tasks.

### hoc
Nested dictionary.
```python
_train = {
    "ego_reflect": {
        "20260918224523": {
            "state": {},
            "intent": {},
            "feedback": {}
        }
    }
}
```
- 1st level key: _target, training objective or purpose
- 2nd level key: _tick
- 3rd level key: data source or type
- value: data content

### dbfs
Shared `_train` table.

**Columns**
- _target: TEXT, training objective or purpose
- _tick: TEXT, record current tick
- key: TEXT, data source or type
- value: TEXT, data content

**Table Creation SQL**
```sql
CREATE TABLE _train (
    _target  TEXT,
    _tick    TEXT,
    key      TEXT,
    value    TEXT
);
```

**Sample Data**
```sql
INSERT INTO _train (_target, _tick, key, value) VALUES
('ego_reflect', '20260918224523', 'state', '{}'),
('ego_reflect', '20260918224523', 'intent', '{}'),
('ego_reflect', '20260918224523', 'feedback', '{}');
```

### Special Provision
- Aggregates all internal table data plus external data
- _target marks training objective
- Used for model training, Ego reflection and cognitive upgrade

### Mandatory Conventions
None

---

## 2.13 Report Summary (_report)
### Overview
Report summary table is system-wide observation panel. It does not participate in underlying tick flow and core engine computation. Aggregates core metrics from all tables for human observation, supports Ego virtual deduction, stores hypothetical experiment observations, distinguishes real runtime data and virtual deduction data.
Upper-layer auxiliary non-fundamental table.

### hoc
Nested dictionary.
```python
_report = {
    "real": {
        "20260918224523": {
            "state": {},
            "intent": {},
            "feedback": {}
        }
    },
    "virtual": {
        "20260918224523": {
            "state": {},
            "intent": {},
            "feedback": {}
        }
    }
}
```
- 1st level key: data type, real / virtual
- 2nd level key: _tick
- 3rd level key: observation source or type
- value: observation content

### dbfs
Shared `_report` table.

**Columns**
- _type: TEXT, data type, real / virtual
- _tick: TEXT, record current tick
- key: TEXT, observation source or type
- value: TEXT, observation content

**Table Creation SQL**
```sql
CREATE TABLE _report (
    _type   TEXT,
    _tick   TEXT,
    key     TEXT,
    value   TEXT
);
```

**Sample Data**
```sql
INSERT INTO _report (_type, _tick, key, value) VALUES
('real', '20260918224523', 'state', '{}'),
('real', '20260918224523', 'intent', '{}'),
('virtual', '20260918224523', 'state', '{}');
```

### Special Provision
- Does not participate in underlying tick flow and core engine computation
- Distinguishes real runtime data and virtual deduction data
- Supports Ego virtual deduction (mental trial run)

**Data Type Definition**
- real: real execution data
- virtual: virtual deduction / hypothetical data

### Mandatory Conventions
None

---

## 2.14 AI Collaboration (_llm)
### Overview
AI collaboration table records prompts and decision rationales of specific IDs during human-AI collaboration. Upper-layer auxiliary non-fundamental table.
Used to trace collaboration history, review decision basis and support subsequent iteration.

### hoc
Nested dictionary.
```python
_llm = {
    "prompt_001": {
        "version": "20260918224522",
        "prompt": "...",
        "reason": "..."
    }
}
```

### dbfs
Shared `_llm` table.

**Columns**
- id: TEXT, collaboration record ID
- version: TEXT, version number, format YYYYMMDDHHMMSS
- prompt: TEXT, user input prompt
- reason: TEXT, decision rationale

**Table Creation SQL**
```sql
CREATE TABLE _llm (
    id       TEXT,
    version  TEXT,
    prompt   TEXT,
    reason   TEXT
);
```

**Sample Data**
```sql
INSERT INTO _llm (id, version, prompt, reason) VALUES
('prompt_001', '20260918224522', '...', '...');
```

### Special Provision
- Not involved in engine computation
- Stores rationale only, not final results
- Records collaboration history for review and iteration

### Mandatory Conventions
None

---

## 2.15 FORGE (_forge)
### Overview
FORGE table is operation log table recording full change traces of FORGE incremental protection module and GOV legacy refactor module. Upper-layer auxiliary non-fundamental table.
Used to trace rule validation, review results, decision basis and governance progress for normalized engineering audit.

### Why no hoc
FORGE table is internal operation log written automatically by engine without manual declaration, so no hoc/dbfs split.

### dbfs
Shared `_forge` table.

**Columns**
- id: TEXT, operation record ID
- _tick: TEXT, record current tick
- _module: TEXT, module, FORGE / GOV
- _action: TEXT, action e.g. Fortify / Observe / Refine / Gather / Enforce / Gauge / Outline / Verify
- _target: TEXT, target of operation
- _result: TEXT, operation result
- _reason: TEXT, operation rationale

**Table Creation SQL**
```sql
CREATE TABLE _forge (
    id       TEXT,
    _tick    TEXT,
    _module  TEXT,
    _action  TEXT,
    _target  TEXT,
    _result  TEXT,
    _reason  TEXT
);
```

**Sample Data**
```sql
INSERT INTO _forge (id, _tick, _module, _action, _target, _result, _reason) VALUES
('op_001', '20260918224523', 'FORGE', 'Fortify', '...', '...', '...');
```

### Special Provision
- Not involved in engine computation
- Records operation traces of FORGE / GOV modules
- Supports normalized audit and traceability

**Module Action Definition**
- FORGE: Incremental protection module, actions: Fortify / Observe / Refine / Gather / Enforce
- GOV: Legacy asset refactor module, actions: Gauge / Outline / Verify

### Mandatory Conventions
None

---

# Part III: Q Function Specification
## Overview
Q is the fundamental unit for representing relations. It can be code or a model. It has independent ID and stored separately. It does not belong to Matter nor Energy.

### hoc
Written directly as functions in script.
```python
def q3f8a2():
    # prompt: calculate health from blood oxygen and loss
    # reason: blood oxygen is primary metric, loss is correction term
    return blood_oxygen - loss
```
- No parameter declaration in function header
- Parameters are global variables injected by engine at runtime
- prompts and reason are written as comments inside function
- return statement is optional, depends on Q purpose

### dbfs
Stored as standalone script files, mapped to database metadata.
```python
# q3f8a2.py
def q3f8a2():
    # prompt: calculate health from blood oxygen and loss
    # reason: blood oxygen is primary metric, loss is correction term
    return blood_oxygen - loss
```
Meanwhile write trace into _llm table:
```sql
INSERT INTO _llm (id, version, prompt, reason) VALUES
('q3f8a2', '20260918224522', 'calculate health from blood oxygen and loss', 'blood oxygen is primary metric, loss is correction term');
```

### Reference Syntax
- Format: `q:<q_id>`
- Example: `q:q3f8a2`

### Valid Reference Locations
- C capability layer of Matter
- Parameter value
- Constraint expressions
- Ego deduction, evaluation, iteration
- Energy state update and time-series calculation

### Version Management
- hoc: no version control
- dbfs: Q itself does not carry version number; version info is stored in register table value
- When upgrading, query register table to find upgradable Q

```python
_register = {
    "q3f8a2": {
        "label": "health calculation",
        "version": "20260918224522"
    }
}
```

### Special Provision
- Function name = q + random number, non-semantic; semantics reside in register table
- No parameter declaration in function header; variables fetched from global scope
- prompts and reason written as internal comments
- In dbfs deployment, trace is inserted into _llm table

### Mandatory Conventions
- Uniform function signature `def qxxxxxx():`, no extra underscores
- prompts and reason comments are mandatory
