# Solutions

solutions holds the official landing projects of the SurvX paradigm.
It targets real industry data and long-term research ！ the layer where the paradigm moves from "demonstrable" to "deliverable."

Difference from examples: examples are demos that showcase paradigm features and don't pursue robustness;
solutions are official projects ！ long-term maintained, real data, deliverable.

## Projects

### FinancialMarkets
Uses the SurvX paradigm to portray markets. No business drive; the focus is on modeling and portrayal itself.
The goal is to express market structure, participants, constraints, and state changes through Matter and Energy,
rather than to trade or make decisions. It is the project closest to "pure paradigm expression" among the four.

### Humans
An intelligent simulation solution. It has evolution and drive.
It targets multi-agent simulation scenarios: multiple entities coexist, perceive, and interact within an environment,
and evolve their own structure and behavior over time. Compared with AITown in examples,
Humans is a more complete, longer-term research vehicle, not just a demo.

### MoLin
A data-driven solution for industries or companies, oriented toward decision-making. For example, quantitative private funds; business-driven.
It starts from real data and provides decision support for a specific industry or company.
The difference from FinancialMarkets: FinancialMarkets portrays markets,
while MoLin uses data to drive decisions, with clear business goals.

### SurvX
The landing solution of the SurvX paradigm. Building SurvX with SurvX ！ self-referential validation.
It is both a solution and the paradigm's own touchstone:
if the paradigm is sufficiently self-consistent, it should be able to describe, run, and evolve the paradigm itself.

## Relationship of the Four

| Project | Nature | Drive | Goal |
|---------|--------|-------|------|
| FinancialMarkets | Portrayal | No business drive | Express markets |
| Humans | Simulation | Evolution + drive | Multi-agent simulation |
| MoLin | Decision | Data + business drive | Industry/company decisions |
| SurvX | Self-reference | The paradigm itself | Paradigm landing validation |

Four forms: portrayal, simulation, decision, self-reference.

## Boundaries

- `solutions/`: official projects ！ long-term research, real data, deliverable.
- `examples/`: demos ！ only showcase paradigm features, not for production delivery.
- `tools/`: general engineering tools, no business logic.
- `survx/`: paradigm kernel, no concrete solutions.

## Naming

Directories: snake_case `_`. Blueprint fields: kebab-case `-`.