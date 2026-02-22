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


def evaluar_regla_jurisdiccion(contract_data: ContractData) -> RuleResult:
	"""Valida jurisdicción permitida para reducir exposición legal internacional.

	Regla legal:
		El departamento legal solo aprueba automáticamente contratos regidos por
		Delaware o Nueva York. Cualquier otra jurisdicción incrementa el riesgo de
		litigio transfronterizo, costos procesales y complejidad de ejecución, por
		lo que debe tratarse como incumplimiento de política base.

	Args:
		contract_data: Contrato validado por Pydantic.

	Returns:
		Tupla (aprobado, comentario_legal).
	"""
	logger.info("Evaluando regla de jurisdicción.")
	jurisdiction = contract_data.governing_jurisdiction

	if jurisdiction is None:
		return (
			False,
			"Jurisdicción ausente en los datos extraídos; asumir riesgo alto y escalar.",
		)

	if not isinstance(jurisdiction, Jurisdiction):
		return (
			False,
			"Jurisdicción con formato inválido; asumir riesgo alto y escalar a legal.",
		)

	allowed_jurisdictions = {Jurisdiction.DELAWARE, Jurisdiction.NY}

	if jurisdiction in allowed_jurisdictions:
		return True, "Jurisdicción aprobada por política interna."

	return (
		False,
		"Jurisdicción fuera de política (solo Delaware o NY para aprobación directa).",
	)


def evaluar_regla_limite_responsabilidad(contract_data: ContractData) -> RuleResult:
	"""Controla transferencia de riesgo económico vía límite de responsabilidad.

	Regla legal:
		Un límite superior a USD 1,000,000 o la ausencia de un límite explícito
		impide aprobación automática porque amplía la exposición financiera de la
		compañía y exige revisión manual por Legal/Compliance.

	Args:
		contract_data: Contrato validado por Pydantic.

	Returns:
		Tupla (aprobado, comentario_legal).
	"""
	logger.info("Evaluando regla de límite de responsabilidad.")
	liability_cap = contract_data.liability_cap_amount

	if liability_cap is None:
		return (
			False,
			"Límite de responsabilidad no identificado; requiere revisión manual.",
		)

	if not isinstance(liability_cap, (int, float)):
		return (
			False,
			"Límite de responsabilidad inválido; asumir riesgo alto y escalar a legal.",
		)

	if liability_cap <= 0:
		return (
			False,
			"Límite de responsabilidad no positivo; requiere validación manual.",
		)

	if liability_cap > 1_000_000:
		return (
			False,
			"Límite de responsabilidad superior a USD 1,000,000; escalar a legal.",
		)

	return True, "Límite de responsabilidad dentro del umbral permitido."


def evaluar_nodos_decision(contract_data: ContractData) -> list[RuleResult]:
	"""Ejecuta reglas aisladas para producir trazabilidad de cumplimiento legal.

	Racional de negocio:
		La evaluación separada por nodos evita lógica monolítica, permite auditoría
		regla-por-regla y conserva evidencia clara de qué políticas corporativas se
		cumplen o se violan en cada contrato.

	Args:
		contract_data: Contrato validado por Pydantic.

	Returns:
		Lista ordenada de resultados (aprobado, comentario_legal), uno por regla.
	"""
	logger.info("Iniciando evaluación determinista de nodos de decisión.")
	reglas: list[RuleFn] = [
		evaluar_regla_jurisdiccion,
		evaluar_regla_limite_responsabilidad,
	]

	resultados: list[RuleResult] = []
	for regla in reglas:
		try:
			aprobado, comentario = regla(contract_data)
		except Exception as exc:
			logger.error("Fallo interno evaluando %s: %s", regla.__name__, exc)
			aprobado, comentario = (
				False,
				f"Fallo interno de evaluación en {regla.__name__}; asumir riesgo alto.",
			)
		logger.info(
			"Resultado de %s | aprobado=%s | comentario=%s",
			regla.__name__,
			aprobado,
			comentario,
		)
		resultados.append((aprobado, comentario))

	return resultados


class ContractEvaluator:
	"""Orquestador determinista del grafo lógico para evaluación contractual.

	Esta clase ejecuta todas las reglas registradas, acumula hallazgos y retorna
	un reporte formal e inmutable (`EvaluationReport`) sin detenerse ante el
	primer incumplimiento.

	Racional de negocio:
		El objetivo no es "fallar rápido", sino producir un dictamen integral para
		que el equipo legal vea simultáneamente todas las banderas rojas y
		advertencias antes de negociar o rechazar el contrato.
	"""

	def __init__(self) -> None:
		"""Inicializa el set de reglas del motor determinista."""
		self._rules: list[RuleConfig] = [
			("jurisdiccion", evaluar_regla_jurisdiccion, "flag_roja"),
			("limite_responsabilidad", evaluar_regla_limite_responsabilidad, "advertencia"),
		]

	def evaluate(self, contract_data: ContractData) -> EvaluationReport:
		"""Construye un veredicto integral y auditable de riesgo contractual.

		Racional de negocio:
			El método agrega incumplimientos por severidad para soportar decisiones
			de aprobación, escalado o rechazo con evidencia estructurada y
			explicable ante auditoría interna.

		Args:
			contract_data: Contrato validado por Pydantic a evaluar.

		Returns:
			EvaluationReport: Resultado formal con aprobación global, flags rojas y
				advertencias acumuladas.
		"""
		logger.info("Iniciando evaluación integral del contrato en ContractEvaluator.")

		flags_rojas: list[str] = []
		advertencias: list[str] = []

		for rule_name, rule_fn, severity in self._rules:
			try:
				approved, legal_comment = rule_fn(contract_data)
			except Exception as exc:
				logger.error("Fallo interno en regla %s: %s", rule_name, exc)
				approved = False
				legal_comment = (
					"Fallo interno del motor al evaluar la regla; "
					"se aplica postura conservadora (riesgo alto)."
				)
				severity = "flag_roja"
			logger.info(
				"Regla=%s | aprobado=%s | severidad=%s | comentario=%s",
				rule_name,
				approved,
				severity,
				legal_comment,
			)

			if approved:
				continue

			if severity == "flag_roja":
				flags_rojas.append(f"[{rule_name}] {legal_comment}")
			else:
				advertencias.append(f"[{rule_name}] {legal_comment}")

		is_approved = len(flags_rojas) == 0
		report = EvaluationReport(
			is_approved=is_approved,
			flags_rojas=flags_rojas,
			advertencias=advertencias,
		)
		logger.info(
			"Evaluación finalizada | is_approved=%s | flags_rojas=%d | advertencias=%d",
			report.is_approved,
			len(report.flags_rojas),
			len(report.advertencias),
		)
		return report
