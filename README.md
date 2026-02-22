# Kelsen-Graph PoC: Deterministic LegalTech Architecture

[![📄 Read the Official Whitepaper (PDF)](https://img.shields.io/badge/%F0%9F%93%84%20Read%20the%20Official%20Whitepaper%20(PDF)-Open-blue?style=for-the-badge)](docs/Whitepaper_KelsenGraph_LuisDosSantos.pdf)
[![CI](https://github.com/L2santos29/kelsen-graph-poc/actions/workflows/ci.yml/badge.svg)](https://github.com/L2santos29/kelsen-graph-poc/actions/workflows/ci.yml)

## Instalación

- Crear y activar entorno virtual.
- Instalar dependencias con `pip install -r requirements.txt`.

## Configuración

- Crear `.env` desde `.env.example`.
- Para ejecución local real del extractor: definir `LLM_API_KEY` y `LLM_API_URL`.
- Para ejecución local sin red: usar `LLM_MOCK_RESPONSE_JSON` con un JSON válido.

## Uso

- Ejecutar orquestación completa: `python main.py`.
- Ejecutar tests: `pytest -q`.

## Arquitectura

- `src/llm_extractor.py`: frontera probabilística (prompt estricto + validación Pydantic).
- `src/logic_graph.py`: evaluación determinista por reglas y reporte formal.
- `tests/`: suite aislada con mocks para simular respuestas LLM.
- CI en GitHub Actions ejecuta tests sin API keys reales ni llamadas externas, por lo que el pipeline es rápido, reproducible y gratuito.
