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
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy import text

app.include_router(empresa_router)


def _ensure_schema():
    # Migração leve (sem Alembic): garante coluna `mensagem` nas solicitações.
    try:
        with engine.connect() as connection:
            has_col = connection.execute(
                text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = 'solicitacoes' AND column_name = 'mensagem'"
                )
            ).first()
            if not has_col:
                connection.execute(text("ALTER TABLE solicitacoes ADD COLUMN mensagem TEXT"))
                connection.commit()
    except Exception:
        # Não quebra o serviço se a checagem falhar (ex: permissões/DB diferente)
        pass


_ensure_schema()


@app.get("/")
def health_check():
    return {"status": "ok", "servico": "ms2_empresas"}

@app.get("/health")
def database_health():
    """Verifica se o banco de dados está acessível."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected", "servico": "ms2_empresas"}
    except Exception as e:
        return {
            "status": "error", 
            "database": "disconnected", 
            "details": str(e),
            "servico": "ms2_empresas"
        }
