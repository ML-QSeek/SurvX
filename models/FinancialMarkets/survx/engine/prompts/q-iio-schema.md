# Q-IIO-schema
**Document Purpose**: Prompt schema for Q-function design phase, for human-AI collaboration. Defines mandatory description items for complex Q design. Distinct from `syntax_zh.md` (syntax validity rules) and the actual Q file (implementation).
**Scope**: Simple Q only requires `# prompt:` `# reason:` comments; complex Q must use this full schema.
**Constraints**: Governed by Part 4 Coding Principles in `syntax_zh.md`.
---
## I. Lang
> Target language: Implementation language of the function.
- **Language**: Python / Rust / HTML / JavaScript, etc.
- **Version**: Language version
- **Style / Spec**: Follow Part 4 Coding Principles in `syntax_zh.md`. Extra conventions are supplemented here.

## II. I - Import
> What is input: What the function receives, dependencies, preconditions.
- **Data Type (Structural State)**: Define input data structure, field specs, nested format, unified outer data envelope.
- **Numeric Range (Value State)**: Define input boundaries, thresholds, valid value domain for basic data validation.
- **Status Flag (Logical State)**: Define preconditions and state requirements for input.
- **Time & Frequency (Temporal State)**: Define call rhythm, rate limits, timeout rules for input.
- **Environment Interaction (Environmental State)**: Track input source, external dependencies, environment context.
- **Metadata (Descriptive State)**: Carry input remarks, version info, owning entity and other extra descriptive information.

## III. I - Internals
> Internal mechanism: How the function operates, underlying principles and constraints.
- **Core Mechanism**:
- **Algorithm / Strategy**:
- **Constraints**:
- **Prohibited Items**:
- **Performance / Complexity Requirement**:

## IV. O - Output
> What is output: Return values, format, side effects and error handling.
- **Data Type (Structural State)**: Define output data structure, field specs, nested format, unified return envelope.
- **Numeric Range (Value State)**: Define output boundaries, thresholds, valid value domain for basic data validation.
- **Status Flag (Logical State)**: Business tags for success, failure, interruption, pending and other execution results.
- **Time & Frequency (Temporal State)**: Define output rhythm, validity period, timeout rules.
- **Environment Interaction (Environmental State)**: Track output destination, side effects, external dependencies, environment context.
- **Metadata (Descriptive State)**: Carry output remarks, version info, creation time, owning entity and other extra descriptive information.

## V. Examples
(To be added upon business cases)
