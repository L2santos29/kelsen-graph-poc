"""Tests for LLM extractor module with deterministic API mocking."""

from __future__ import annotations

import json

import pytest
from pytest_mock import MockerFixture

from src.exceptions import LLMExtractionError, LegalDataValidationError
from src.llm_extractor import _call_llm_api, extraer_datos_contrato
from src.models import ContractData, ContractType, Jurisdiction


def _build_valid_raw_json() -> str:
	"""Return a valid JSON payload aligned with ContractData schema."""
	return json.dumps(
		{
			"contract_type": "NDA",
			"governing_jurisdiction": "DELAWARE",
			"effective_date": "2026-03-01",
			"explicit_expiration_date": None,
			"auto_renewal": True,
			"non_renewal_notice_days": 15,
			"has_arbitration_clause": False,
			"liability_cap_amount": 500000.0,
			"indemnification_uncapped": False,
			"confidentiality_survival_years": 3,
			"trade_secret_survival_years": 5,
		}
	)


def test_extraer_datos_contrato_happy_path_returns_contractdata(mocker: MockerFixture) -> None:
	"""Debe convertir una respuesta JSON perfecta en un modelo Pydantic válido."""
	mocker.patch("src.llm_extractor.get_llm_api_key", return_value="test-api-key")
	mocker.patch("src.llm_extractor._call_llm_api", return_value=_build_valid_raw_json())

	result = extraer_datos_contrato("Contrato de prueba")

	assert isinstance(result, ContractData)
	assert result.contract_type == ContractType.NDA
	assert result.governing_jurisdiction == Jurisdiction.DELAWARE


def test_extraer_datos_contrato_hallucinated_enum_raises_validation_error(
	mocker: MockerFixture,
) -> None:
	"""Debe interceptar jurisdicciones inválidas y elevar LegalDataValidationError."""
	payload = json.loads(_build_valid_raw_json())
	payload["governing_jurisdiction"] = "MARTE"

	mocker.patch("src.llm_extractor.get_llm_api_key", return_value="test-api-key")
	mocker.patch("src.llm_extractor._call_llm_api", return_value=json.dumps(payload))

	with pytest.raises(LegalDataValidationError):
		extraer_datos_contrato("Contrato de prueba")


def test_call_llm_api_timeout_raises_llm_extraction_error(
	mocker: MockerFixture,
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Debe convertir un timeout de red en LLMExtractionError de dominio."""
	monkeypatch.delenv("LLM_MOCK_RESPONSE_JSON", raising=False)
	monkeypatch.setenv("LLM_API_URL", "https://example.test/v1/chat/completions")
	monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "1")

	mocker.patch(
		"src.llm_extractor.urllib.request.urlopen",
		side_effect=TimeoutError("simulated timeout"),
	)

	with pytest.raises(LLMExtractionError):
		_call_llm_api(
			system_prompt="system",
			user_prompt="user",
			api_key="test-api-key",
		)
