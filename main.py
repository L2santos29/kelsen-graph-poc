"""Application entry point for Kelsen-Graph PoC orchestration flow."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.exceptions import JSONParseError, LLMExtractionError, LegalDataValidationError
from src.llm_extractor import extraer_datos_contrato
from src.logic_graph import ContractEvaluator

logger = logging.getLogger(__name__)


class ContractFileError(Exception):
    """Raised when the input contract file cannot be loaded."""


def run_pipeline() -> int:
    """Run the end-to-end orchestration pipeline.

    Flow:
        1) Load environment variables safely.
        2) Validate required API credentials.
        3) Read raw contract text from disk.
        4) Extract structured data with the LLM module.
        5) Evaluate deterministic legal rules.
        6) Log and emit a controlled verdict summary.

    Returns:
        Process exit code. `0` for success, non-zero for controlled failure.

    Raises:
        ContractFileError: If the contract file cannot be read.
        LLMExtractionError: If extraction provider or API config fails.
        JSONParseError: If LLM output is not valid JSON.
        LegalDataValidationError: If extracted payload violates Pydantic schema.
    """
    load_dotenv()

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise LLMExtractionError(
            "Missing required environment variable 'LLM_API_KEY'. "
            "Create/update .env before running the pipeline."
        )

    contract_path = Path("data") / "dummy_contract.txt"
    try:
        contract_text = contract_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractFileError(
            f"Could not read contract input file at {contract_path}."
        ) from exc

    logger.info("Input contract loaded from %s", contract_path)

    extracted_data = extraer_datos_contrato(contract_text)
    evaluator = ContractEvaluator()
    report = evaluator.evaluate(extracted_data)

    logger.info(
        "Pipeline finished | is_approved=%s | flags_rojas=%d | advertencias=%d",
        report.is_approved,
        len(report.flags_rojas),
        len(report.advertencias),
    )
    return 0


def main() -> int:
    """Execute orchestration with global, controlled exception handling."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        return run_pipeline()
    except ContractFileError as exc:
        logger.error("Input file failure: %s", exc)
        return 2
    except (LLMExtractionError, JSONParseError, LegalDataValidationError) as exc:
        logger.error("Pipeline domain failure: %s", exc)
        return 1
    except Exception as exc:
        logger.error("Unexpected fatal error: %s", exc)
        return 99


if __name__ == "__main__":
    sys.exit(main())
