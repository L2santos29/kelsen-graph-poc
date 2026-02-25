# Kelsen-Graph PoC — Neuro-Symbolic Contract Intelligence

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/L2santos29/kelsen-graph-poc/actions/workflows/ci.yml/badge.svg)](https://github.com/L2santos29/kelsen-graph-poc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Project Status](https://img.shields.io/badge/Status-Production--Style%20PoC-0A7E3B)](#)
[![Paradigm](https://img.shields.io/badge/Paradigm-Neuro--Symbolic-6A1B9A)](#)

[![📄 Read the Official Whitepaper (PDF)](https://img.shields.io/badge/%F0%9F%93%84%20Read%20the%20Official%20Whitepaper%20(PDF)-Open-blue?style=for-the-badge)](docs/Whitepaper_KelsenGraph_LuisDosSantos.pdf)

Kelsen-Graph is a LegalTech Proof of Concept designed to reduce LLM hallucination risk in contract analysis by separating probabilistic extraction from deterministic legal reasoning.

---

## 1) Problem vs. Solution

### The Problem: Black-Box LLM Risk in Legal Workflows

Pure LLM pipelines are probabilistic. In legal and compliance contexts, probabilistic behavior can produce inconsistent clause interpretation, fabricated exceptions, or malformed outputs that create financial and regulatory exposure.

### The Solution: Neuro-Symbolic Decoupling

Kelsen-Graph enforces a strict architecture:

- **Eyes (LLM Extractor):** The LLM only extracts structured facts.
- **Customs (Pydantic Validation):** Every extracted field is type-checked and schema-validated.
- **Brain (Deterministic Logic Graph):** Pure Python rules issue auditable verdicts.

Result: no hidden reasoning, no silent coercions, and traceable policy decisions.

---

## 2) Zero-Setup Executive Demo

No Python setup, no API key, no paid calls required.

```bash
git clone https://github.com/L2santos29/kelsen-graph-poc.git
cd kelsen-graph-poc
bash run_demo.sh
```

**For Windows (PowerShell):**

```powershell
git clone https://github.com/L2santos29/kelsen-graph-poc.git
cd kelsen-graph-poc
python -m venv .venv ; .venv\Scripts\activate ; pip install -q -r requirements.txt ; python demo.py --mock
```

What the launcher does automatically:

1. Verifies `python3` is installed.
2. Creates/activates `.venv`.
3. Installs dependencies silently.
4. Runs `demo.py --mock`.
5. Shows a staged 4-act terminal narrative ending in a legal verdict.

Example output (abridged):

```text
[ACT 1/4] Reading legal document...
[ACT 2/4] The 'Eyes' (Neuro-Symbolic Extraction)
[ACT 3/4] The 'Brain' (Deterministic Logic Graph)
[ACT 4/4] Final Verdict
🟢 APPROVED
```

---

## 3) Engineering Standards (CTO View)

This PoC is built with production-style software discipline:

- **Strict Data Contracts:** Pydantic models for extraction and evaluation outputs.
- **Deterministic Rule Engine:** Isolated policy rules in `src/logic_graph.py`.
- **Structured Error Taxonomy:** Domain exceptions for extraction, parsing, and validation failures.
- **Static Quality Gates:** Ruff + Mypy enforced locally and in CI.
- **Automated Testing:** Pytest + mock strategy for fast, offline, reproducible checks.
- **Developer Orchestration:** `Makefile` for `lint`, `test`, `format`, and `demo`.
- **CI/CD Quality Gate:** GitHub Actions blocks low-quality merges before tests even run.

Core commands:

```bash
make lint
make test
make demo
```

---

## 4) Data-Driven Scenario Suite

The `data/` directory includes explicit legal test scenarios:

- `contract_01_standard_approval.txt` → safe, policy-aligned baseline.
- `contract_02_high_risk_rejection.txt` → hidden financial red-flag profile.
- `contract_03_government_exception.txt` → conditional government exception path.

This allows the same architecture to demonstrate approval, rejection, and exception handling under controlled conditions.

---

## 5) Author

Built by a **Legal Engineer** focused on bridging strict legal doctrine and auditable software execution.

Contributions are welcome from engineers aligned with deterministic LegalTech standards. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a Pull Request.

- LinkedIn: [Luis Daniel Dos Santos](https://www.linkedin.com/in/luis-legal-engineer/)
If you are evaluating this project for hiring, partnership, or product incubation, start with the whitepaper and then run the zero-setup demo.
