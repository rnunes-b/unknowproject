import httpx
import asyncio
import os
from dotenv import load_dotenv
import re

load_dotenv()

LOGIN_URL = os.getenv("LOGIN_URL")
BALANCE_URL = os.getenv("BALANCE_URL")
STATUS_URL = os.getenv("STATUS_URL")


def format_cpf(cpf: str) -> str:
    cleaned_cpf = re.sub(r"\D", "", cpf)
    formatted_cpf = (
        f"{cleaned_cpf[:3]}.{cleaned_cpf[3:6]}.{cleaned_cpf[6:9]}-{cleaned_cpf[9:]}"
    )
    return formatted_cpf


async def get_token(email: str, password: str) -> str:
    payload = {"email": email, "password": password}
    async with httpx.AsyncClient() as client:
        response = await client.post(LOGIN_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["data"]["token"]


async def fetch_fgts_balance(cpf: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    formatted_cpf = format_cpf(cpf)
    retry_attempts = 2

    for attempt in range(retry_attempts):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{BALANCE_URL}?document={formatted_cpf}", headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("data"):
                    if data["data"]["status_reason"] is None:
                        filtered_status = await fetch_filtered_status(cpf, token)
                        if filtered_status and filtered_status[0] != "Status não encontrado":
                            return {"status": "success", "balance": filtered_status}

                        if attempt == retry_attempts - 1:
                            return {
                                "status": "success",
                                "message": "O status ainda está pendente. Por favor, tente buscar mais tarde."
                            }
                    else:
                        return {"status": "success", "result": data["data"]["status"]}
            
            except httpx.RequestError as exc:
                print(f"Erro ao solicitar saldo (tentativa {attempt + 1}): {exc}")
            
            if attempt < retry_attempts - 1:
                await asyncio.sleep(1)  

    return {
        "status": "error",
        "message": "Sistema indisponível no momento. Por favor, tente novamente mais tarde."
    }

async def fetch_filtered_status(cpf: str, token: str) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    formatted_cpf = format_cpf(cpf)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{STATUS_URL}?product_id=3", headers=headers)
            response.raise_for_status()
            data = response.json()
            filtered_status_reasons = [
                item["status_reason"]
                for item in data["data"]
                if item["document"] == formatted_cpf
            ]
            return (
                filtered_status_reasons[0]
                if filtered_status_reasons
                else ["Status não encontrado"]
            )
        except httpx.RequestError as exc:
            print(f"Erro ao buscar status: {exc}")
            return ["Erro ao buscar status"]
