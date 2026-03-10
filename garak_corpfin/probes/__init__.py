"""
Corporate finance domain probes for enterprise LLM security assessment.

Standard probes test direct requests; advanced probes use indirect
framing, authority claims, and escalation to challenge models that
pass standard probes.
"""

from garak_corpfin.probes.board import BoardConfidentiality
from garak_corpfin.probes.earnings import AdvancedEarningsManipulation, EarningsManipulation
from garak_corpfin.probes.insider import AdvancedInsiderInfo, InsiderInfo
from garak_corpfin.probes.ma import AdvancedMADisclosure, MADisclosure
from garak_corpfin.probes.valuation import ValuationFabrication

__all__ = [
    "MADisclosure",
    "AdvancedMADisclosure",
    "EarningsManipulation",
    "AdvancedEarningsManipulation",
    "ValuationFabrication",
    "InsiderInfo",
    "AdvancedInsiderInfo",
    "BoardConfidentiality",
]

# Exported for use by the enterprise CLI domain registry
CORPFIN_PROBES = {
    "ma-disclosure": MADisclosure,
    "advanced-ma-disclosure": AdvancedMADisclosure,
    "earnings-manipulation": EarningsManipulation,
    "advanced-earnings-manipulation": AdvancedEarningsManipulation,
    "valuation-fabrication": ValuationFabrication,
    "insider-info": InsiderInfo,
    "advanced-insider-info": AdvancedInsiderInfo,
    "board-confidentiality": BoardConfidentiality,
}
