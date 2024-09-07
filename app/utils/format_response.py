from typing import Dict, Any
from decimal import Decimal


def format_monthly_rate(rate: Decimal) -> str:
    return f"{rate * 100:.2f}"


def format_result(result: Dict[str, Any]) -> Dict[str, Decimal]:
    try:
        data = result["data"]
        return {
            "amount_released": data["disbursed_issue_amount"],
            "contract_balance": data["assignment_amount"],
            "iof": data["iof_amount"],
            "tac": data["tac"],
            "monthly_rate": float(format_monthly_rate(data["monthly_rate"])),
        }
    except KeyError as error:
        raise KeyError(f"Campo obrigatório ausente no resultado {error}")
    except ValueError as error:
        raise ValueError(f"Erro ao converter valor: {error}")
