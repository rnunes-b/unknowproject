from fastapi import FastAPI
from app.routers import router
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

app.include_router(router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "FastAPI está rodando!"}
