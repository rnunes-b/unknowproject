from fastapi import APIRouter, HTTPException, Depends
from app.services import get_token, fetch_fgts_balance, fetch_filtered_status
from app.models import UserAuth
import httpx

router = APIRouter()


async def get_user_token(user: UserAuth):
    try:
        return await get_token(user.email, user.password)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail="Falha na autenticação"
        )


@router.post("/fgts-balance")
async def get_fgts_balance(
    cpf: str, user: UserAuth, token: str = Depends(get_user_token)
):
    try:
        balance = await fetch_fgts_balance(cpf, token)
        if balance["status"] == "error":
            raise HTTPException(status_code=404, detail=balance["message"])
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filtered-status")
async def get_filtered_status(
    cpf: str, user: UserAuth, token: str = Depends(get_user_token)
):
    try:
        status_reasons = await fetch_filtered_status(cpf, token)
        return {"status_reasons": status_reasons}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
