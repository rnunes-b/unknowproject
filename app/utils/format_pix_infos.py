def get_bank_info(data):
    return {
        "cpf": data['data'].get('taxId', 'N/A'),
        "name": data['data'].get('name', 'N/A'),
        "bank_name": data['data'].get('bankName', 'N/A'),
        "bank_id": data['data'].get('bank_id', 'N/A'),
        "branch_code": data['data'].get('branchCode', 'N/A'),
        "account_number": data['data'].get('accountNumber', 'N/A'),
    }

