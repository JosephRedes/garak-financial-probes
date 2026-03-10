"""
HR domain probes for enterprise LLM security assessment.

Standard probes test direct requests; advanced probes use indirect
framing, authority claims, and persona escalation to challenge models
that pass standard probes.
"""

from garak_hr.probes.bias import AdvancedProtectedClassBias, ProtectedClassBias
from garak_hr.probes.compensation import AdvancedCompensationLeakage, CompensationLeakage
from garak_hr.probes.privacy import AdvancedEmployeeDataPrivacy, EmployeeDataPrivacy
from garak_hr.probes.termination import UnauthorizedTerminationAdvice
from garak_hr.probes.workplace import HostileWorkplace

__all__ = [
    "ProtectedClassBias",
    "AdvancedProtectedClassBias",
    "EmployeeDataPrivacy",
    "AdvancedEmployeeDataPrivacy",
    "UnauthorizedTerminationAdvice",
    "CompensationLeakage",
    "AdvancedCompensationLeakage",
    "HostileWorkplace",
]

# Exported for use by the enterprise CLI domain registry
HR_PROBES = {
    "protected-class": ProtectedClassBias,
    "advanced-protected-class": AdvancedProtectedClassBias,
    "employee-privacy": EmployeeDataPrivacy,
    "advanced-employee-privacy": AdvancedEmployeeDataPrivacy,
    "termination-advice": UnauthorizedTerminationAdvice,
    "compensation": CompensationLeakage,
    "advanced-compensation": AdvancedCompensationLeakage,
    "hostile-workplace": HostileWorkplace,
}
