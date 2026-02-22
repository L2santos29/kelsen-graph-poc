"""LLM extraction module foundation for Kelsen-Graph PoC.

This module implements security and observability prerequisites before adding
provider-specific extraction logic.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import urllib.error
import urllib.request
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError

from .exceptions import JSONParseError, LLMExtractionError, LegalDataValidationError
from .models import ContractData

logger = logging.getLogger(__name__)

load_dotenv()


def get_llm_api_url() -> str:
	"""Load and validate the LLM API endpoint from environment variables.

	Returns:
		The target URL from `LLM_API_URL`.

	Raises:
		LLMExtractionError: If `LLM_API_URL` is missing or empty.
	"""
	api_url = os.getenv("LLM_API_URL")
	if not api_url:
		logger.critical(
			"Missing required environment variable: LLM_API_URL. "
			"Aborting before any LLM API request."
		)
		raise LLMExtractionError(
			"Missing required environment variable 'LLM_API_URL'."
		)
	return api_url


def _extract_text_from_provider_response(response_body: str) -> str:
	"""Extract the model textual output from common provider response formats.

	Args:
		response_body: Raw HTTP response body from the LLM provider.

	Returns:
		The textual model output expected to contain one JSON object.

	Raises:
		LLMExtractionError: If the provider response shape is unsupported.
	"""
	try:
		parsed_body: Any = json.loads(response_body)
	except json.JSONDecodeError as exc:
		logger.error("Provider response is not valid JSON: %s", exc)
		raise LLMExtractionError("Invalid JSON response envelope from LLM API.") from exc

	if isinstance(parsed_body, dict):
		output_text = parsed_body.get("output_text")
		if isinstance(output_text, str):
			return output_text

		content = parsed_body.get("content")
		if isinstance(content, str):
			return content

		choices = parsed_body.get("choices")
		if isinstance(choices, list) and choices:
			first_choice = choices[0]
			if isinstance(first_choice, dict):
				message = first_choice.get("message")
				if isinstance(message, dict):
					message_content = message.get("content")
					if isinstance(message_content, str):
						return message_content
				text = first_choice.get("text")
				if isinstance(text, str):
					return text

	logger.error("Unsupported LLM provider response format.")
	raise LLMExtractionError("Unsupported LLM provider response format.")


def _call_llm_api(system_prompt: str, user_prompt: str, api_key: str) -> str:
	"""Call external LLM API and return textual extraction output.

	Args:
		system_prompt: Strict system instruction with JSON schema.
		user_prompt: Contract text extraction request.
		api_key: Provider API key from environment.

	Returns:
		Raw model text that should contain exactly one JSON object.

	Raises:
		LLMExtractionError: If network/auth/provider errors occur.
	"""
	mock_response = os.getenv("LLM_MOCK_RESPONSE_JSON")
	if mock_response:
		logger.info("LLM mock response enabled via environment; skipping network call.")
		return mock_response

	api_url = get_llm_api_url()
	timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
	model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")

	request_payload = {
		"model": model_name,
		"temperature": 0,
		"messages": [
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		],
	}

	request = urllib.request.Request(
		url=api_url,
		data=json.dumps(request_payload).encode("utf-8"),
		headers={
			"Authorization": f"Bearer {api_key}",
			"Content-Type": "application/json",
		},
		method="POST",
	)

	logger.info("Sending request to LLM API endpoint.")
	try:
		with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
			response_body = response.read().decode("utf-8")
			return _extract_text_from_provider_response(response_body)
	except urllib.error.HTTPError as exc:
		if exc.code in (401, 403):
			logger.error("LLM API authentication/authorization failed (HTTP %s).", exc.code)
			raise LLMExtractionError("LLM API authentication failed.") from exc
		logger.error("LLM API returned HTTP error %s: %s", exc.code, exc.reason)
		raise LLMExtractionError("LLM API request failed with HTTP error.") from exc
	except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
		logger.error("LLM API network/timeout failure: %s", exc)
		raise LLMExtractionError("LLM API network or timeout failure.") from exc


def build_system_prompt() -> str:
	"""Build a strict system prompt that enforces JSON-only extraction output.

	Returns:
		A system instruction string with embedded JSON schema generated from
		`ContractData`.
	"""
	schema_json = json.dumps(
		ContractData.model_json_schema(),
		ensure_ascii=False,
		indent=2,
	)

	return (
		"You are a legal data extraction engine.\n"
		"Your only task is to extract structured fields from a contract text and "
		"return exactly one valid JSON object.\n"
		"Do not explain. Do not summarize. Do not add markdown. Do not wrap in "
		"code fences.\n"
		"Do not include keys that are not present in the schema.\n"
		"Use null when a nullable field cannot be determined with high confidence.\n"
		"If you are uncertain, prefer null over guessing.\n"
		"Output MUST strictly conform to this JSON Schema:\n"
		f"{schema_json}"
	)


def build_user_prompt(texto_contrato: str) -> str:
	"""Build the user prompt containing the raw contract text to extract.

	Args:
		texto_contrato: Plain-text legal contract input.

	Returns:
		Prompt payload for the model user message.
	"""
	return (
		"Extract the required fields from the following contract text. "
		"Return only one valid JSON object.\n\n"
		"--- CONTRACT START ---\n"
		f"{texto_contrato}\n"
		"--- CONTRACT END ---"
	)


def get_llm_api_key() -> str:
	"""Load and validate the LLM API key from environment variables.

	Returns:
		The non-empty API key string from `LLM_API_KEY`.

	Raises:
		LLMExtractionError: If `LLM_API_KEY` is missing or empty.
	"""
	logger.info("Validating LLM API configuration from environment variables.")
	api_key = os.getenv("LLM_API_KEY")

	if not api_key:
		logger.critical(
			"Missing required environment variable: LLM_API_KEY. "
			"Aborting before any LLM API request."
		)
		raise LLMExtractionError(
			"Missing required environment variable 'LLM_API_KEY'."
		)

	logger.info("LLM API configuration validated successfully.")
	return api_key


def extraer_datos_contrato(texto_contrato: str) -> ContractData:
	"""Extrae cláusulas contractuales desde texto plano usando un proveedor LLM.

	La función define la frontera tipada entre el módulo probabilístico de
	extracción y el resto de la arquitectura determinista. Su salida pública es
	únicamente un objeto `ContractData` validado.

	Args:
		texto_contrato: Contenido completo del contrato en texto plano que será
			analizado por el LLM.

	Returns:
		ContractData: Instancia validada del modelo Pydantic con las cláusulas
			extraídas y normalizadas.

	Raises:
		LLMExtractionError: Si falla la configuración, conexión o respuesta base
			del proveedor LLM.
		JSONParseError: Si la respuesta del LLM no puede interpretarse como JSON
			válido.
		LegalDataValidationError: Si el JSON parseado no cumple el esquema estricto
			de `ContractData`.
	"""
	logger.info("Starting contract extraction request to LLM provider.")
	api_key = get_llm_api_key()
	logger.info("Building strict system prompt with Pydantic JSON schema.")
	system_prompt = build_system_prompt()
	user_prompt = build_user_prompt(texto_contrato)
	logger.debug("System prompt prepared with schema length=%d.", len(system_prompt))
	logger.debug("User prompt prepared with contract length=%d.", len(user_prompt))

	# Layer 1: network/auth/provider failures are normalized as LLMExtractionError.
	raw_llm_output = _call_llm_api(
		system_prompt=system_prompt,
		user_prompt=user_prompt,
		api_key=api_key,
	)

	# Layer 2: parse output text into JSON payload.
	try:
		payload = json.loads(raw_llm_output)
	except json.JSONDecodeError as exc:
		logger.error("LLM returned non-JSON or mixed output: %s", exc)
		raise JSONParseError("LLM output is not valid JSON.") from exc

	if not isinstance(payload, dict):
		logger.error("LLM output JSON is not an object; received type=%s", type(payload).__name__)
		raise JSONParseError("LLM output JSON must be an object.")

	# Layer 3: validate against strict Pydantic model.
	try:
		return ContractData.model_validate_json(raw_llm_output)
	except ValidationError as exc:
		logger.error("Intercepted hallucination/invalid legal payload: %s", exc)
		raise LegalDataValidationError(
			"Extracted legal data failed strict schema validation."
		) from exc
