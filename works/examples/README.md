# SurvX Examples

The examples directory holds demo projects for SurvX.
**All examples are for illustrating paradigm concepts only, not for official deliverable systems.**
Official research vehicles and industry solutions live in the `solutions/` directory (humans, molin).

SurvX is an entity meta-modeling paradigm, used to model entities that carry goals, constraints, states, and interactions.
These demos progress from simple to advanced, gradually validating SurvX core capabilities and the capabilities of the survx-frontend-web frontend sub-paradigm.

## Naming Conventions

| Level | Style | Example |
|-------|-------|---------|
| Demo identifier (name) | PascalCase | `HelloWorld`, `SimpleCounter` |
| Demo display title (title) | Chinese, may contain proper nouns | `简单计数器`, `Works 灰度演示` |
| Blueprint internal fields (Energy, relation, etc.) | kebab-case `-` | `goal-type`, `energy-value` |
| Frontend sub-paradigm name | kebab-case `-` | `survx-frontend-web` |

> Note: system table names in `design_zh.md` (`_parameter`, `_constraint`, etc.) use an underscore prefix,
> which belongs to storage-layer conventions and does not conflict with the blueprint field naming in this document.

## Demo List (ordered by development difficulty)

### Basic Examples (no Ego; validate base blueprints and state flow)

1. **HelloWorld**
    The smallest SurvX entry example. A simplest Field entity with only basic Goal and Energy fields.
    After the instance runtime starts, it automatically loads the blueprint, generates a basic interaction panel, and allows reading and writing entity state.
    Validates: the most basic blueprint loading, instance initialization, engine communication, and basic frontend sub-paradigm rendering.

2. **SimpleCounter**
    The minimal SurvX demo. A counter entity supporting increment and decrement.
    Constraint: the value cannot be less than 0.
    Validates: Field blueprint declaration, Energy read/write, basic business constraint checking, engine event loop, and auto-generated frontend panel.

3. **SensorSim**
    A simulated sensor entity. Automatically updates metric state on a fixed cadence.
    Validates: autonomous entity state updates, periodic events, out-of-range alerts, and WebSocket real-time state push.

### Advanced Examples (multi-entity, works gray release, frontend sub-paradigm)

4. **MultiEntityLink**
    Multiple Field entities coexist, read each other's state, and produce event interactions.
    Validates: the Relation layer, cross-entity event communication, and multi-entity coexistence.

5. **WorksGrayDemo**
    Demonstrates the works mechanism and instance gray release.
    Prepares two sets of behavior-logic blueprints to upgrade and roll back logic for a subset of instances.
    Validates: works version management and instance gray iteration.

6. **DynamicFormView**
    A demo for the survx-frontend-web frontend sub-paradigm.
    UI layout and controls are all declared in the Field blueprint's relation. Modify the blueprint and the interface reassembles automatically, with no frontend code changes.
    Validates: blueprint-driven dynamic interface assembly and bidirectional interaction.

7. **ViewCombineWorkspace**
    A workspace where entity panels are freely combined.
    Users can drag, resize, and freely arrange entity panels; custom layouts can be saved as view entities and restored automatically on next open.
    Validates: dynamic multi-panel composition and user-defined work views.

8. **AITown**
    A lightweight multi-agent simulation town. Multiple resident entities perceive and interact within an environment entity, with render2d_web 2D visualization.
    Validates: multi-entity coexistence, a global environment entity, and 2D canvas visualization.

### Expert Examples (with Ego; validate XGI core capabilities)

9. **EgoSelfMonitor**
    A basic Ego self-check entity. The entity has the required four layers G/L/R/O, can read its own blueprint and state, and continuously self-checks constraints.
    Validates: Ego self-reference and entity introspection.

10. **EgoAdaptiveThreshold**
    An Ego entity with controlled adaptive capability. It can autonomously adjust its own parameters within business constraint boundaries.
    Validates: controlled self-evolution and adaptive parameter adjustment.

### Optional CLI Example

**DemoCliOnly**
Does not start the frontend; operates entities only through scripts + engine.
Proves that SurvX can run independently of the frontend sub-paradigm.

## Recommended Development Order

HelloWorld → SimpleCounter → SensorSim → MultiEntityLink → WorksGrayDemo →
DynamicFormView → ViewCombineWorkspace → AITown → EgoSelfMonitor →
EgoAdaptiveThreshold → (optional: DemoCliOnly)

## Boundaries

- `examples/`: demos, for illustrating paradigm features. Robustness is not pursued; not for official research or business delivery.
- `solutions/`: official solutions humans, molin. For long-term research and real industry data landing.