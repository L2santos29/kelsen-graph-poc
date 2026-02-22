# Kelsen-Graph PoC: Deterministic LegalTech Architecture

[![📄 Read the Official Whitepaper (PDF)](https://img.shields.io/badge/%F0%9F%93%84%20Read%20the%20Official%20Whitepaper%20(PDF)-Open-blue?style=for-the-badge)](docs/Whitepaper_KelsenGraph_LuisDosSantos.pdf)
[![CI](https://github.com/L2santos29/kelsen-graph-poc/actions/workflows/ci.yml/badge.svg)](https://github.com/L2santos29/kelsen-graph-poc/actions/workflows/ci.yml)

A Proof of Concept (PoC) demonstrating a neuro-symbolic architecture to reduce Large Language Model (LLM) hallucinations in LegalTech. The system forces probabilistic AI extraction through a deterministic Python logic graph for auditable, reproducible contract analysis.

## Architecture

This project is intentionally split into three layers:

- **The "Eyes" (Probabilistic Layer)**
	- `src/llm_extractor.py` performs NLP extraction from legal text using an LLM.
	- Prompting is strict and output is expected in a constrained JSON schema.

- **The "Customs" (Validation Layer)**
	- Pydantic validates extracted payloads before they enter the reasoning system.
	- Invalid or malformed fields are rejected early with explicit exceptions.

- **The "Brain" (Deterministic Layer)**
	- `src/logic_graph.py` evaluates legal rules in pure Python.
	- Final compliance decisions are deterministic, inspectable, and independent of AI randomness.

## Quick Start

```bash
git clone https://github.com/L2santos29/kelsen-graph-poc.git
cd kelsen-graph-poc

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Configuration & Security

1. Create your local configuration from the template:

	 ```bash
	 cp .env.example .env
	 ```

2. Choose one execution mode:
	 - **Live API mode:** set `LLM_API_KEY` and `LLM_API_URL` in `.env`.
	 - **Mock mode (recommended for evaluators):** set `LLM_MOCK_RESPONSE_JSON` with a valid JSON payload.

The mock mode is designed for zero-cost local execution: no external API key, no paid calls, and no network dependency.

## Testing Strategy

- Test framework: `pytest`
- Mocking approach: LLM calls are simulated through mock-based patching (`pytest-mock`, with `unittest.mock`-style patterns).
- Resilience checks cover malformed model output, simulated network timeouts, and extraction failures before deterministic evaluation.
- CI (`.github/workflows/ci.yml`) runs the suite without real API keys or external calls, keeping pipelines fast and reproducible.

Run tests locally:

```bash
pytest -q
```

## About & References

- Whitepaper (PDF): [Whitepaper_KelsenGraph_LuisDosSantos.pdf](docs/Whitepaper_KelsenGraph_LuisDosSantos.pdf)
- LinkedIn: [Author Profile (replace with your URL)](https://www.linkedin.com/in/your-profile)
