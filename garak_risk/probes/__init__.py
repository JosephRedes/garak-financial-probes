"""
Risk management domain probes for enterprise LLM security assessment.

Standard probes test direct requests; advanced probes use indirect
framing, authority claims, and escalation to challenge models that
pass standard probes.
"""

from garak_risk.probes.credit_risk import (
    AdvancedCreditRiskMisrepresentation,
    CreditRiskMisrepresentation,
)
from garak_risk.probes.model_risk import AdvancedModelRiskGuidance, ModelRiskGuidance
from garak_risk.probes.operational import OperationalRiskEvasion
from garak_risk.probes.regulatory import AdvancedRegulatoryCapitalAdvice, RegulatoryCapitalAdvice
from garak_risk.probes.stress_test import StressTestFabrication

__all__ = [
    "ModelRiskGuidance",
    "AdvancedModelRiskGuidance",
    "CreditRiskMisrepresentation",
    "AdvancedCreditRiskMisrepresentation",
    "StressTestFabrication",
    "OperationalRiskEvasion",
    "RegulatoryCapitalAdvice",
    "AdvancedRegulatoryCapitalAdvice",
]

# Exported for use by the enterprise CLI domain registry
RISK_PROBES = {
    "model-risk": ModelRiskGuidance,
    "advanced-model-risk": AdvancedModelRiskGuidance,
    "credit-risk": CreditRiskMisrepresentation,
    "advanced-credit-risk": AdvancedCreditRiskMisrepresentation,
    "stress-test": StressTestFabrication,
    "operational-risk": OperationalRiskEvasion,
    "regulatory-capital": RegulatoryCapitalAdvice,
    "advanced-regulatory-capital": AdvancedRegulatoryCapitalAdvice,
}
