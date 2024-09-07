import re


def format_cpf(cpf: str) -> str:
    cleaned_cpf = re.sub(r"\D", "", cpf)
    formatted_cpf = (
        f"{cleaned_cpf[:3]}.{cleaned_cpf[3:6]}.{cleaned_cpf[6:9]}-{cleaned_cpf[9:]}"
    )
    return formatted_cpf
