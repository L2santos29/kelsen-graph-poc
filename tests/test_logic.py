"""Tests for deterministic legal logic graph evaluation."""

from __future__ import annotations

from datetime import date

from src.logic_graph import ContractEvaluator
from src.models import ContractData, ContractType, Jurisdiction


def _build_base_contract() -> ContractData:
	"""Create a valid baseline contract object for deterministic evaluations."""
	return ContractData(
		contract_type=ContractType.NDA,
		governing_jurisdiction=Jurisdiction.DELAWARE,
		effective_date=date(2026, 3, 1),
		explicit_expiration_date=date(2027, 3, 1),
		auto_renewal=False,
		non_renewal_notice_days=None,
		has_arbitration_clause=False,
		liability_cap_amount=500_000.0,
		indemnification_uncapped=False,
		confidentiality_survival_years=3,
		trade_secret_survival_years=5,
	)


def test_contract_evaluator_approves_fully_compliant_contract() -> None:
	"""A compliant contract should be approved with no red flags."""
	evaluator = ContractEvaluator()
	contract_data = _build_base_contract()

	report = evaluator.evaluate(contract_data)

	assert report.is_approved is True
	assert report.red_flags == []
	assert report.warnings == []


def test_contract_evaluator_rejects_contract_with_disallowed_jurisdiction() -> None:
	"""A disallowed jurisdiction should generate a red flag and reject contract."""
	evaluator = ContractEvaluator()
	contract_data = _build_base_contract().model_copy(
		update={"governing_jurisdiction": Jurisdiction.CA}
	)

	report = evaluator.evaluate(contract_data)

	assert report.is_approved is False
	assert len(report.red_flags) == 1
	assert "jurisdiction" in report.red_flags[0]
