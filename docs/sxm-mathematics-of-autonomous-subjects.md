# SXM: Mathematics of Autonomous Subjects

This document does not yet develop specific formulas. Its primary task is to pose the research question, delineate boundaries, establish method, and provide a validation scheme. Formulas belong to subsequent work; the current goal is to fully establish the problem space.

## 1. The Research Question

Phenomena such as self-awareness, individual behavior, and collective effects have long been studied, yet a unified mathematical tool for them has never emerged.

Ideas about "how a subject behaves, how it cognizes, how it evolves" are scattered across psychology, behavioral science, game theory, cybernetics, and complex systems, but no unified and operational core has formed.

The goal of this document is to establish a researchable mathematical problem space for such phenomena.

## 2. Method

A functionalist approach is adopted, setting aside ontological discussion.

Only this methodology is followed: start from function, examine what the object "does," rather than asking "what it essentially is."

The mystery surrounding consciousness arises largely not from its internal mechanism, but from its mode of access: it can only be perceived from within, in the first person; it cannot be directly shared or publicly verified, yet it can be communicated. Therefore, approaching it from function and behavior is the only publicly verifiable path.

This methodology governs all subsequent trade-offs: anything that cannot be functionally verified is excluded from the framework.

## 3. Theoretical Core

A set of core variables + two roles + a feedback loop.

Core variables are a set of variables that include internal states.

The same set of core variables simultaneously plays two roles:

1. Maintained objects: subject to survival constraints; once they fall below a danger zone, the subject fails;
2. Behavioral drivers: when these variables have deficits, they drive the subject to produce behavior.

Survival (maintaining one's own existence) and drive (generating goals and demands) are not two independent things, but two functions of the same set of core variables.

Deficit → drives behavior; falling below the threshold → survival fails.

The feedback loop has two branches:

Inward: reading one's own state
Outward: changing the external environment

The two form a closed loop; subject behavior is the result of this loop's continuous solving.

Thus the minimal core can be summarized as:

A set of core variables + the dual role of maintenance/drive + a feedback loop.

## 4. System Properties

The system described here is a coupled nonlinear system with feedback, dynamically variable goal weights, coexisting multiple objectives, and time-varying constraints.

From this it follows:

- In most scenarios, no concise analytical solution exists;
- In stable environments, feasible solutions and approximate optimal solutions can be found;
- Real environments are open and dynamic; no global optimum exists, only continuously adaptive feasible solutions.

Therefore this mathematical framework does not pursue the "optimal," but the "feasible."

It does not describe "how to solve an optimization problem," but "how a subject continuously adapts and maintains survival in an open environment."

## 5. Cognitive Mechanism

Individual cognition is not equivalent to the real environment.

The environment is unknown to the individual; the individual possesses its own internal cognition.

The "optimum" an individual solves for is optimal relative to its own cognition, not the global optimum of the real environment.

The deviation between cognition and environment drives continuous cognitive updating.

Two modes can be distinguished, exploitation and exploration:

- Not actively updating cognition: an approximate optimal solution is obtained under existing cognition;
- Active cognitive exploration: "reducing cognitive deviation" is incorporated into the goal set, adding an exploratory goal, at which point the global optimum no longer holds.

This means that within this mathematical framework, the "optimum" is an unstable concept, changing with cognition and exploratory behavior. What can be solved for is only the feasible solution under current cognition.

## 6. Validation Scheme

This framework is an experimental system, not purely deductive speculation.

Validation method: backtesting, similar in spirit to quantitative investing, placing the subject into an environment for simulated runs.

Performance evaluation includes both long-term and short-term dimensions.

The core observable metric: the survival curve, characterizing the subject's survival performance along the time axis.

Extendable research directions:

- How to enable an individual to grow better and more purposefully;
- Environment design (education, governance, opinion guidance, etc.);
- Deriving collective behavior from individual evolution.

The validation method constrains the framework's form:

The model must support simulation and backtesting;
Variables must be observable and computable;
Otherwise the survival curve cannot be drawn.

## 7. Research Boundaries

The research object must simultaneously satisfy:

Continuously maintaining a set of core internal variables;
Being situated in a multi-constraint environment;
Having multiple mutually conflicting goals;
Possessing inward perception and outward action, forming a closed feedback loop;
Behavior being the result of this system's continuous dynamic solving.

System boundaries:

The framework defines only the behavioral and cognitive growth rules of a single autonomous individual; populations and generational evolution are extension directions, not the starting point.

It is a purely mathematical rule system, bound to no biological, machine, or simulation substrate, capable of generally describing all autonomous systems.

It offers no ontological conclusions, upholding only the functionalist methodology.

## 8. Positioning of the Program

This document does not provide final answers, but constructs a problem space:

Defining which problems are worth studying, what method to adopt, how to judge research success, and what lies outside the research scope.

Whether the system ultimately proves simple or complex is left to subsequent research; the current goal is to make the research problem of autonomous subjects researchable, verifiable, and advanceable.

## 9. Mathematical Form

### 9.1 The Subject

The subject evolves within an environment; its structure, self-cognition, and mechanism change over time.

The subject consists of the following elements:

- Structure M: the subject's organizational form;
- Self-cognition E: the subject's internal model of itself and the environment;
- Mechanism Φ: the relations and functions within the subject (i.e., the abstraction of Q);
- Core variables C: a set of variables that are maintained and simultaneously drive behavior.

The update rule for the subject's structure over time is:

M_{t+1} = F( M_t , E_t , Φ_t ; C_t )

The update rule for self-cognition over time is:

E_{t+1} = G( E_t , M_t ; C_t )

where F and G are update rules, and C_t is the value of the core variables at time t.

The environment V is the background of the subject's evolution, not an independent term parallel to the subject, but a condition appearing in the above updates.

The environment itself changes over time:

V_{t+1} = H( V_t , M_t , E_t )

### 9.2 External Standard

The external standard is given by the researcher, acting on the subject's developmental trajectory and outputting a degree of match:

S : {M_t} → degree of match

It falls into two categories:

- Finite goal: S({M_t}) = distance(M_T, S)
- Infinite goal: S({M_t}) = accumulated match of the rate of change of M_t over time

### 9.3 The Top-Level Problem

Given an external standard S, find the configuration that maximizes the match between the subject's trajectory {M_t} and S:

max Match( {M_t}, S )

Constraints:

- Self-consistency constraint: all behavior must be self-consistent within self-cognition E;
- Survival constraint: those variables in core variables C that serve as maintained objects must not fall below the danger zone.

### 9.4 The Position of Core Variables

Core variables C are the pivot of the subject:

- As maintained objects, they enter the survival constraint;
- As behavioral drivers, they enter the update rules F and G;
- Their deficits drive behavior, and their thresholds determine failure.

Mechanism Φ is not listed separately; it is embedded in F and G, manifesting as functional relations.