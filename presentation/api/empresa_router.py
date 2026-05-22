from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

from infrastructure.database.conexao import get_db
from infrastructure.database.models import AcessoEmpresaModel, EmpresaModel
from infrastructure.database.empresa_repository_impl import (
    EmpresaRepositoryImpl, MembroRepositoryImpl, SolicitacaoRepositoryImpl, PapelRepositoryImpl
)
from application.use_cases.empresa_use_cases import (
    ListarPapeisUseCase, CriarPapelUseCase, EditarPapelUseCase, DeletarPapelUseCase,
    ListarEmpresasUseCase, CriarEmpresaUseCase, EditarEmpresaUseCase,
    DeletarEmpresaUseCase, ListarMembrosUseCase, RemoverMembroUseCase,
    SolicitarAcessoUseCase, GerenciarSolicitacaoUseCase, AlterarRoleMembroUseCase
)

router = APIRouter(prefix="/empresas", tags=["Empresas"])
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "docuia-secret-dev")


def get_usuario_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


# --- Schemas ---

class EmpresaInput(BaseModel):
    nome: str
    descricao: str = ""

class SolicitacaoAcaoInput(BaseModel):
    acao: str  # "aprovada" ou "recusada"


# --- Endpoints ---

@router.get("")
def listar_empresas(usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = EmpresaRepositoryImpl(db)
    empresas = ListarEmpresasUseCase(repo).executar(usuario_id)
    return [{"id": e.id, "nome": e.nome, "descricao": e.descricao, "dono_id": e.dono_id, "cor": e.cor} for e in empresas]


@router.post("/{empresa_id:int}/acessos", status_code=204)
def registrar_acesso_empresa(empresa_id: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    existing = (
        db.query(AcessoEmpresaModel)
        .filter(AcessoEmpresaModel.empresa_id == empresa_id, AcessoEmpresaModel.usuario_id == usuario_id)
        .first()
    )
    now = datetime.utcnow()
    if existing:
        existing.ultimo_acesso_em = now
    else:
        db.add(AcessoEmpresaModel(empresa_id=empresa_id, usuario_id=usuario_id, ultimo_acesso_em=now))
    db.commit()


@router.get("/recentes")
def listar_empresas_recentes(limit: int = 6, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    limit = max(1, min(int(limit), 50))
    rows = (
        db.query(EmpresaModel, AcessoEmpresaModel.ultimo_acesso_em)
        .join(AcessoEmpresaModel, AcessoEmpresaModel.empresa_id == EmpresaModel.id)
        .filter(AcessoEmpresaModel.usuario_id == usuario_id)
        .order_by(AcessoEmpresaModel.ultimo_acesso_em.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "nome": e.nome,
            "descricao": e.descricao,
            "dono_id": e.dono_id,
            "cor": e.cor,
            "ultimo_acesso_em": ts.isoformat() if ts else None,
        }
        for (e, ts) in rows
    ]

@router.post("", status_code=201)
def criar_empresa(dados: EmpresaInput, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = EmpresaRepositoryImpl(db)
    membro_repo = MembroRepositoryImpl(db)
    papel_repo = PapelRepositoryImpl(db)
    empresa = CriarEmpresaUseCase(repo, membro_repo, papel_repo).executar(dados.nome, dados.descricao, usuario_id)
    return {"id": empresa.id, "nome": empresa.nome, "cor": empresa.cor}


@router.get("/{empresa_id:int}")
def detalhe_empresa(empresa_id: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = EmpresaRepositoryImpl(db)
    empresa = repo.buscar_por_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"id": empresa.id, "nome": empresa.nome, "descricao": empresa.descricao, "dono_id": empresa.dono_id, "cor": empresa.cor}


@router.put("/{empresa_id:int}")
def editar_empresa(empresa_id: int, dados: EmpresaInput, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = EmpresaRepositoryImpl(db)
    membro_repo = MembroRepositoryImpl(db)
    try:
        empresa = EditarEmpresaUseCase(repo, membro_repo).executar(empresa_id, dados.nome, dados.descricao, usuario_id)
        return {"id": empresa.id, "nome": empresa.nome, "cor": empresa.cor}
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{empresa_id:int}", status_code=204)
def deletar_empresa(empresa_id: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = EmpresaRepositoryImpl(db)
    try:
        DeletarEmpresaUseCase(repo).executar(empresa_id, usuario_id)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{empresa_id:int}/membros")
def listar_membros(empresa_id: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    membro_repo = MembroRepositoryImpl(db)
    membros = ListarMembrosUseCase(membro_repo).executar(empresa_id)
    return [{"id": m.id, "usuario_id": m.usuario_id, "role": m.role} for m in membros]


@router.delete("/{empresa_id:int}/membros/{usuario_id_alvo:int}", status_code=204)
def remover_membro(empresa_id: int, usuario_id_alvo: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    membro_repo = MembroRepositoryImpl(db)
    empresa_repo = EmpresaRepositoryImpl(db)
    try:
        RemoverMembroUseCase(membro_repo, empresa_repo).executar(empresa_id, usuario_id_alvo, usuario_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

class AlterarRoleInput(BaseModel):
    role: str

@router.put("/{empresa_id:int}/membros/{usuario_id_alvo:int}/role")
def alterar_role_membro(empresa_id: int, usuario_id_alvo: int, dados: AlterarRoleInput, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    membro_repo = MembroRepositoryImpl(db)
    empresa_repo = EmpresaRepositoryImpl(db)
    try:
        membro = AlterarRoleMembroUseCase(membro_repo, empresa_repo).executar(empresa_id, usuario_id_alvo, dados.role, usuario_id)
        return {"id": membro.id, "usuario_id": membro.usuario_id, "role": membro.role}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{empresa_id:int}/solicitacoes")
def listar_solicitacoes(empresa_id: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    sol_repo = SolicitacaoRepositoryImpl(db)
    solicitacoes = sol_repo.listar_por_empresa(empresa_id)
    return [{"id": s.id, "usuario_id": s.usuario_id, "status": s.status} for s in solicitacoes]


@router.post("/{empresa_id:int}/solicitacoes", status_code=201)
def solicitar_acesso(empresa_id: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    sol_repo = SolicitacaoRepositoryImpl(db)
    membro_repo = MembroRepositoryImpl(db)
    try:
        sol = SolicitarAcessoUseCase(sol_repo, membro_repo).executar(empresa_id, usuario_id)
        return {"id": sol.id, "status": sol.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{empresa_id:int}/solicitacoes/{solicitacao_id:int}")
def gerenciar_solicitacao(empresa_id: int, solicitacao_id: int, dados: SolicitacaoAcaoInput, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    sol_repo = SolicitacaoRepositoryImpl(db)
    membro_repo = MembroRepositoryImpl(db)
    empresa_repo = EmpresaRepositoryImpl(db)
    try:
        sol = GerenciarSolicitacaoUseCase(sol_repo, membro_repo, empresa_repo).executar(
            solicitacao_id, dados.acao, usuario_id
        )
        return {"id": sol.id, "status": sol.status}
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=403, detail=str(e))


class PapelInput(BaseModel):
    nome: str
    descricao: str = ""
    permissoes: str = ""

@router.get("/{empresa_id:int}/papeis")
def listar_papeis(empresa_id: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = PapelRepositoryImpl(db)
    papeis = ListarPapeisUseCase(repo).executar(empresa_id)
    return [{"id": p.id, "nome": p.nome, "descricao": p.descricao, "permissoes": p.permissoes} for p in papeis]

@router.post("/{empresa_id:int}/papeis", status_code=201)
def criar_papel(empresa_id: int, dados: PapelInput, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = PapelRepositoryImpl(db)
    papel = CriarPapelUseCase(repo).executar(empresa_id, dados.nome, dados.descricao, dados.permissoes)
    return {"id": papel.id, "nome": papel.nome, "descricao": papel.descricao, "permissoes": papel.permissoes}

@router.put("/{empresa_id:int}/papeis/{papel_id:int}")
def editar_papel(empresa_id: int, papel_id: int, dados: PapelInput, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = PapelRepositoryImpl(db)
    try:
        papel = EditarPapelUseCase(repo).executar(papel_id, dados.nome, dados.descricao, dados.permissoes)
        return {"id": papel.id, "nome": papel.nome, "descricao": papel.descricao, "permissoes": papel.permissoes}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{empresa_id:int}/papeis/{papel_id:int}", status_code=204)
def deletar_papel(empresa_id: int, papel_id: int, usuario_id: int = Depends(get_usuario_id), db: Session = Depends(get_db)):
    repo = PapelRepositoryImpl(db)
    DeletarPapelUseCase(repo).executar(papel_id)
