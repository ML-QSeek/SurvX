# Tools Directory

tools holds the general engineering tools, runtime foundation, rendering capabilities, and external adapters of the SurvX paradigm.
Scenario-agnostic, reusable, non-business, non-kernel ¡ª referenced and integrated by examples and solutions as needed.
It does not hold business logic, research solutions, or paradigm kernel code.

> The kernel defines rules, tools build infrastructure, examples demonstrate capabilities, solutions deliver results.

## Directory Positioning

| Directory | Responsibility |
|-----------|----------------|
| `survx/` | Paradigm core: entity mechanisms, Energy, constraints, Ego, event scheduling, blueprint parsing |
| `tools/` | Pluggable engineering components built on kernel contracts: communication, connection, data fetching, frontend, AI access, dev tools |
| `solutions/` | Business / research landing (humans, molin), with full business logic |
| `examples/` | Lightweight demos, only showcasing paradigm capabilities, not for production delivery |

Naming follows global conventions: directories snake_case `_`, blueprint fields kebab-case `-`.

## Tool List

### CommServer
Communication service. The communication layer of a SurvX instance; both internal and external traffic uniformly go over HTTP and WebSocket.
HTTP dynamic routing: one name = one module = one function = one path; loaded from `routes.json` at startup, supports registration, hot reload, and deregistration at runtime.
WS broadcast channels: one name = one `/ws/{name}` channel; channels are isolated, and everyone connected broadcasts to each other.
Paradigm mapping: implements **Field.R (Relation layer)**, carrying the relationships between the instance and the outside world, and between processes.
Tech: FastAPI + uvicorn; in-memory dictionaries manage the route table and channel pool; no persistence needed in hoc state.

### Connectors
Connectors. Integration components for external interfaces, databases, and other external resources.
Core design: all external resources are modeled as "Ego-less entities" ¡ª external databases, caches, message queues, HTTP/GRPC interfaces, third-party algorithm packages, detection models, peripherals and sensors.
Connectors only do protocol conversion, state mapping, and event pass-through; they own no business goals and do not break kernel constraint mechanisms.

### FinDataFetcher
Financial data fetcher. A data-fetching integration component, responsible for pulling from external data sources, transforming, and writing into the instance.
Like Connectors, it belongs to external integration, but is oriented toward data-fetching scenarios, encapsulating the fetching, field mapping, and scheduling logic of specific data sources.

### Frontend
Frontend framework. The foundation of the survx-frontend-web frontend sub-paradigm.
Reads blueprint UI declarations, auto-assembles pages, renders entity panels, syncs state in real time, and provides a sandboxed runtime environment.
It does not embed any 2D/3D rendering logic; it only provides canvas embedding capability.

### LLMGate
AI integration interface. Uniformly accesses large-model capabilities, used by instances and Ego for reasoning, blueprint generation, and solution evaluation.
AI may only operate on Matter structured blueprints; it is forbidden to tamper with execution flow, bypass the constraint layer, or obtain scheduling privileges.

### Studio
Development workbench. Project management and development tooling, supporting instance creation, blueprint editing, debugging, and publishing.
Corresponds to `instances/survx_studio/`; it is the entry point on the developer side.

## Principles for Adding Tools

Build when needed, grow incrementally; do not pre-create empty directories.
A tool enters tools only if it satisfies all four: general, reusable, not tied to a business scenario, and not part of kernel logic.