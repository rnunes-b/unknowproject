from pydantic import BaseModel
from typing import Optional, Dict, Any

class SimulationRequest(BaseModel):
    contact: Dict[str, Any]
    bank_access: Dict[str, str]

class PIXResume(BaseModel):
    account_number: str
    account_type: str
    bank_id: str
    branch_code: str
    account_created_at: str

class Contact(BaseModel):
    cpf: str
    birthdate: str
    gender: str
    name: str
    phone: str
    document_issue_date: str
    document: str
    document_federation_unit: str
    document_type: str
    mother_name: str
    city: str
    suburb: str
    number: str
    state: str
    street: str
    zip_code: str

class ProposalRequestPIX(BaseModel):
    contact: Contact
    pix_resume: PIXResume
    bank_access: Dict[str, str]

class BankAccountInfo(BaseModel):
    account_number: str
    account_type: str
    bank_id: str
    branch_number: str

class ProposalRequestCC(BaseModel):
    contact: Contact
    bank_account_info: BankAccountInfo
    bank_access: Dict[str, str]

class FormalizationRequest(BaseModel):
    bank_access: Dict[str, str]