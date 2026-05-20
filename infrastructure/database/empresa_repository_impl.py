from typing import List, Optional
from sqlalchemy.orm import Session

from domain.entities.empresa import Empresa, Membro, Solicitacao, Papel
from domain.ports.empresa_repository import (
    IEmpresaRepository, IMembroRepository, ISolicitacaoRepository, IPapelRepository
)
from infrastructure.database.models import EmpresaModel, MembroModel, SolicitacaoModel, PapelModel


class EmpresaRepositoryImpl(IEmpresaRepository):

    def __init__(self, db: Session):
        self.db = db

    def _para_entidade(self, m: EmpresaModel) -> Empresa:
        return Empresa(id=m.id, nome=m.nome, descricao=m.descricao,
                       dono_id=m.dono_id, status=m.status, criado_em=m.criado_em, cor=getattr(m, 'cor', 'indigo'))

    def salvar(self, empresa: Empresa) -> Empresa:
        model = EmpresaModel(nome=empresa.nome, descricao=empresa.descricao, dono_id=empresa.dono_id, status=empresa.status, cor=empresa.cor)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._para_entidade(model)

    def buscar_por_id(self, id: int) -> Optional[Empresa]:
        model = self.db.query(EmpresaModel).filter(EmpresaModel.id == id).first()
        return self._para_entidade(model) if model else None

    def listar_por_usuario(self, usuario_id: int) -> List[Empresa]:
        # Retorna empresas onde o usuário é membro
        membros = self.db.query(MembroModel).filter(MembroModel.usuario_id == usuario_id).all()
        empresa_ids = [m.empresa_id for m in membros]
        models = self.db.query(EmpresaModel).filter(EmpresaModel.id.in_(empresa_ids), EmpresaModel.status != "arquivado").all()
        return [self._para_entidade(m) for m in models]

    def atualizar(self, empresa: Empresa) -> Empresa:
        model = self.db.query(EmpresaModel).filter(EmpresaModel.id == empresa.id).first()
        model.nome = empresa.nome
        model.descricao = empresa.descricao
        model.status = empresa.status
        self.db.commit()
        self.db.refresh(model)
        return self._para_entidade(model)

    def deletar(self, id: int) -> None:
        model = self.db.query(EmpresaModel).filter(EmpresaModel.id == id).first()
        self.db.delete(model)
        self.db.commit()


class MembroRepositoryImpl(IMembroRepository):

    def __init__(self, db: Session):
        self.db = db

    def _para_entidade(self, m: MembroModel) -> Membro:
        return Membro(id=m.id, empresa_id=m.empresa_id,
                      usuario_id=m.usuario_id, role=m.role, criado_em=m.criado_em)

    def adicionar(self, membro: Membro) -> Membro:
        model = MembroModel(empresa_id=membro.empresa_id,
                            usuario_id=membro.usuario_id, role=membro.role)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._para_entidade(model)

    def listar_por_empresa(self, empresa_id: int) -> List[Membro]:
        models = self.db.query(MembroModel).filter(MembroModel.empresa_id == empresa_id).all()
        return [self._para_entidade(m) for m in models]

    def buscar(self, empresa_id: int, usuario_id: int) -> Optional[Membro]:
        model = self.db.query(MembroModel).filter(
            MembroModel.empresa_id == empresa_id,
            MembroModel.usuario_id == usuario_id
        ).first()
        return self._para_entidade(model) if model else None

    def remover(self, empresa_id: int, usuario_id: int) -> None:
        model = self.db.query(MembroModel).filter(
            MembroModel.empresa_id == empresa_id,
            MembroModel.usuario_id == usuario_id
        ).first()
        if model:
            self.db.delete(model)
            self.db.commit()


class SolicitacaoRepositoryImpl(ISolicitacaoRepository):

    def __init__(self, db: Session):
        self.db = db

    def _para_entidade(self, m: SolicitacaoModel) -> Solicitacao:
        return Solicitacao(id=m.id, empresa_id=m.empresa_id,
                           usuario_id=m.usuario_id, status=m.status, criado_em=m.criado_em)

    def salvar(self, solicitacao: Solicitacao) -> Solicitacao:
        model = SolicitacaoModel(empresa_id=solicitacao.empresa_id,
                                 usuario_id=solicitacao.usuario_id)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._para_entidade(model)

    def listar_por_empresa(self, empresa_id: int) -> List[Solicitacao]:
        models = self.db.query(SolicitacaoModel).filter(
            SolicitacaoModel.empresa_id == empresa_id
        ).all()
        return [self._para_entidade(m) for m in models]

    def buscar_por_id(self, id: int) -> Optional[Solicitacao]:
        model = self.db.query(SolicitacaoModel).filter(SolicitacaoModel.id == id).first()
        return self._para_entidade(model) if model else None

    def atualizar_status(self, id: int, status: str) -> Solicitacao:
        model = self.db.query(SolicitacaoModel).filter(SolicitacaoModel.id == id).first()
        model.status = status
        self.db.commit()
        self.db.refresh(model)
        return self._para_entidade(model)


class PapelRepositoryImpl(IPapelRepository):
    def __init__(self, db: Session):
        self.db = db

    def _para_entidade(self, m: PapelModel) -> Papel:
        return Papel(id=m.id, empresa_id=m.empresa_id, nome=m.nome, descricao=m.descricao, permissoes=m.permissoes)

    def listar_por_empresa(self, empresa_id: int) -> List[Papel]:
        models = self.db.query(PapelModel).filter(PapelModel.empresa_id == empresa_id).all()
        return [self._para_entidade(m) for m in models]

    def buscar_por_id(self, id: int) -> Optional[Papel]:
        model = self.db.query(PapelModel).filter(PapelModel.id == id).first()
        return self._para_entidade(model) if model else None

    def salvar(self, papel: Papel) -> Papel:
        if papel.id:
            model = self.db.query(PapelModel).filter(PapelModel.id == papel.id).first()
            model.nome = papel.nome
            model.descricao = papel.descricao
            model.permissoes = papel.permissoes
        else:
            model = PapelModel(empresa_id=papel.empresa_id, nome=papel.nome, descricao=papel.descricao, permissoes=papel.permissoes)
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._para_entidade(model)

    def deletar(self, id: int) -> None:
        model = self.db.query(PapelModel).filter(PapelModel.id == id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
