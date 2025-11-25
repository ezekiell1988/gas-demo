"""
Modelos Pydantic para Employee.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date


class PhysicalAddress(BaseModel):
    """Dirección física del empleado."""
    Line1: Optional[str] = Field(None, max_length=500)
    Line2: Optional[str] = Field(None, max_length=500)
    Line3: Optional[str] = Field(None, max_length=500)
    Line4: Optional[str] = Field(None, max_length=500)
    Line5: Optional[str] = Field(None, max_length=500)
    City: Optional[str] = Field(None, max_length=255)
    Country: Optional[str] = None
    CountrySubDivisionCode: Optional[str] = Field(None, max_length=255, description="Código de estado/provincia")
    PostalCode: Optional[str] = None


class EmailAddress(BaseModel):
    """Email del empleado."""
    Address: Optional[EmailStr] = None


class TelephoneNumber(BaseModel):
    """Número telefónico."""
    FreeFormNumber: Optional[str] = Field(None, max_length=20)


class EmployeeCreate(BaseModel):
    """Modelo para crear un empleado."""
    GivenName: str = Field(..., max_length=100, description="Nombre")
    FamilyName: str = Field(..., max_length=100, description="Apellido")
    MiddleName: Optional[str] = Field(None, max_length=100, description="Segundo nombre")
    DisplayName: Optional[str] = Field(None, max_length=500)
    Title: Optional[str] = Field(None, max_length=16)
    Suffix: Optional[str] = Field(None, max_length=16)
    PrimaryEmailAddr: Optional[EmailAddress] = None
    PrimaryPhone: Optional[TelephoneNumber] = None
    Mobile: Optional[TelephoneNumber] = None
    PrimaryAddr: Optional[PhysicalAddress] = None
    EmployeeNumber: Optional[str] = Field(None, max_length=100)
    SSN: Optional[str] = Field(None, max_length=100)
    Gender: Optional[str] = Field(None, description="Male o Female")
    HiredDate: Optional[date] = None
    ReleasedDate: Optional[date] = None
    BirthDate: Optional[date] = None
    BillableTime: Optional[bool] = False
    BillRate: Optional[float] = None
    CostRate: Optional[float] = None
    Active: Optional[bool] = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "GivenName": "Juan",
                "FamilyName": "Pérez",
                "MiddleName": "Carlos",
                "DisplayName": "Juan C. Pérez",
                "PrimaryEmailAddr": {
                    "Address": "juan.perez@example.com"
                },
                "PrimaryPhone": {
                    "FreeFormNumber": "(555) 123-4567"
                },
                "Mobile": {
                    "FreeFormNumber": "(555) 987-6543"
                },
                "PrimaryAddr": {
                    "Line1": "123 Main Street",
                    "City": "San Francisco",
                    "CountrySubDivisionCode": "CA",
                    "PostalCode": "94107"
                },
                "EmployeeNumber": "EMP-001",
                "Gender": "Male",
                "HiredDate": "2024-01-15",
                "Active": True
            }
        }


class EmployeeUpdate(BaseModel):
    """Modelo para actualizar un empleado."""
    Id: str = Field(..., description="ID del empleado")
    SyncToken: str = Field(..., description="Token de sincronización")
    GivenName: str = Field(..., max_length=100)
    FamilyName: str = Field(..., max_length=100)
    MiddleName: Optional[str] = Field(None, max_length=100)
    DisplayName: Optional[str] = Field(None, max_length=500)
    Title: Optional[str] = Field(None, max_length=16)
    Suffix: Optional[str] = Field(None, max_length=16)
    PrimaryEmailAddr: Optional[EmailAddress] = None
    PrimaryPhone: Optional[TelephoneNumber] = None
    Mobile: Optional[TelephoneNumber] = None
    PrimaryAddr: Optional[PhysicalAddress] = None
    EmployeeNumber: Optional[str] = Field(None, max_length=100)
    SSN: Optional[str] = Field(None, max_length=100)
    Gender: Optional[str] = None
    HiredDate: Optional[date] = None
    ReleasedDate: Optional[date] = None
    BirthDate: Optional[date] = None
    BillableTime: Optional[bool] = None
    BillRate: Optional[float] = None
    CostRate: Optional[float] = None
    Active: Optional[bool] = None
