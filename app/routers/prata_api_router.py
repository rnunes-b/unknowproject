
from fastapi import APIRouter, HTTPException
from app.services.prata_api_service import PrataApiService
from app.models.prata_api_models import SimulationRequest, ProposalRequest, FormalizationRequest
import traceback
router = APIRouter()
prata_service = PrataApiService()

@router.post("/simulate_fgts")
async def simulate_fgts(data: SimulationRequest):
    try:
        result = await prata_service.simulate_fgts(data.dict())
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send_proposal")
async def send_proposal(data: ProposalRequest):
    try:
        result = await prata_service.send_proposal(data.dict())
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get_formalization_url/{proposal_id}")
async def get_formalization_url(proposal_id: str, data: FormalizationRequest):
    try:
        result = await prata_service.get_formalization_url(data.dict(), proposal_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))