from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.empresa import Empresa, Membro, Solicitacao, Papel


class IEmpresaRepository(ABC):
    @abstractmethod
    def salvar(self, empresa: Empresa) -> Empresa: pass

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Empresa]: pass

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int) -> List[Empresa]: pass

    @abstractmethod
    def atualizar(self, empresa: Empresa) -> Empresa: pass

    @abstractmethod
    def deletar(self, id: int) -> None: pass


class IMembroRepository(ABC):
    @abstractmethod
    def adicionar(self, membro: Membro) -> Membro: pass

    @abstractmethod
    def listar_por_empresa(self, empresa_id: int) -> List[Membro]: pass

    @abstractmethod
    def buscar(self, empresa_id: int, usuario_id: int) -> Optional[Membro]: pass

    @abstractmethod
    def remover(self, empresa_id: int, usuario_id: int) -> None: pass


class ISolicitacaoRepository(ABC):
    @abstractmethod
    def salvar(self, solicitacao: Solicitacao) -> Solicitacao: pass

    @abstractmethod
    def listar_por_empresa(self, empresa_id: int) -> List[Solicitacao]: pass

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Solicitacao]: pass

    @abstractmethod
    def atualizar_status(self, id: int, status: str) -> Solicitacao: pass


class IPapelRepository(ABC):
    @abstractmethod
    def listar_por_empresa(self, empresa_id: int) -> List[Papel]: pass
    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Papel]: pass
    @abstractmethod
    def salvar(self, papel: Papel) -> Papel: pass
    @abstractmethod
    def deletar(self, id: int) -> None: pass
