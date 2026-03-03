"""
Legal domain probes for enterprise LLM security assessment.

Standard probes test direct requests; advanced probes use indirect
framing, authority claims, and escalation to challenge models that
pass standard probes.
"""

from garak_legal.probes.advice import AdvancedUnauthorizedLegalAdvice, UnauthorizedLegalAdvice
from garak_legal.probes.disclosure import (
    AdvancedConfidentialMatterDisclosure,
    ConfidentialMatterDisclosure,
)
from garak_legal.probes.fabrication import CaseLawHallucination, ContractFabrication
from garak_legal.probes.litigation import AdvancedLitigationStrategy, LitigationStrategy
from garak_legal.probes.privilege import AdvancedPrivilegeLeakage, PrivilegeLeakage

__all__ = [
    "UnauthorizedLegalAdvice",
    "AdvancedUnauthorizedLegalAdvice",
    "PrivilegeLeakage",
    "AdvancedPrivilegeLeakage",
    "CaseLawHallucination",
    "ContractFabrication",
    "LitigationStrategy",
    "AdvancedLitigationStrategy",
    "ConfidentialMatterDisclosure",
    "AdvancedConfidentialMatterDisclosure",
]

# Exported for use by the enterprise CLI domain registry
LEGAL_PROBES = {
    "advice": UnauthorizedLegalAdvice,
    "advanced-advice": AdvancedUnauthorizedLegalAdvice,
    "privilege": PrivilegeLeakage,
    "advanced-privilege": AdvancedPrivilegeLeakage,
    "case-law": CaseLawHallucination,
    "contract": ContractFabrication,
    "litigation": LitigationStrategy,
    "advanced-litigation": AdvancedLitigationStrategy,
    "disclosure": ConfidentialMatterDisclosure,
    "advanced-disclosure": AdvancedConfidentialMatterDisclosure,
}
