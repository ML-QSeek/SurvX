# Alternative Natural‑Language Interaction: White‑Box Translation under the SurvX Paradigm
Technical Note｜Mechanism self‑consistency argument only. Engineering performance and scale are out‑of‑scope; no large‑model dependency is introduced. Implementation challenges such as compression and ambiguity resolution are deferred to prototype phase.

## Background: Two Existing Natural‑Language Interaction Paradigms
Two major approaches dominate current natural‑language interaction research.

**Large‑model dialogue paradigm**: Natural text serves as input and output. Knowledge is embedded within model parameters, and replies are generated probabilistically. The processes of interaction and understanding reside inside a black box; intermediate steps cannot be explicitly traced.

**World‑model paradigm**: An environment simulator is constructed to predict the next‑step state given current states and actions. This approach achieves internal structuring and executable deduction. Nevertheless, it models state‑transition processes only. Language acts merely as an input‑output carrier and is not itself an object of modeling.

This note discusses a third feasible mechanism: **white‑box blueprint‑translation interaction**.
Language is not complete knowledge in itself. Instead, it is a lossy‑compressed signal derived from an agent’s internal executable blueprint. Language propagates via the environment to the receiving agent. The receiver performs parsing, completion and deduction relying on its own cognitive network to achieve understanding. Where information gaps exist, multi‑round inquiries converge toward sufficient information.

Understanding is a local process occurring on the receiver’s side. Information bias originates from three phases: **compression, propagation, and completion**. Every step within this cognitive loop is explicitly observable: entity nodes referenced by words, propagation paths of state changes, positions of information gaps, and exact links where bias emerges can all be located — hence the term “white‑box” mechanism.

## Full Mechanism Loop: Compression ‑ Propagation ‑ Parsing & Completion ‑ Deduction & Understanding
**Compression**: The sender compresses its internal executable blueprint into natural‑language text. Numeric values are mapped onto rhetorical descriptions; key causal chains are extracted and organized chronologically or causally into textual form. Compression is lossy; information loss is determined by compression rules.

**Propagation**: Linguistic messages are relayed through the environment entity for cross‑agent communication. Direct agent‑to‑agent communication is prohibited; internal states remain isolated. All messages pass through environmental channels, and the full communication history is traceable. Propagation may introduce bias caused by channel observation granularity and forwarding rules.

**Parsing & Completion**: The receiver performs token‑level parsing over incoming language, retrieves matching entity nodes inside its symbol layer, and assembles a preliminary partial blueprint. Missing nodes or broken links are marked as information gaps. The receiver initiates inquiries toward the sender, converging information via multi‑round interaction. Completion draws entirely upon the receiver’s private local cognitive network rather than copying the sender’s original blueprint.

**Deduction & Understanding**: Based on the parsed preliminary blueprint, the receiver invokes its relation and cognitive networks to execute state deduction. Understanding is accomplished **only when the deduction chain runs through completely**. Merely receiving text or parsing a static blueprint does not constitute understanding. Understanding is a private process of the receiver, and full deduction paths remain traceable.

These four phases constitute a complete cross‑agent cognitive loop. Compression rules, transmission channels, symbol matching points, and deduction chains are all inspectable.

## Positioning and Distinctions
### Differences from Traditional Symbolic Paradigms
Symbolic AI, semantic networks, and knowledge graphs share the core premise: structures behind language can be explicitly represented. They are constrained by three practical limitations: combinatorial explosion caused by exhaustive rule‑sets, high manual‑encoding maintenance costs, and proficiency in factual queries but poor support for state evolution.

Knowledge graphs excel at “being queried”, yet struggle at “being executed”. In dialogues, facts can be retrieved, but query results cannot be transformed into subsequent state transitions — producing the well‑known phenomenon: *“queryable but not runnable”*.

The present mechanism fills the “runnable” gap by building upon the SurvX paradigm. Static structures are explicitly described, and those same structures can be executed by the engine to enable transitions from facts to state changes.

### Positioning versus the Two Preceding Paradigms
- Against large‑model systems: Large models output text with black‑box internals. This mechanism outputs complete blueprints, propagation chains and constraint sets; every step is traceable — this is white‑box translation.
- Against world‑model systems: World models simulate transitions of the external objective environment. This mechanism simulates internal agent cognition: how concepts associate, how changes propagate, and how constraints take effect. All processes are inspectable and interpretable.

Methodologically, this forms an independent path alongside the other two (it does not replace them). It pursues verifiable understanding, runnable reasoning, and interpretable agent‑to‑agent interaction.

## Internal Self‑Consistency within the SurvX Paradigm
Feasibility originates from self‑consistency of SurvX’s declarative model and requires no external components. A runnable blueprint is assembled from four categories of declarations:

**Structure declaration**: Entities are described via layered blueprints. Components, capabilities, external relations and constraint boundaries are stored in flattened form. Every node can be mapped onto symbol‑layer linguistic representations.

**Change declaration**: State‑evolution rules reside within the data layer and are evaluated per timestep. Business evolution logic is not hard‑coded inside the engine kernel.

**Relation declaration**: Mutual influences between entities are defined within relation tables. State changes propagate through relation tables instead of hard‑coded invocation chains.

**Ordinance / Constraint declaration**: Runtime thresholds and behavioural constraints live inside constraint tables. Interception and validation occur during deduction execution rather than as post‑hoc checks after execution completes.

The four declaration categories form a closed loop: data changes trigger state propagation, propagation passes constraint validation, and constraint outcomes are written‑back into states. The next timestep starts from the updated state. Cross‑agent messages always transit through the environment, enforcing observation‑domain boundaries and full communication traceability.

> Meaning of “blueprint‑is‑runnable”: One unified set of declarations describes both **what the system is** and **how the system will evolve**. Given an input change, the engine derives successive states following relation tables, with constraints permitting or blocking transitions — reasoning capability emerges from this process.

## Corresponding Formal Problems and Falsifiability
Each stage of the cognitive loop maps onto established information‑theoretic and probabilistic models, granting the mechanism falsifiable theoretical foundations:

- **Compression loss**: Compressing high‑dimensional blueprints down to low‑dimensional language relates to rate‑distortion theory and the information‑bottleneck principle. The core trade‑off lies between compression ratio and information distortion.
- **Transmission distortion**: Linguistic messages passing through environmental channels correspond to channel‑capacity and transmission‑distortion metrics.
- **Completion accuracy**: The receiver treats its cognitive network as prior knowledge and incoming language as observational evidence, performing maximum‑a‑posteriori inference. Completion quality depends on mutual information (shared knowledge) between two agents’ cognitive networks.
- **Bias measurement**: Besides aggregate distribution divergence (KL‑divergence), white‑box explicit structure enables bias localisation down to individual entity nodes, relational links and constraint rules.
- **Experimental verifiability**: Controlled experiments can be designed: vary shared‑knowledge levels between agents and observe bias shifts; measure blueprint‑language mapping success rates; plot compression‑ratio versus distortion curves. All sub‑propositions are testable.

A structural advantage of the paradigm: **research object and verification tool are the same SurvX multi‑agent instance**.
Construct a SurvX instance containing multiple independent agents plus an environment. The instance itself simulates agent cognitive interaction; linguistic transmission bias is one special case of such interaction. No separate test‑harness is required to observe the full cognitive loop.

## Capabilities If the Minimal Logical Loop Holds
Should the minimal logical loop be validated, the mechanism delivers these capabilities:
- **Verifiable understanding**: When the system reports “understanding achieved”, it can furnish blueprints and full deduction chains as objective evidence instead of vague conclusions.
- **Runnable reasoning**: Given one state change, deduce subsequent state evolutions following the relation‑constraint closed loop.
- **Interpretable interaction**: Humans and systems interact grounded on shared explicit symbolic blueprints.
- **Quantifiable bias**: Information loss caused by linguistic interaction yields both aggregate metrics and localised reports pointing to distorted nodes and links.

## Summary
This document provides mechanism‑level argumentation: structures behind language can be explicitly represented, and those representations can be executed for deduction. Within the unified declarative SurvX system these three elements form a closed loop.
At present only logical self‑consistency is demonstrated. Follow‑up work targets implementing a minimal running‑instance loop, advancing from mechanism‑level argument to runtime empirical evidence.

> Note: Concrete implementation topics including compression algorithms, ambiguity resolution and questioning strategies lie outside the scope of this mechanism argument.
