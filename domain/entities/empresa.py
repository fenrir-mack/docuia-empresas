from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Empresa:
    id: Optional[int]
    nome: str
    descricao: str
    dono_id: int
    cor: str = "indigo"
    status: str = "ativo"
    criado_em: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Membro:
    id: Optional[int]
    empresa_id: int
    usuario_id: int
    role: str  # "owner", "admin", "member"
    criado_em: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Solicitacao:
    id: Optional[int]
    empresa_id: int
    usuario_id: int
    status: str = "pendente"  # "pendente", "aprovada", "recusada"
    criado_em: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Papel:
    id: Optional[int]
    empresa_id: int
    nome: str
    descricao: str
    permissoes: str
