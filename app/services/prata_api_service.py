from typing import Dict, Any
from app.utils import format_result, format_cpf, format_date, format_phone
from app.exceptions import BotProposalInfoException, BotUnauthorizedException
import httpx
import time
from dotenv import load_dotenv
import traceback
import os
import json


load_dotenv()


class PrataApiService:
    def __init__(self):
        self.proxy_url = os.getenv("PROXY_URL")
        self.login_url = "https://api.bancoprata.com.br/v1/users/login"
        self.simulate_proposal_url = (
            "https://api.bancoprata.com.br/v1/qitech/fgts/balance"
        )
        self.status_url = (
            "https://api.bancoprata.com.br/v1/qitech/fgts/balance-wait-list"
        )
        self.pix_url = "https://api.bancoprata.com.br/v1/payments/bank-account/info"
        self.first_stage = "https://api.bancoprata.com.br/v1/clients/account/admin"
        self.second_stage = (
            "https://api.bancoprata.com.br/v1/clients/qualification/admin"
        )
        self.third_stage = "https://api.bancoprata.com.br/v1/clients/address/admin"
        self.fourth_stage = (
            "https://api.bancoprata.com.br/v1/clients/bank-account/admin"
        )
        self.send_proposal_url = "https://api.bancoprata.com.br/v1/proposals/admin"
        self.detail_url = "https://api.bancoprata.com.br/v1/proposals/"
        self.proposals_url = "https://ymlzcthbmqcpwaiwcg3hikmbpa0rsehz.lambda-url.us-east-1.on.aws/v1/proposals?product_id=3"
        self.formalization_url = (
            "https://api.bancoprata.com.br/v1/anti-fraud?account_id="
        )
        self.retry_attempts = 3
        self.retry_delay = 5
        self.token = None
        self.client = None
        self.cookies = httpx.Cookies()

    async def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        headers_agent = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": "https://api.bancoprata.com.br/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        if self.client is None:
            self.client = httpx.AsyncClient(
                proxies={"http://": self.proxy_url, "https://": self.proxy_url},
                headers=headers_agent,
                cookies=self.cookies,
                timeout=30.0,
            )

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            self.cookies.update(response.cookies)

            return response
        except httpx.HTTPStatusError as e:
            traceback.print_exc()
            error_message = f"HTTP error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if isinstance(error_data, dict) and "error" in error_data:
                    error_message = error_data["error"].get("message", error_message)
            except json.JSONDecodeError:
                error_message += f" - Response: {e.response.text}"
            raise BotProposalInfoException(error_message)
        except httpx.RequestError as error:
            raise BotProposalInfoException(f"Request error: {str(error)}")
        except Exception as e:
            raise BotProposalInfoException(f"Unexpected error: {str(e)}")

    async def authenticate(self, data: Dict[str, Any]) -> str:
        if self.token:
            return self.token
        try:
            user_data = data["bank_access"]
            payload = {
                "email": user_data["username"],
                "password": user_data["password"],
            }
            response = await self._make_request(
                "POST", self.login_url, json=payload, timeout=10
            )

            for encoding in ["utf-8", "latin-1", "iso-8859-1"]:
                try:
                    context = json.loads(response.content.decode(encoding))
                    self.token = context["data"]["token"]
                    return self.token
                except UnicodeDecodeError:
                    continue

            raise BotUnauthorizedException(
                "Não foi possível decodificar a resposta do servidor"
            )

        except BotProposalInfoException as e:
            raise BotUnauthorizedException(f"Erro de autenticação: {str(e)}")
        except Exception as e:
            raise BotUnauthorizedException(f"Erro inesperado: {str(e)}")

    async def get_auth_headers(self, data: Dict[str, Any]) -> Dict[str, str]:
        if not self.token:
            await self.authenticate(data)
        return {"Authorization": f"Bearer {self.token}"}

    async def simulate_fgts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        headers = await self.get_auth_headers(data)
        cpf = format_cpf(data["contact"]["cpf"])

        try:
            response = await self._make_request(
                "GET", f"{self.simulate_proposal_url}?document={cpf}", headers=headers
            )
            result = response.json()

            if not result.get("data"):
                raise BotProposalInfoException(
                    "Status ainda não disponível, tentar novamente em alguns minutos"
                )

            if result["data"].get("status_reason"):
                raise BotProposalInfoException(result["data"]["status_reason"])

            if not result["data"].get("issue_amount"):
                return await self.fetch_filtered_status(data)

            strategy_result = await self.fetch_check_value(data, cpf)

            # pix_result = await self.fetch_pix(data, cpf)
            # pix_result = None

            # if pix_result["data"]:
            #     pix_resume = self.create_pix_resume(pix_result["data"])
            # else:
            #     pix_resume = None

            # strategy_result["pix_resume"] = pix_resume

            return strategy_result

        except BotProposalInfoException as e:
            traceback.print_exc()
            raise BotProposalInfoException(f"Erro na simulação: {str(e)}")

    async def fetch_filtered_status(self, data):
        headers = await self.get_auth_headers(data)
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
                        "Erro ao buscar status, tente novamente mais tarde"
                    )

    # async def fetch_check_value(self, data, cpf):
    #     headers = await self.get_auth_headers(data)
    #     try:
    #         async with httpx.AsyncClient() as client:
    #             strategy = await client.get(
    #                 f"{self.simulate_proposal_url}?document={cpf}&rate_id=16",
    #                 headers=headers,
    #             )
    #             resume = strategy.json()
    #             return format_result(resume)
    #     except httpx.RequestError:
    #         raise BotProposalInfoException(strategy.json())

    async def fetch_check_value(self, data, cpf):
        headers = await self.get_auth_headers(data)
        try:
            response = await self._make_request(
                "GET",
                f"{self.simulate_proposal_url}?document={cpf}&rate_id=16",
                headers=headers,
            )

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")

            try:
                resume = response.json()
            except json.JSONDecodeError:
                print("Failed to decode JSON. Response might not be JSON.")
                if response.text.strip() == "":
                    print("Response is empty.")
                    raise BotProposalInfoException(
                        "Received empty response from server"
                    )
                else:
                    print(f"Non-JSON response: {response.text}")
                    raise BotProposalInfoException(
                        f"Received non-JSON response: {response.text[:100]}..."
                    )

            return format_result(resume)
        except httpx.RequestError as error:
            print(f"Request error in fetch_check_value: {error}")
            raise BotProposalInfoException(f"Error fetching data: {str(error)}")
        except Exception as e:
            print(f"Unexpected error in fetch_check_value: {e}")
            raise BotProposalInfoException(f"Unexpected error: {str(e)}")

    async def fetch_pix(self, data, cpf):
        headers = await self.get_auth_headers(data)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.pix_url}?pix_key={cpf}&btn_clicked=true", headers=headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"data": None}
            else:
                raise BotProposalInfoException(response.json())
        except httpx.RequestError:
            raise BotProposalInfoException(response.json())

    async def send_proposal_pix(self, data):
        try:
            headers = await self.get_auth_headers(data)
            cpf = format_cpf(data["contact"]["cpf"])

            simulation_result = await self.simulate_fgts(data)
            common_fields = {
                "contract_balance": simulation_result["contract_balance"],
                "amount_released": simulation_result["amount_released"],
            }

            account_id = await self._send_first_stage(data, headers)
            await self._send_second_stage(data, headers, account_id)
            await self._send_third_stage(data, headers, account_id)

            pix_fields = {
                **common_fields,
                "account_number": data["pix_resume"]["account_number"],
                "account_type": data["pix_resume"]["account_type"],
                "bank_id": data["pix_resume"]["bank_id"],
                "branch_number": data["pix_resume"]["branch_code"],
                "input_type": "pix",
                "account_created_at": data["pix_resume"]["account_created_at"],
            }
            await self._send_pix_stage(pix_fields, headers, account_id, cpf)

            proposal = await self._send_last_stage(pix_fields, headers, account_id)
            url = await self.get_formalization_url(
                data, proposal["proposal_identifier"]
            )

            return {"resume": proposal["proposal_number"], "formalization_url": url}
        except httpx.RequestError as e:
            traceback.print_exc()
            raise BotProposalInfoException(str(e))

    async def send_proposal_cc(self, data):
        try:
            headers = await self.get_auth_headers(data)

            simulation_result = await self.simulate_fgts(data)
            common_fields = {
                "contract_balance": simulation_result["contract_balance"],
                "amount_released": simulation_result["amount_released"],
            }

            account_id = await self._send_first_stage(data, headers)
            await self._send_second_stage(data, headers, account_id)
            await self._send_third_stage(data, headers, account_id)

            bank_account_fields = {
                **common_fields,
                **data["bank_account_info"],
                "input_type": "manual",
            }
            await self._send_bank_account_stage(
                bank_account_fields, headers, account_id
            )

            proposal = await self._send_last_stage(
                bank_account_fields, headers, account_id
            )
            url = await self.get_formalization_url(
                data, proposal["proposal_identifier"]
            )

            return {"resume": proposal["proposal_number"], "formalization_url": url}
        except httpx.RequestError as e:
            traceback.print_exc()
            raise BotProposalInfoException(str(e))

    async def _send_first_stage(self, data, headers):
        first_stage = {
            "birthdate": format_date(data["contact"]["birthdate"]),
            "document": format_cpf(data["contact"]["cpf"]),
            "email": "falecom@bancoprata.com.br",
            "gender": ("Masculino" if data["contact"]["gender"] == "M" else "Feminino"),
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
            "document_issued_at": format_date(data["contact"]["document_issue_date"]),
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

    async def _send_bank_account_stage(self, bank_account_info, headers, account_id):
        bank_account_stage = {
            "account_created_at": "",
            "account_id": account_id,
            "account_number": bank_account_info["account_number"],
            "account_type": bank_account_info["account_type"],
            "bank_id": bank_account_info["bank_id"],
            "branch_number": bank_account_info["branch_number"],
            "input_type": bank_account_info["input_type"],
        }
        await self._send_request(self.fourth_stage, headers, bank_account_stage)

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
            response = await self._make_request(
                "POST", url, json=data, headers=headers, timeout=10
            )
            return response.json()
        except BotProposalInfoException as error:
            traceback.print_exc()
            raise BotProposalInfoException(str(error))

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
            headers = await self.get_auth_headers(data)
            url = f"{self.formalization_url}{proposal_id}"

            response = await self._make_request("GET", url, headers=headers)
            formalization = response.json()
            return f"https://assina.bancoprata.com.br/validacao/{formalization['data']['token']}"

        except BotProposalInfoException as e:
            if "404" in str(e):
                return {
                    "status": "Not Found",
                    "message": "Ainda não foi possível encontrar o link de formalização, tente novamente mais tarde.",
                }
            else:
                return {
                    "status": "Error",
                    "message": f"Ocorreu um erro ao buscar o link de formalização. Erro: {str(e)}. Por favor, tente novamente mais tarde.",
                }

    # async def _get_pix(self, data, cpf):
    #     headers = await self.get_auth_headers(data)

    #     try:
    #         async with httpx.AsyncClient() as client:
    #             response = await client.get(
    #                 f"{self.pix_url}?pix_key={cpf}&btn_clicked=true", headers=headers
    #             )
    #             response.raise_for_status()
    #             return {"data": response.json()["data"]}
    #     except httpx.HTTPStatusError as e:
    #         error_message = f"HTTP error: {e.response.status_code}"
    #         try:
    #             error_data = e.response.json()
    #             if isinstance(error_data, dict) and "error" in error_data:
    #                 error_message = error_data["error"].get("message", error_message)
    #         except json.JSONDecodeError:
    #             error_message += f" - Response: {e.response.text}"
    #         raise BotProposalInfoException(error_message)
    #     except httpx.RequestError as error:
    #         raise BotProposalInfoException(f"Request error: {str(error)}")
    #     except Exception as e:
    #         raise BotProposalInfoException(f"Unexpected error: {str(e)}")
