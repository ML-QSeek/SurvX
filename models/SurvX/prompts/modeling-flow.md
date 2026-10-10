# SurvX
## Modeling & Reasoning Flow
### Preceding Mandatory Rules (Highest Priority for AI, Not Skippable)
This document depends on the preceding foundational meta-model: `core-content`.
Loading order: **Load the core instance meta-model first, then load this modeling flow.**

### Human-AI Collaboration Mandatory Modes (System Default Rules)
1. **Default mode: Step-by-step discussion, phased output, human-AI alignment.**
   AI MUST NOT output the full blueprint in one pass, skip process steps, or silently complete full modeling.
2. After finishing each key process stage, AI must present current results, wait for user confirmation before proceeding to the next stage.
3. Only when the user explicitly instructs **"full one-time output"**, may AI merge all steps and directly deliver the complete modeling result.
4. All structural plans, module splits, functional designs, logic flows and constraint rules **must be discussed, aligned and confirmed before implementation.**

### Process Input & Output
Input: Unfamiliar external problem / unstructured requirement
Output: Complete runnable Instance blueprint (Field + Ego + Env Matter + Energy)

---

1. **【G‑Goal】Ego retrieves the goal**. The initial goal can be provided by humans from user requirements; the goal targets external problems instead of solving internal issues.
2. Activate Ego’s cognition layer `()survx-relation` to start reasoning.
3. Around the target, consider two parts simultaneously: internal Field entity structure and external environment structure; meanwhile plan relationships between internal and external components.
   > Supplementary specification: Internal structure belongs to the Field layer system, external environment structure belongs to the Env layer system. Interaction links between internal and external are recorded into the Relation external relationship layer of both sides, **NOT stored inside the Ego cognitive knowledge graph.**
4. Reason Capability: Define how each entity component cooperates, executable functions and module capabilities.
5. During reasoning, synchronously write deduced parameters, thresholds and configurations into `_survx` (Energy), persisted as parameter snapshots and constraint snapshots.
6. Build constraint sets: Package required constraints for the corresponding actions and functions to achieve the goal. Constraints serve the goal unidirectionally. Perform validation; if validation fails, roll back and adjust prior structures / capabilities / relationships.
   > Hard rule: The Ordinance layer (O) **converges unidirectionally toward the Goal layer (G).** Constraints must not alter the goal definition in reverse.
7. Summarize Feature characteristics: Sort out multiple alternative paths for entities from Relation, Capability and Ordinance to handle different sub-problems.
👉 At this point the full Entity‑Field blueprint is finished. A standalone Field can solve problems mechanically without requiring an Ego.

### On-demand Subproblem Decomposition
Split the main goal into multiple subproblems:
├─ If a subproblem has an existing available entity (algorithm package / third-party component / existing Field): Stop further decomposition. Only define Relation and Capability for this entity at upper level, inherit its constraints and features.
└─ If no ready entity exists for the subproblem: Recursively return to step 1 and run the full reasoning workflow for this subproblem to generate the corresponding child Field.

> Recursion hard constraint: Recursive modeling only generates **child Field business entities**. Do NOT repeatedly create child Ego or child Env to avoid redundant nested instances.

8. After finishing the base Field blueprint and subproblem decomposition, handle self-iteration, internal optimization and continuous external iteration. This work belongs exclusively to Ego.
9. Design the five base layers of Ego itself:
   - S: List of internal components at Ego’s cognitive level
   - C: Cooperation and operation mechanism among Ego components
   - R: Ego’s cognitive storage (cognitive knowledge graph for reasoning and review)
   - O: Ego’s inherent cognitive constraints, reasoning boundaries and evaluation criteria
   - F: Ego’s cognitive traits, reasoning preferences and optimization style
10. **【L‑Logic Symbol Layer】** Convert all internal thinking, reasoning logic and cognitive concepts inside Ego’s S/C/R/O/F/G into standardized symbols, terms and conventions (SurvX symbol system). This supports blueprint persistence, cross-entity communication and external output.
11. Design the runtime environment `[survx]field` hosting the whole system:
    - S: Structural components and resource composition of the environment
    - C: Data, resources, computing power and operational capabilities provided by the environment
    - R: Interaction channels and feedback mechanisms between the environment, entities and external world
    - O: Resource constraints and runtime boundaries of the environment itself
    - F: Inherent characteristics and dynamic variation patterns of the runtime environment

---

## Practical Supplementary Notes (Operational constraints only; no new paradigm concepts added)
1. The reasoning flow is an **analytical design thinking process**, not equivalent to program runtime sequence. Actual program runtime sequence is fully driven by state changes within `Energy`.
2. Subproblem recursive decomposition: Prioritize reusing existing components to avoid rebuilding Fields. Recursive modeling shall only be triggered when no available implementation exists to keep instances lightweight.
3. Matter blueprint is declarative structural description with no directly executable logic. Real executable logic is implemented by referenced base functional blocks of Feature.
4. Mandatory layering rule: Every layer must be filled with valid design content. Empty definitions or blank structures are prohibited. Blank layers indicate incomplete and non-production-ready entity design.
5. Stage isolation specification: Steps 1-7 form the **static business modeling stage** (output independently runnable Field). Steps 8-11 form the **self-evolution capability modeling stage** (endow the instance with iterative optimization capability).
