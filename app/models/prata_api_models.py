from pydantic import BaseModel, EmailStr
from typing import Optional, Union

class UserAuth(BaseModel):
    email: EmailStr 
    password: str

class PixResume(BaseModel):
    cpf: str
    bank_name: str
    client_name: str
    account_number: str
    branch_code: str
    bank_id: int
    account_created_at: str
    account_type: str
    input_type: str = "pix"

class BankAccountInfo(BaseModel):
    account_number: str
    account_type: str
    bank_id: int
    branch_number: str
    input_type: str = "manual"
    account_created_at: Optional[str] = None

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
    pix_resume: Optional[PixResume] = None

class BankAccess(BaseModel):
    username: str
    password: str

class SimulationRequest(BaseModel):
    contact: Contact
    bank_access: BankAccess

class ProposalRequest(SimulationRequest):
    bank_access: BankAccess
    simulation: Optional[dict] = None
    bank_account_info: Optional[BankAccountInfo] = None

class FormalizationRequest(BaseModel):
    bank_access: BankAccess