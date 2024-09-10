import httpx
from app.exceptions import APIException

class ViaCEPService:
    def __init__(self):
        self.base_url = "https://viacep.com.br/ws"

    async def get_address(self, cep: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/{cep}/json/")
                response.raise_for_status()
                data = response.json()

                if "erro" in data:
                    raise APIException("CEP não encontrado", status_code=404, error_type="NotFoundError")

                return {
                    "city": data["localidade"],
                    "neighborhood": data["bairro"],
                    "state": data["uf"],
                    "street": data["logradouro"],
                    "zipcode": data["cep"],
                    "complement": data["complemento"],
                }

        except httpx.HTTPStatusError as e:
            raise APIException(f"Erro ao buscar CEP: {str(e)}", status_code=e.response.status_code, error_type="HTTPError")
        except httpx.RequestError as e:
            raise APIException(f"Erro de conexão ao buscar CEP: {str(e)}", status_code=503, error_type="ConnectionError")
