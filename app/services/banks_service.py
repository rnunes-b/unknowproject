import json
from typing import List, Optional
from app.models import Bank
import os
from functools import lru_cache

class BankService:
    def __init__(self, file_path: str = "banks.json"):
        self.file_path = os.path.join(os.path.dirname(__file__), file_path)
        self.banks = self._load_banks()

    @lru_cache(maxsize=1)
    def _load_banks(self) -> List[Bank]:
        with open(self.file_path, 'r', encoding='utf-8') as file:
            banks_data = json.load(file)
        return [Bank(**bank) for bank in banks_data]

    def search_bank(self, query: str) -> Optional[Bank]:
        query = query.lower()
        for bank in self.banks:
            if bank.code == query or query in bank.name.lower():
                return bank
        return None

    def list_all_banks(self) -> List[Bank]:
        return self.banks