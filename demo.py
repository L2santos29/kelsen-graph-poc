"""Showroom CLI entry point for Kelsen-Graph demonstrations.

Stage 1 scope:
- Define a simple, friendly CLI interface.
- Support a mock toggle for zero-setup demos.
- Provide a default contract path for one-command execution.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from src.config import get_settings
from src.exceptions import JSONParseError, LLMExtractionError, LegalDataValidationError
from src.logic_graph import ContractEvaluator
from src.models import ContractData, ContractType, Jurisdiction

DEFAULT_CONTRACT_PATH = "data/dummy_contract.txt"


class ContractFileError(Exception):
    """Raised when the demo contract file cannot be loaded."""


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the demo CLI parser.

    Returns:
        Configured `ArgumentParser` for the showroom command-line UX.
    """
    parser = argparse.ArgumentParser(
        description="Kelsen-Graph Showroom: executive legal contract assessment demo",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=DEFAULT_CONTRACT_PATH,
        help=(
            "Input contract path (.txt). "
            f"Default: {DEFAULT_CONTRACT_PATH}"
        ),
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help=(
            "Enable offline simulation mode for demo runs without API key "
            "or network access."
        ),
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip theatrical pauses for a faster demo run.",
    )
    return parser


def pause(seconds: float, fast_mode: bool) -> None:
    """Pause execution unless fast mode is enabled."""
    if not fast_mode:
        time.sleep(seconds)


def build_mock_payload() -> dict[str, object]:
    """Build a prefabricated extraction payload for offline demo mode."""
    return {
        "contract_type": ContractType.NDA,
        "governing_jurisdiction": Jurisdiction.DELAWARE,
        "effective_date": date(2026, 3, 1),
        "explicit_expiration_date": date(2027, 3, 1),
        "auto_renewal": False,
        "non_renewal_notice_days": None,
        "has_arbitration_clause": False,
        "liability_cap_amount": 500000.0,
        "indemnification_uncapped": False,
        "confidentiality_survival_years": 3,
        "trade_secret_survival_years": 5,
    }


def load_contract_text(contract_file_path: str) -> str:
    """Load raw contract text from the provided file path.

    Raises:
        ContractFileError: If file does not exist or cannot be read.
    """
    contract_path = Path(contract_file_path)
    if not contract_path.exists():
        raise ContractFileError(f"Contract file not found: {contract_path}")

    try:
        return contract_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractFileError(f"Could not read contract file: {contract_path}") from exc


def run_demo(contract_file_path: str, mock_mode: bool, fast_mode: bool) -> int:
    """Run showroom flow in offline-mock or online-production mode."""
    print("\n=== KELSEN-GRAPH SHOWROOM ===")

    print("\n[ACT 1/4] Reading legal document...")
    contract_text = load_contract_text(contract_file_path)
    print(f"✓ Document loaded: {contract_file_path}")
    print("...analyzing initial contract structure")
    pause(1, fast_mode)

    print("\n[ACT 2/4] The 'Eyes' (Neuro-Symbolic Extraction)")
    print("• LLM running in deterministic mode (temperature=0.0)")
    if mock_mode:
        print("• OFFLINE mode active: local simulation without network or API key")
        extracted_data = ContractData.model_validate(build_mock_payload())
    else:
        print("• ONLINE mode active: production extraction flow")
        settings = get_settings()
        from src.llm_extractor import extract_contract_data

        extracted_data = extract_contract_data(
            contract_text,
            api_key=settings.llm_api_key,
            api_url=settings.llm_api_url,
            model_name=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            mock_mode=settings.llm_mock_mode,
            mock_response_json=settings.llm_mock_response_json,
        )

    print("✓ Pydantic-validated JSON:")
    print(extracted_data.model_dump_json(indent=2))
    pause(1, fast_mode)

    print("\n[ACT 3/4] The 'Brain' (Deterministic Logic Graph)")
    print("• Executing legal decision matrix...")
    evaluator = ContractEvaluator()
    report = evaluator.evaluate(extracted_data)
    pause(1, fast_mode)

    print("\n[ACT 4/4] Final Verdict")
    if report.is_approved:
        print("🟢 APPROVED")
        print("The contract complies with configured deterministic policies.")
    else:
        print("🔴 REJECTED")
        print("Policy-violating clauses:")
        for flag in report.red_flags:
            print(f"  - {flag}")

    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"  - {warning}")

    print("\n=== END OF DEMO ===")
    return 0


def main() -> int:
    """Parse CLI arguments and execute showroom flow."""
    args = build_argument_parser().parse_args()

    try:
        return run_demo(
            contract_file_path=args.file,
            mock_mode=args.mock,
            fast_mode=args.fast,
        )
    except ValidationError as exc:
        print(f"\n[ERROR] Configuration/data validation failed: {exc}")
        return 3
    except ContractFileError as exc:
        print(f"\n[ERROR] Input file failure: {exc}")
        return 2
    except (LLMExtractionError, JSONParseError, LegalDataValidationError) as exc:
        print(f"\n[ERROR] Domain failure during demo execution: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
