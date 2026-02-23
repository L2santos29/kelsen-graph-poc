"""LLM extraction module foundation for Kelsen-Graph PoC.

This module implements security and observability prerequisites before adding
provider-specific extraction logic.
"""

from __future__ import annotations

import json
import logging
import socket
import urllib.error
import urllib.request
from typing import Any

from pydantic import ValidationError

from .exceptions import JSONParseError, LLMExtractionError, LegalDataValidationError
from .models import ContractData

logger = logging.getLogger(__name__)


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


def _call_llm_api(
	system_prompt: str,
	user_prompt: str,
	api_key: str,
	*,
	api_url: str | None,
	model_name: str,
	timeout_seconds: float,
	mock_mode: bool,
	mock_response_json: str | None,
) -> str:
	"""Call external LLM API and return textual extraction output.

	Args:
		system_prompt: Strict system instruction with JSON schema.
		user_prompt: Contract text extraction request.
		api_key: Provider API key from environment.
		api_url: Provider API endpoint.
		model_name: Provider model identifier.
		timeout_seconds: Request timeout in seconds.
		mock_mode: Enables network-free mocked LLM output.
		mock_response_json: Mock JSON payload when mock mode is enabled.

	Returns:
		Raw model text that should contain exactly one JSON object.

	Raises:
		LLMExtractionError: If network/auth/provider errors occur.
	"""
	if mock_mode:
		if not mock_response_json:
			raise LLMExtractionError(
				"Mock mode is enabled but no mock response payload was provided."
			)
		logger.info("LLM mock response enabled via environment; skipping network call.")
		return mock_response_json

	if not api_url:
		raise LLMExtractionError("Missing LLM API URL for non-mock execution.")

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


def build_user_prompt(contract_text: str) -> str:
	"""Build the user prompt containing the raw contract text to extract.

	Args:
		contract_text: Plain-text legal contract input.

	Returns:
		Prompt payload for the model user message.
	"""
	return (
		"Extract the required fields from the following contract text. "
		"Return only one valid JSON object.\n\n"
		"--- CONTRACT START ---\n"
		f"{contract_text}\n"
		"--- CONTRACT END ---"
	)


def extract_contract_data(
	contract_text: str,
	*,
	api_key: str,
	api_url: str | None,
	model_name: str,
	timeout_seconds: float,
	mock_mode: bool,
	mock_response_json: str | None,
) -> ContractData:
	"""Extract contract clauses from plain text using an LLM provider.

	This function defines the typed boundary between probabilistic extraction and
	the deterministic legal logic layer. Its public output is always a validated
	`ContractData` object.

	Args:
		contract_text: Full plain-text contract content to analyze.
		api_key: API key validated by the centralized settings layer.
		api_url: LLM provider endpoint for online execution.
		model_name: LLM model identifier to invoke.
		timeout_seconds: Maximum timeout per network call.
		mock_mode: Enables local simulation mode with no internet dependency.
		mock_response_json: Mock JSON payload used when mock mode is enabled.

	Returns:
		ContractData: Validated Pydantic model instance with normalized clauses.

	Raises:
		LLMExtractionError: If provider config/network/base response fails.
		JSONParseError: If the LLM response cannot be parsed as valid JSON.
		LegalDataValidationError: If parsed JSON fails strict `ContractData` schema.
	"""
	logger.info("Starting contract extraction request to LLM provider.")
	logger.info("Building strict system prompt with Pydantic JSON schema.")
	system_prompt = build_system_prompt()
	user_prompt = build_user_prompt(contract_text)
	logger.debug("System prompt prepared with schema length=%d.", len(system_prompt))
	logger.debug("User prompt prepared with contract length=%d.", len(user_prompt))

	# Layer 1: network/auth/provider failures are normalized as LLMExtractionError.
	raw_llm_output = _call_llm_api(
		system_prompt=system_prompt,
		user_prompt=user_prompt,
		api_key=api_key,
		api_url=api_url,
		model_name=model_name,
		timeout_seconds=timeout_seconds,
		mock_mode=mock_mode,
		mock_response_json=mock_response_json,
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
