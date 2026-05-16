from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.api.empresa_router import router as empresa_router
from infrastructure.database.conexao import engine
from infrastructure.database.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DocuIA — MS2 Empresas",
    description="Microserviço responsável por empresas, membros e solicitações de acesso",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://docuia-frontend-hdc8hzfqbqebc6cp.brazilsouth-01.azurewebsites.net",
        "http://localhost:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(empresa_router)


@app.get("/")
def health_check():
    return {"status": "ok", "servico": "ms2_empresas"}
