"""Domain exception hierarchy for Kelsen-Graph PoC.

These exceptions provide explicit failure semantics at the boundary between the
LLM extractor and deterministic legal logic.
"""


class KelsenGraphError(Exception):
	"""Base class for all domain-specific errors in Kelsen-Graph.

	This root exception allows callers to catch all project-level failures while
	still enabling specific handling for each error subclass.
	"""


class LLMExtractionError(KelsenGraphError):
	"""Raised when extraction from the LLM provider fails.

	Typical causes include network errors, authentication problems, provider
	timeouts, and empty or malformed API responses.
	"""


class JSONParseError(KelsenGraphError):
	"""Raised when extractor output cannot be parsed as valid JSON.

	This error isolates failures where the LLM returns explanatory prose,
	markdown, or partially formatted payloads instead of strict JSON.
	"""


class LegalDataValidationError(KelsenGraphError):
	"""Raised when extracted legal data violates schema constraints.

	This error is used when parsed payloads do not satisfy Pydantic models,
	including invalid enums, missing required fields, or type mismatches.
	"""
