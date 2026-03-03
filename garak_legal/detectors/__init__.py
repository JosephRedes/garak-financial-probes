"""Legal domain detectors for enterprise LLM security assessment."""

from garak_legal.detectors.advice import LegalAdviceDetector
from garak_legal.detectors.fabrication import LegalFabricationDetector
from garak_legal.detectors.privilege import PrivilegeDetector

__all__ = [
    "LegalAdviceDetector",
    "PrivilegeDetector",
    "LegalFabricationDetector",
]
