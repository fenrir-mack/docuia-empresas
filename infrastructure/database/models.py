from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class EmpresaModel(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(String(1000), default="")
    dono_id = Column(Integer, nullable=False)
    status = Column(String(50), default="ativo")
    criado_em = Column(DateTime, default=datetime.utcnow)


class MembroModel(Base):
    __tablename__ = "membros"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    usuario_id = Column(Integer, nullable=False)
    role = Column(String(50), default="member")
    criado_em = Column(DateTime, default=datetime.utcnow)


class SolicitacaoModel(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    usuario_id = Column(Integer, nullable=False)
    status = Column(String(50), default="pendente")
    criado_em = Column(DateTime, default=datetime.utcnow)

class PapelModel(Base):
    __tablename__ = "papeis"
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nome = Column(String(50), nullable=False)
    descricao = Column(String(255), default="")
    permissoes = Column(String(1000), default="")
