"""
Financial services probes for Garak LLM vulnerability scanner.

This module provides specialized probes for testing LLMs in financial contexts:
- Impartiality / AdvancedImpartiality: Unauthorized investment advice
- Misconduct / AdvancedMisconduct: Market manipulation, insider trading
- Disclosure / AdvancedDisclosure: Confidential information leakage
- Hallucination: Fabricated financial data
- Compliance / AdvancedCompliance: Regulatory violations
- Calculation: Financial math errors
- Leakage: Proprietary data exposure
- Sycophancy / AdvancedSycophancy: Risk validation

Advanced probes use indirect framing, authority claims, and persona embedding
to test guardrails that handle direct requests correctly.
"""

from garak_financial.probes.calculation import Calculation
from garak_financial.probes.compliance import AdvancedCompliance, Compliance
from garak_financial.probes.disclosure import AdvancedDisclosure, Disclosure
from garak_financial.probes.hallucination import Hallucination
from garak_financial.probes.impartiality import AdvancedImpartiality, Impartiality
from garak_financial.probes.leakage import Leakage
from garak_financial.probes.misconduct import AdvancedMisconduct, Misconduct
from garak_financial.probes.sycophancy import AdvancedSycophancy, Sycophancy

__all__ = [
    "Impartiality",
    "AdvancedImpartiality",
    "Misconduct",
    "AdvancedMisconduct",
    "Disclosure",
    "AdvancedDisclosure",
    "Hallucination",
    "Compliance",
    "AdvancedCompliance",
    "Calculation",
    "Leakage",
    "Sycophancy",
    "AdvancedSycophancy",
]
