# Contributing to SurvX

Thank you for contributing to this project! 🎉

This document defines the conventions for Issues, PRs, code, and documentation contributions in this repository.

## Prerequisites

Before submitting any contribution, please read:

- [README.md](./README.md) — Core concepts and positioning of the project
- [Paradigm Design Document](./docs/paradigm-as-solution-framework.md) — Unified design, decomposition, and documentation conventions for this project

All code, module, and documentation changes **must conform to the SurvX paradigm system**.

## Contribution Types

You can participate in the project in the following ways:

1. Bug fixes (code, logic, copy errors)
2. Feature iteration, module extension
3. Documentation improvement, example completion, description optimization
4. Code refactoring, performance optimization, structural standardization
5. Issue discussion, requirement suggestions, problem feedback

## Issue Conventions (Questions / Feature Requests / Bug Reports)

1. Search existing Issues first to avoid duplicates
2. Bug reports must include: symptom, reproduction steps, expected result, runtime environment
3. Feature suggestions should explain: use case, problem solved, design approach
4. **For major structural changes, open an Issue for discussion first and confirm before development**

## PR Workflow (Code / Documentation Merging)

1. Fork this repository
2. Create a feature branch based on `main`
3. Submit a PR after local development and self-testing are complete
4. The PR description must clearly state: what problem this change solves, which Issue it corresponds to
5. Wait for maintainer review, revisions, and merge

### PR Hard Constraints

1. **All new modules must conform to the SurvX paradigm**
   - Business/fixed modules: follow the Field five-layer structure
   - Iterative/complex designs: follow the Ego seven-layer design process
2. Documentation changes must align with the repository's unified paradigm
3. Ensure code is runnable and contains no breaking changes
4. PRs for major architectural changes without prior discussion **will not be merged**

## Documentation Contribution Conventions

1. Formal project documentation is stored uniformly in `/docs`
2. All formal documents must include a paradigm declaration at the top:

```
Note: This document adopts the SurvX unified analysis and design paradigm. See docs/paradigm-as-solution-framework.md for details.
```

3. Essays, drafts, and personal reflections **are not committed to this repository**

## Branch Conventions

- `main`: stable trunk branch, always kept runnable and releasable
- All feature development uses temporary branches; direct push to `main` is prohibited

## Commit Conventions

Semantic commit format is used:

```
<type>(<scope>): <subject>
```

### type

- `feat`: new feature, module
- `fix`: bug fix
- `docs`: documentation change
- `refactor`: code refactoring, no external behavior change
- `perf`: performance optimization
- `test`: test-related
- `chore`: build, config, dependencies, and other miscellaneous items
- `scope` (optional): module name, e.g. `ego`, `field`, `docs`
- `subject`: brief description, no trailing period

### Examples

- `feat(ego): add goal decomposition workflow`
- `fix(field): correct relation resolve logic`
- `docs: update contributing.md`

> Principle: each commit should ideally make only one type of change; major changes may include a body describing the design rationale.
> This project does not enforce tool-based validation — compliance is on an honor system.

## Code of Conduct

- Keep discussions friendly, rational, and focused on technology and design
- Respect the project's existing architecture and paradigm design
- All contributions prioritize **serving the project's long-term stability and uniformity**

## Closing

This project follows the design philosophy of **minimalism, convergence, structure, and iterability**.

All contributions aim to make the entire paradigm more rigorous, more universal, and more practical.
