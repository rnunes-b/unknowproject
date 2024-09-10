from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.services.prata_api_service import PrataApiService
from app.services import BankService
from app.models.prata_api_models import SimulationRequest, ProposalRequestPIX, ProposalRequestCC, FormalizationRequest
from app.utils import get_bank_info

router = APIRouter()

def get_prata_service():
    return PrataApiService()

def get_bank_service():
    return BankService()

@router.post("/simulate_fgts")
async def simulate_fgts(data: SimulationRequest, prata_service: PrataApiService = Depends(get_prata_service)):
    try:
        return await prata_service.simulate_fgts(data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send_proposal_pix")
async def send_proposal_pix(data: ProposalRequestPIX, prata_service: PrataApiService = Depends(get_prata_service)):
    try:
        proposal_data = data.dict(exclude_unset=True)
        proposal_data["send_method"] = "pix"
        return await prata_service.send_proposal_pix(proposal_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send_proposal_cc")
async def send_proposal_cc(data: ProposalRequestCC, prata_service: PrataApiService = Depends(get_prata_service)):
    try:
        proposal_data = data.dict(exclude_unset=True)
        proposal_data["send_method"] = "bank_account"
        return await prata_service.send_proposal_cc(proposal_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get_formalization_url/{proposal_id}")
async def get_formalization_url(proposal_id: str, data: FormalizationRequest, prata_service: PrataApiService = Depends(get_prata_service)):
    try:
        result = await prata_service.get_formalization_url(data.dict(), proposal_id)
        return {"link": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get_pix_infos/{cpf}")
async def get_pix_infos(cpf: str, data: dict, prata_service: PrataApiService = Depends(get_prata_service)):
    try:
        result = await prata_service._get_pix(data, cpf)
        return get_bank_info(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/banks")
async def get_banks(
    query: Optional[str] = Query(None, description="Código do banco ou parte do nome para busca")
):
    bank_service = get_bank_service()
    
    if query:
        bank = bank_service.search_bank(query)
        if bank:
            return [bank.dict()]
        else:
            return []
    else:
        return [bank.dict() for bank in bank_service.list_all_banks()]