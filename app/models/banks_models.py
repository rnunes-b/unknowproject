from pydantic import BaseModel

class Bank(BaseModel):
    id: int
    code: str
    ispb: str
    name: str
    digital: int
    only_commission: int
    