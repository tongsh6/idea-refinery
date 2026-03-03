# IdeaRefinery Constitution

## Core Principles

### I. Schema-Driven Artifacts (NON-NEGOTIABLE)

All output artifacts (PRD, TECH_SPEC, EXEC_PLAN) MUST be structured JSON first, then exported to Markdown. Pydantic v2 models are the single source of truth for artifact structure. No free-form or ad-hoc document formats.

### II. CR Closed-Loop (NON-NEGOTIABLE)

Every review round MUST produce structured CR (problem/rationale/change/acceptance/severity). Every edit round MUST resolve all CRs: ACCEPT/REJECT/DEFER with rationale. Blocking CRs MUST be closed before Gate pass. All CR state changes MUST be persisted and replayable.

### III. Gate as Quality Guard

Gate rules enforce objective quality thresholds:
- Missing sections → FAIL
- Unresolved Blocking CRs → FAIL
- avgScore ≥ 8 and Blocking = 0 → PASS
- Convergence or budget exhaustion → STOP

Gate decisions are deterministic and reproducible from config + evaluator results.

### IV. Test-First Development

- `pytest` must pass before any release
- `python -m build` must succeed before any release
- New features require test coverage
- No type suppression (`as any`, `@ts-ignore`, `@ts-expect-error`)

### V. Provider Agnosticism

IdeaRefinery supports multiple LLM providers (OpenAI-compatible, Ollama, Gemini, Claude). Code must not hard-bind to any single provider. Provider failures must trigger retry + fallback, never crash.

### VI. Simplicity & YAGNI

- Not a full-featured RAG platform — only retrieval interface + reference slots
- Not IDE-bound — Copilot as optional plugin only
- Start with minimal viable approach; extend only when needed
- Prefer existing libraries over new dependencies

## Technology Constraints

- **Language**: Python 3.11+ (currently 3.12)
- **Type System**: Pydantic v2 for all data models; strict typing
- **Orchestration**: LangGraph state machine (Draft → Review → Edit → Gate)
- **Storage**: SQLite for OSS persistence
- **CLI**: Click + Rich for terminal interface
- **Templates**: Jinja2 for prompt templates
- **Export**: Markdown (OSS default), extensible to PDF

## Development Workflow

- **Git Flow**: `main → feature` development; `features → release → main` publishing
- **Pre-release gates**: `pytest` + `python -m build`
- **No direct push to main**
- **AIEF process**: Proposal → Design → Implement → Review (see `workflow/INDEX.md`)
- **Spec-Driven Development**: Use spec-kit `/speckit.*` commands for structured feature development
- **Experience capture**: Record lessons learned for significant changes (see `context/experience/`)

## Governance

This constitution supersedes ad-hoc decisions. Amendments require:
1. Documented rationale
2. Team review
3. Version bump

All code changes must verify compliance with these principles.

**Version**: 1.0.0 | **Ratified**: 2026-03-02 | **Last Amended**: 2026-03-02
