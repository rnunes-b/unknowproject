from typing import Dict, Optional
import re


def extract_max_value(
    result: Dict[str, Dict[str, str]], currency_symbol: str = "R$"
) -> Optional[float]:
    try:
        message = result["error"]["message"]
        pattern = rf"{re.escape(currency_symbol)}\s*([\d.,]+)"
        matches = re.findall(pattern, message)

        if matches:
            max_value_str = matches[-1]
            max_value_str = max_value_str.replace(".", "").replace(",", ".")
            return float(max_value_str)
    except (KeyError, ValueError, AttributeError) as e:
        print(f"Erro ao extrair o valor: {e}")
        pass
    return None
