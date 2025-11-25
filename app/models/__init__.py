"""
Modelos de datos de la aplicación.
"""

from app.models.employee import (
    PhysicalAddress,
    EmailAddress,
    TelephoneNumber,
    EmployeeCreate,
    EmployeeUpdate
)
from app.models.auth import OAuthConfig

__all__ = [
    "PhysicalAddress",
    "EmailAddress",
    "TelephoneNumber",
    "EmployeeCreate",
    "EmployeeUpdate",
    "OAuthConfig"
]
