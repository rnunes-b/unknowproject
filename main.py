
from fastapi import FastAPI
from app.routers.prata_api_router import router as prata_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FGTS API",
    description="API para consulta de saldo FGTS e status",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prata_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "rodando!"}