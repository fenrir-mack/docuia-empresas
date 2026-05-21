import random
from typing import List
from domain.entities.empresa import Empresa, Membro, Solicitacao, Papel
from domain.ports.empresa_repository import (
    IEmpresaRepository, IMembroRepository, ISolicitacaoRepository, IPapelRepository
)


class ListarEmpresasUseCase:
    """Retorna todas as empresas em que o usuário é membro."""

    def __init__(self, repo: IEmpresaRepository):
        self.repo = repo

    def executar(self, usuario_id: int) -> List[Empresa]:
        return self.repo.listar_por_usuario(usuario_id)


class CriarEmpresaUseCase:
    """Cria uma nova empresa e adiciona o criador como owner."""

    def __init__(self, repo: IEmpresaRepository, membro_repo: IMembroRepository, papel_repo: IPapelRepository = None):
        self.papel_repo = papel_repo
        self.repo = repo
        self.membro_repo = membro_repo

    def executar(self, nome: str, descricao: str, usuario_id: int) -> Empresa:
        cor = random.choice(['teal', 'rose', 'amber', 'indigo', 'emerald', 'cyan'])
        empresa = Empresa(id=None, nome=nome, descricao=descricao, dono_id=usuario_id, cor=cor)
        empresa = self.repo.salvar(empresa)

        # Criador vira owner automaticamente
        membro = Membro(id=None, empresa_id=empresa.id, usuario_id=usuario_id, role="owner")
        self.membro_repo.adicionar(membro)

        if hasattr(self, 'papel_repo') and self.papel_repo:
            self.papel_repo.salvar(Papel(None, empresa.id, "Owner", "Controle total da empresa", "gerenciar_membros,editar_configuracoes,excluir_empresa"))
            self.papel_repo.salvar(Papel(None, empresa.id, "Admin", "Pode gerenciar projetos e membros", "gerenciar_membros,editar_configuracoes"))
            self.papel_repo.salvar(Papel(None, empresa.id, "Member", "Acesso básico à empresa", "ver_projetos,participar_projetos,criar_projetos"))

        return empresa


class EditarEmpresaUseCase:
    """Edita nome e descrição de uma empresa (apenas owner/admin)."""

    def __init__(self, repo: IEmpresaRepository, membro_repo: IMembroRepository):
        self.repo = repo
        self.membro_repo = membro_repo

    def executar(self, empresa_id: int, nome: str, descricao: str, usuario_id: int) -> Empresa:
        empresa = self.repo.buscar_por_id(empresa_id)
        if not empresa:
            raise ValueError("Empresa não encontrada")
        
        membro = self.membro_repo.buscar(empresa_id, usuario_id)
        if empresa.dono_id != usuario_id and (not membro or membro.role not in ('owner', 'admin')):
            raise PermissionError("Acesso negado: Você não possui permissão para realizar esta ação.")

        empresa.nome = nome
        empresa.descricao = descricao
        return self.repo.atualizar(empresa)


class DeletarEmpresaUseCase:
    """Remove uma empresa (apenas owner)."""

    def __init__(self, repo: IEmpresaRepository):
        self.repo = repo

    def executar(self, empresa_id: int, usuario_id: int) -> None:
        empresa = self.repo.buscar_por_id(empresa_id)
        if not empresa:
            raise ValueError("Empresa não encontrada")
        if empresa.dono_id != usuario_id:
            raise PermissionError("Acesso negado: Você não possui permissão para realizar esta ação.")
        empresa.status = "arquivado"
        self.repo.atualizar(empresa)


class ListarMembrosUseCase:
    """Lista todos os membros de uma empresa."""

    def __init__(self, membro_repo: IMembroRepository):
        self.membro_repo = membro_repo

    def executar(self, empresa_id: int) -> List[Membro]:
        return self.membro_repo.listar_por_empresa(empresa_id)


class RemoverMembroUseCase:
    """Remove um membro da empresa (apenas owner/admin)."""

    def __init__(self, membro_repo: IMembroRepository, empresa_repo: IEmpresaRepository):
        self.membro_repo = membro_repo
        self.empresa_repo = empresa_repo

    def executar(self, empresa_id: int, usuario_id_alvo: int, usuario_id_solicitante: int) -> None:
        empresa = self.empresa_repo.buscar_por_id(empresa_id)
        solicitante_membro = self.membro_repo.buscar(empresa_id, usuario_id_solicitante)
        if empresa.dono_id != usuario_id_solicitante and (not solicitante_membro or solicitante_membro.role not in ('owner', 'admin')):
            raise PermissionError("Acesso negado: Você não possui permissão para realizar esta ação.")
            
        if empresa.dono_id == usuario_id_alvo:
            raise PermissionError("Acesso negado: Não é possível remover o dono da empresa.")
        self.membro_repo.remover(empresa_id, usuario_id_alvo)


class SolicitarAcessoUseCase:
    """Usuário solicita entrada em uma empresa."""

    def __init__(self, solicitacao_repo: ISolicitacaoRepository, membro_repo: IMembroRepository):
        self.solicitacao_repo = solicitacao_repo
        self.membro_repo = membro_repo

    def executar(self, empresa_id: int, usuario_id: int) -> Solicitacao:
        ja_membro = self.membro_repo.buscar(empresa_id, usuario_id)
        if ja_membro:
            raise ValueError("Você já é membro desta empresa")

        solicitacao = Solicitacao(id=None, empresa_id=empresa_id, usuario_id=usuario_id)
        return self.solicitacao_repo.salvar(solicitacao)


class GerenciarSolicitacaoUseCase:
    """Owner aprova ou recusa uma solicitação de acesso."""

    def __init__(
        self,
        solicitacao_repo: ISolicitacaoRepository,
        membro_repo: IMembroRepository,
        empresa_repo: IEmpresaRepository
    ):
        self.solicitacao_repo = solicitacao_repo
        self.membro_repo = membro_repo
        self.empresa_repo = empresa_repo

    def executar(self, solicitacao_id: int, acao: str, usuario_id_solicitante: int) -> Solicitacao:
        if acao not in ("aprovada", "recusada"):
            raise ValueError("Ação inválida. Use 'aprovada' ou 'recusada'")

        solicitacao = self.solicitacao_repo.buscar_por_id(solicitacao_id)
        if not solicitacao:
            raise ValueError("Solicitação não encontrada")

        empresa = self.empresa_repo.buscar_por_id(solicitacao.empresa_id)
        solicitante_membro = self.membro_repo.buscar(solicitacao.empresa_id, usuario_id_solicitante)
        if empresa.dono_id != usuario_id_solicitante and (not solicitante_membro or solicitante_membro.role not in ('owner', 'admin')):
            raise PermissionError("Acesso negado: Você não possui permissão para realizar esta ação.")

        solicitacao = self.solicitacao_repo.atualizar_status(solicitacao_id, acao)

        if acao == "aprovada":
            membro = Membro(
                id=None,
                empresa_id=solicitacao.empresa_id,
                usuario_id=solicitacao.usuario_id,
                role="member"
            )
            self.membro_repo.adicionar(membro)

        return solicitacao


class AlterarRoleMembroUseCase:
    """Altera o role de um membro (apenas owner)."""

    def __init__(self, membro_repo: IMembroRepository, empresa_repo: IEmpresaRepository):
        self.membro_repo = membro_repo
        self.empresa_repo = empresa_repo

    def executar(self, empresa_id: int, usuario_id_alvo: int, novo_role: str, usuario_id_solicitante: int) -> Membro:
        if novo_role not in ("owner", "admin", "member"):
            raise ValueError("Role inválido")

        empresa = self.empresa_repo.buscar_por_id(empresa_id)
        if not empresa:
            raise ValueError("Empresa não encontrada")

        solicitante_membro = self.membro_repo.buscar(empresa_id, usuario_id_solicitante)
        is_owner = (empresa.dono_id == usuario_id_solicitante)
        is_admin = (solicitante_membro and solicitante_membro.role == 'admin')

        if not is_owner and not is_admin:
            raise PermissionError("Acesso negado: Você não possui permissão para realizar esta ação.")

        if is_admin and not is_owner and novo_role == 'owner':
            raise PermissionError("Acesso negado: Apenas o dono pode conceder privilégios de Owner.")

        if empresa.dono_id == usuario_id_alvo:
            raise PermissionError("Acesso negado: Não é possível alterar o cargo do dono da empresa.")

        membro_alvo = self.membro_repo.buscar(empresa_id, usuario_id_alvo)
        if not membro_alvo:
            raise ValueError("Membro não encontrado")

        # Atualizando a entidade (precisa de db.commit no repository se formos usar atualizar, mas o repo atual não tem atualizar_membro)
        # Como o MemberRepositoryImpl não tem método "atualizar", vou deletar e adicionar para recriar com a nova role
        self.membro_repo.remover(empresa_id, usuario_id_alvo)
        membro_alvo.id = None # para criar um novo id
        membro_alvo.role = novo_role
        return self.membro_repo.adicionar(membro_alvo)


class ListarPapeisUseCase:
    def __init__(self, repo: IPapelRepository):
        self.repo = repo
    def executar(self, empresa_id: int) -> List[Papel]:
        return self.repo.listar_por_empresa(empresa_id)

class CriarPapelUseCase:
    def __init__(self, repo: IPapelRepository):
        self.repo = repo
    def executar(self, empresa_id: int, nome: str, descricao: str, permissoes: str) -> Papel:
        papel = Papel(id=None, empresa_id=empresa_id, nome=nome, descricao=descricao, permissoes=permissoes)
        return self.repo.salvar(papel)

class EditarPapelUseCase:
    def __init__(self, repo: IPapelRepository):
        self.repo = repo
    def executar(self, papel_id: int, nome: str, descricao: str, permissoes: str) -> Papel:
        papel = self.repo.buscar_por_id(papel_id)
        if not papel: raise ValueError("Papel não encontrado")
        papel.nome = nome
        papel.descricao = descricao
        papel.permissoes = permissoes
        return self.repo.salvar(papel)

class DeletarPapelUseCase:
    def __init__(self, repo: IPapelRepository):
        self.repo = repo
    def executar(self, papel_id: int) -> None:
        self.repo.deletar(papel_id)
