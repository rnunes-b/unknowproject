from pydantic import BaseModel, EmailStr
from typing import Optional

class UserAuth(BaseModel):
    email: EmailStr 
    password: str

class Contact(BaseModel):
    cpf: str
    birthdate: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    document: Optional[str] = None
    document_issue_date: Optional[str] = None
    document_federation_unit: Optional[str] = None
    document_type: Optional[str] = None
    mother_name: Optional[str] = None
    city: Optional[str] = None
    suburb: Optional[str] = None
    number: Optional[str] = None
    state: Optional[str] = None
    street: Optional[str] = None
    zip_code: Optional[str] = None

class BankAccess(BaseModel):
    username: str
    password: str

class SimulationRequest(BaseModel):
    contact: Contact
    bank_access: BankAccess

class ProposalRequest(SimulationRequest):
    bank_access: BankAccess
    simulation: Optional[dict] = None

class FormalizationRequest(BaseModel):
    bank_access: BankAccess