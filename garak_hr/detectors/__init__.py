"""HR domain detectors for enterprise LLM security assessment."""

from garak_hr.detectors.bias import BiasDetector
from garak_hr.detectors.privacy import PrivacyDetector
from garak_hr.detectors.termination import TerminationAdviceDetector

__all__ = ["BiasDetector", "PrivacyDetector", "TerminationAdviceDetector"]
