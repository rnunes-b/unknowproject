from typing import Dict, Any
from app.utils import format_result, extract_max_value, format_cpf, format_date, format_phone
from app.exceptions import BotProposalInfoException, BotUnauthorizedException
import httpx
import time
import traceback

class PrataApiService:
    def __init__(self):
        self.login_url = "https://api.bancoprata.com.br/v1/users/login"
        self.simulate_proposal_url = "https://api.bancoprata.com.br/v1/qitech/fgts/balance"
        self.status_url = "https://api.bancoprata.com.br/v1/qitech/fgts/balance-wait-list"
        self.pix_url = "https://api.bancoprata.com.br/v1/payments/bank-account/info"
        self.first_stage = "https://api.bancoprata.com.br/v1/clients/account/admin"
        self.second_stage = "https://api.bancoprata.com.br/v1/clients/qualification/admin"
        self.third_stage = "https://api.bancoprata.com.br/v1/clients/address/admin"
        self.fourth_stage = "https://api.bancoprata.com.br/v1/clients/bank-account/admin"
        self.send_proposal_url = "https://api.bancoprata.com.br/v1/proposals/admin"
        self.detail_url = "https://api.bancoprata.com.br/v1/proposals/"
        self.proposals_url = "https://ymlzcthbmqcpwaiwcg3hikmbpa0rsehz.lambda-url.us-east-1.on.aws/v1/proposals?product_id=3"
        self.formalization_url = "https://api.bancoprata.com.br/v1/anti-fraud?account_id="
        self.retry_attempts = 3
        self.retry_delay = 5

    async def authenticate(self, data):
        try:
            user_data = data["bank_access"]
            payload = {
                "email": user_data["username"],
                "password": user_data["password"],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.login_url, json=payload, timeout=10)
                response.raise_for_status()

            context = response.json()
            return context["data"]["token"]

        except httpx.RequestError as error:
            traceback.print_exc()
            raise BotUnauthorizedException(
                f"Não foi possível autenticar, verfique as credenciais informadas. E tente novamente, se o problema persistir contacte o suporte. {str(error)}"
            )

        except (KeyError, ValueError) as e:
            raise BotUnauthorizedException(f"Verifique os dados informados: {str(e)}")

        except Exception as e:
            raise BotUnauthorizedException(
                f"Erro inesperado, entre em contato: {str(e)}"
            )

    async def simulate_fgts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        token = await self.authenticate(data)
        headers = {"Authorization": f"Bearer {token}"}
        cpf = format_cpf(data["contact"]["cpf"])

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.simulate_proposal_url}?document={cpf}", headers=headers
                )
                response.raise_for_status()
                result = response.json()

            if not result.get("data"):
                raise BotProposalInfoException(
                    "Status ainda não disponível, tentar novamente em alguns minutos"
                )

            if result["data"].get("status_reason"):
                raise BotProposalInfoException(result["data"]["status_reason"])

            if not result["data"].get("issue_amount"):
                return await self.fetch_filtered_status(data)
            
            value_issue = result["data"]["issue_amount"]

            value = await self.fetch_check_value(data, cpf, value_issue)

            strategy_result = await self.fetch_strategy(data, cpf, value)

            pix_result = await self.fetch_pix(data, cpf)

            pix_resume = self.create_pix_resume(pix_result["data"])

            strategy_result["pix_resume"] = pix_resume

            return strategy_result

        except httpx.RequestError as e:
            traceback.print_exc()
            raise BotProposalInfoException(
                f"Não foi possível simular o valor, tente novamente mais tarde: {str(e)}"
            )

    async def fetch_filtered_status(self, data):
        token = await self.authenticate(data)
        headers = {"Authorization": f"Bearer {token}"}
        cpf = format_cpf(data["contact"]["cpf"])

        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.status_url}?product_id=3", headers=headers
                    )
                    response.raise_for_status()
                    result = response.json()
                    filtered_status_reasons = [
                        item["status_reason"]
                        for item in result.get("data", [])
                        if item.get("document") == cpf and item.get("status_reason")
                    ]
                    if filtered_status_reasons:
                        raise BotProposalInfoException(filtered_status_reasons[0])

                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise BotProposalInfoException(
                            "Status ainda não disponível, tentar novamente mais tarde",
                        )

            except httpx.RequestError:
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise BotProposalInfoException(
                        "Não foi possivel encontrar o status, tente novamente mais tarde"
                    )

    async def fetch_strategy(self, data, cpf, value):
        token = await self.authenticate(data)
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient() as client:
                strategy = await client.get(
                    f"{self.simulate_proposal_url}?document={cpf}&rate_id=16&wish_amount={value}",
                    headers=headers,
                )
                strategy.raise_for_status()
                strategy_result = format_result(strategy.json())
                return strategy_result
        except httpx.RequestError:
            raise BotProposalInfoException(strategy.json())

    async def fetch_check_value(self, data, cpf, value):
        token = await self.authenticate(data)
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient() as client:
                strategy = await client.get(
                    f"{self.simulate_proposal_url}?document={cpf}&rate_id=16&wish_amount={value}",
                    headers=headers,
                )
                value = extract_max_value(strategy.json())
                return value
        except httpx.RequestError:
            raise BotProposalInfoException(strategy.json())

    async def fetch_pix(self, data, cpf):
        token = await self.authenticate(data)
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.pix_url}?pix_key={cpf}&btn_clicked=true", headers=headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError:
            raise BotProposalInfoException(response.json())

    async def send_proposal(self, data):
        try:
            token = await self.authenticate(data)
            headers = {"Authorization": f"Bearer {token}"}
            cpf = format_cpf(data["contact"]["cpf"])

            simulation_result = await self.simulate_fgts(data)
            simulation_fields = {
                "contract_balance": simulation_result["contract_balance"],
                "amount_released": simulation_result["amount_released"],
                "account_number": simulation_result["pix_resume"]["account_number"],
                "account_type": simulation_result["pix_resume"]["account_type"],
                "bank_id": simulation_result["pix_resume"]["bank_id"],
                "branch_number": simulation_result["pix_resume"]["branch_code"],
                "input_type": simulation_result["pix_resume"]["input_type"],
                "account_created_at": simulation_result["pix_resume"]["account_created_at"],
            } 

            account_id = await self._send_first_stage(data, headers)
            await self._send_second_stage(data, headers, account_id)
            await self._send_third_stage(data, headers, account_id)
            await self._send_pix_stage(simulation_fields, headers, account_id, cpf)
            proposal = await self._send_last_stage(simulation_fields, headers, account_id)
            url = await self.get_formalization_url(data, proposal["proposal_identifier"])

            return {"resume": proposal["proposal_number"], "formalization_url": url}
        except httpx.RequestError as e:
            raise BotProposalInfoException(str(e))

    async def _send_first_stage(self, data, headers):
        first_stage = {
            "birthdate": format_date(data["contact"]["birthdate"]),
            "document": format_cpf(data["contact"]["cpf"]),
            "email": "falecom@bancoprata.com.br",
            "gender": (
                "Masculino" if data["contact"]["gender"] == "M" else "Feminino"
            ),
            "name": data["contact"]["name"],
            "phone": format_phone(data["contact"]["phone"]),
        }
        response = await self._send_request(self.first_stage, headers, first_stage)
        return response["data"]["id"]

    async def _send_second_stage(self, data, headers, account_id):
        second_stage = {
            "account_id": account_id,
            "alimony": "",
            "company_document": "",
            "dependents": "",
            "document_issued_at": format_date(
                data["contact"]["document_issue_date"]
            ),
            "document_number": data["contact"]["document"],
            "document_state": data["contact"]["document_federation_unit"],
            "document_type": data["contact"]["document_type"],
            "marital_status": "Solteiro(a)",
            "mother_name": data["contact"]["mother_name"],
        }
        await self._send_request(self.second_stage, headers, second_stage)

    async def _send_third_stage(self, data, headers, account_id):
        third_stage = {
            "account_id": account_id,
            "city": data["contact"]["city"],
            "neighborhood": data["contact"]["suburb"],
            "number": data["contact"]["number"],
            "state": data["contact"]["state"],
            "street": data["contact"]["street"],
            "unit": "",
            "zipcode": data["contact"]["zip_code"],
        }
        await self._send_request(self.third_stage, headers, third_stage)

    async def _send_pix_stage(self, data, headers, account_id, cpf):
        pix_stage = {
            "account_created_at": data["account_created_at"],
            "account_id": account_id,
            "account_number": data["account_number"],
            "account_type": data["account_type"],
            "bank_id": data["bank_id"],
            "branch_number": data["branch_number"],
            "input_type": data["input_type"],
            "pix_key": cpf,
        
        }
        await self._send_request(self.fourth_stage, headers, pix_stage)

    async def _send_last_stage(self, data, headers, account_id):
        proposal = {
            "account_id": account_id,
            "amount": data["contract_balance"],
            "product_id": 3,
            "rate_id": 15,
            "status": "Pendência",
            "total_amount": "",
            "wish_amount": data["amount_released"],
            "wish_bankaccount": False,
            "wish_creditcard": False,
        }
        response = await self._send_request(self.send_proposal_url, headers, proposal)
        number = response["data"]["id"]
        proposal_identifier = response["data"]["account_id"]

        return {"proposal_number": number, "proposal_identifier": proposal_identifier}

    async def _send_request(self, url, headers, data):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            traceback.print_exc()
            raise BotProposalInfoException(str(e))

    @staticmethod
    def create_pix_resume(pix_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "cpf": pix_data["key"],
            "bank_name": pix_data["bankName"],
            "client_name": pix_data["name"],
            "account_number": pix_data["accountNumber"],
            "branch_code": pix_data["branchCode"],
            "bank_id": pix_data["bank_id"],
            "account_created_at": pix_data["created"],
            "account_type": "Corrente",
            "input_type": "pix",
        }


    async def get_formalization_url(self, data, proposal_id):
        try:
            token = await self.authenticate(data)
            headers = {"Authorization": f"Bearer {token}"}

            url = f"{self.formalization_url}{proposal_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                formalization = response.json()
                url = f"https://assina.bancoprata.com.br/validacao/{formalization['data']['token']}"

            return url

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "status": "Not Found",
                    "message": "Ainda não foi possível encontrar o link de formalização, tente novamente mais tarde.",
                }
            else:
                return {
                    "status": "Error",
                    "message": f"Ocorreu um erro ao buscar o link de formalização. Status: {e.response.status_code}. Por favor, tente novamente mais tarde.",
                }
        except httpx.RequestError as e:
            return {
                "status": "Error",
                "message": f"Ocorreu um erro de conexão ao buscar o link de formalização: {str(e)}. Por favor, tente novamente mais tarde.",
            }

