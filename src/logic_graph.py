"""Deterministic legal decision graph foundations for Kelsen-Graph PoC.

This module will host auditable rule evaluations over validated `ContractData`
objects extracted from legal text.
"""

from __future__ import annotations

import logging
from typing import Callable

from .models import ContractData, EvaluationReport, Jurisdiction

logger = logging.getLogger(__name__)

RuleResult = tuple[bool, str]
RuleFn = Callable[[ContractData], RuleResult]
RuleConfig = tuple[str, RuleFn, str]


def evaluate_jurisdiction_rule(contract_data: ContractData) -> RuleResult:
	"""Validate allowed jurisdiction to reduce cross-border legal exposure.

	Legal rule:
		Legal approves automatic routing only for Delaware or New York governing
		law. Any other jurisdiction increases litigation complexity and should be
		treated as a policy failure.

	Args:
		contract_data: Pydantic-validated contract data.

	Returns:
		Tuple of (approved, legal_comment).
	"""
	logger.info("Evaluating jurisdiction rule.")
	jurisdiction = contract_data.governing_jurisdiction

	if jurisdiction is None:
		return (
			False,
			"Jurisdiction missing in extracted data; assume high risk and escalate.",
		)

	if not isinstance(jurisdiction, Jurisdiction):
		return (
			False,
			"Jurisdiction format is invalid; assume high risk and escalate to legal.",
		)

	allowed_jurisdictions = {Jurisdiction.DELAWARE, Jurisdiction.NY}

	if jurisdiction in allowed_jurisdictions:
		return True, "Jurisdiction approved by internal policy."

	return (
		False,
		"Jurisdiction out of policy (only Delaware or NY qualify for direct approval).",
	)


def evaluate_liability_cap_rule(contract_data: ContractData) -> RuleResult:
	"""Control financial risk transfer through liability-cap validation.

	Legal rule:
		A cap above USD 1,000,000 or absence of an explicit cap blocks automatic
		approval because it increases financial exposure and requires legal review.

	Args:
		contract_data: Pydantic-validated contract data.

	Returns:
		Tuple of (approved, legal_comment).
	"""
	logger.info("Evaluating liability-cap rule.")
	liability_cap = contract_data.liability_cap_amount

	if liability_cap is None:
		return (
			False,
			"Liability cap not identified; manual review is required.",
		)

	if not isinstance(liability_cap, (int, float)):
		return (
			False,
			"Liability cap is invalid; assume high risk and escalate to legal.",
		)

	if liability_cap <= 0:
		return (
			False,
			"Liability cap is non-positive; manual validation is required.",
		)

	if liability_cap > 1_000_000:
		return (
			False,
			"Liability cap exceeds USD 1,000,000; escalate to legal.",
		)

	return True, "Liability cap is within the allowed threshold."


def evaluate_decision_nodes(contract_data: ContractData) -> list[RuleResult]:
	"""Execute isolated rules to produce auditable legal compliance traces.

	Business rationale:
		Node-by-node evaluation prevents monolithic logic, enables per-rule audit,
		and preserves clear evidence of policy compliance and violations.

	Args:
		contract_data: Pydantic-validated contract data.

	Returns:
		Ordered list of (approved, legal_comment), one tuple per rule.
	"""
	logger.info("Starting deterministic decision-node evaluation.")
	rules: list[RuleFn] = [
		evaluate_jurisdiction_rule,
		evaluate_liability_cap_rule,
	]

	results: list[RuleResult] = []
	for rule in rules:
		try:
			approved, comment = rule(contract_data)
		except Exception as exc:
			logger.error("Internal failure while evaluating %s: %s", rule.__name__, exc)
			approved, comment = (
				False,
				f"Internal evaluation failure in {rule.__name__}; assume high risk.",
			)
		logger.info(
			"Result for %s | approved=%s | comment=%s",
			rule.__name__,
			approved,
			comment,
		)
		results.append((approved, comment))

	return results


class ContractEvaluator:
	"""Deterministic orchestration engine for contract policy evaluation.

	This class executes all registered rules, accumulates findings, and returns
	an immutable `EvaluationReport` without stopping on the first failure.

	Business rationale:
		The goal is not just fail-fast behavior, but a full legal assessment where
		red flags and warnings are visible together for decision-making.
	"""

	def __init__(self) -> None:
		"""Initialize the deterministic rule set."""
		self._rules: list[RuleConfig] = [
			("jurisdiction", evaluate_jurisdiction_rule, "red_flag"),
			("liability_cap", evaluate_liability_cap_rule, "warning"),
		]

	def evaluate(self, contract_data: ContractData) -> EvaluationReport:
		"""Build an auditable, consolidated contract-risk verdict.

		Business rationale:
			This method aggregates rule failures by severity to support approval,
			escalation, or rejection decisions with structured audit evidence.

		Args:
			contract_data: Pydantic-validated contract data to evaluate.

		Returns:
			EvaluationReport: Formal output with global approval, red flags, and
				warnings.
		"""
		logger.info("Starting full contract evaluation in ContractEvaluator.")

		red_flags: list[str] = []
		warnings: list[str] = []

		for rule_name, rule_fn, severity in self._rules:
			try:
				approved, legal_comment = rule_fn(contract_data)
			except Exception as exc:
				logger.error("Internal failure in rule %s: %s", rule_name, exc)
				approved = False
				legal_comment = (
					"Internal rule-engine failure; "
					"a conservative high-risk posture is applied."
				)
				severity = "red_flag"
			logger.info(
				"Rule=%s | approved=%s | severity=%s | comment=%s",
				rule_name,
				approved,
				severity,
				legal_comment,
			)

			if approved:
				continue

			if severity == "red_flag":
				red_flags.append(f"[{rule_name}] {legal_comment}")
			else:
				warnings.append(f"[{rule_name}] {legal_comment}")

		is_approved = len(red_flags) == 0
		report = EvaluationReport(
			is_approved=is_approved,
			red_flags=red_flags,
			warnings=warnings,
		)
		logger.info(
			"Evaluation finished | is_approved=%s | red_flags=%d | warnings=%d",
			report.is_approved,
			len(report.red_flags),
			len(report.warnings),
		)
		return report
