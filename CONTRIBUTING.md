# Contributing Guide

Thanks for your interest in improving Kelsen-Graph PoC.

This project follows a strict engineering protocol to preserve deterministic behavior, legal-audit traceability, and CI reliability.

## Contribution Workflow

1. Fork the repository and create a feature branch.
2. Keep changes focused, small, and clearly documented.
3. Open a Pull Request with:
   - A concise problem statement.
   - A summary of your technical approach.
   - Evidence that all required checks pass.

## Non-Negotiable Rules for Every Pull Request

All proposed changes **must** satisfy the three rules below:

1. **Typed with Pydantic and Mypy**
   - Data exchanged between layers must remain explicitly modeled and validated.
   - Type hints must be complete enough to pass static analysis.

2. **Code Quality Gate (`make lint`)**
   - Your PR must pass the linting/formatting gate.
   - This enforces a consistent, PEP 8-aligned codebase and avoids style regressions.

3. **Test Gate (`make test`)**
   - All unit tests must pass before review.
   - Changes that break deterministic behavior, extraction resilience, or CI reproducibility will be rejected.

## Local Validation Checklist

Run the following commands before opening your Pull Request:

```bash
make lint
make test
```

## Scope and Design Principles

- Keep the neuro-symbolic separation intact: extraction is probabilistic, legal reasoning is deterministic.
- Do not introduce hidden AI reasoning inside the deterministic graph.
- Prefer explicit errors and auditable outputs over implicit behavior.

Thanks for helping keep this project production-grade and collaboration-ready.