import os
import re
import shutil
from datetime import datetime
from typing import Optional

from config import log


def normalizar_nome_pasta(nome: str) -> str:
    """Normaliza nome de pasta removendo caracteres invalidos no Windows."""
    nome = (nome or "").strip()
    nome = re.sub(r'[\\/:*?"<>|]+', '-', nome)
    nome = re.sub(r'\s+', '_', nome)
    return nome.strip('._-') or "sessao"


def criar_pasta_sessao(base_dir: str, nome_sessao: str) -> str:
    """Cria pasta unica para sessao de inventario."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_final = f"{normalizar_nome_pasta(nome_sessao)}_{ts}"
    pasta = os.path.join(base_dir, nome_final)
    os.makedirs(pasta, exist_ok=True)
    log("SESSAO_CRIADA", f"pasta={pasta}")
    return pasta


def sincronizar_sessao_nuvem(pasta_sessao: str, pasta_nuvem: Optional[str]) -> Optional[str]:
    """Sincroniza pasta da sessao para a pasta de nuvem configurada."""
    if not pasta_nuvem:
        return None

    pasta_nuvem = pasta_nuvem.strip()
    if not pasta_nuvem:
        return None

    if not os.path.isdir(pasta_sessao):
        return None

    destino = os.path.join(pasta_nuvem, os.path.basename(pasta_sessao))
    os.makedirs(destino, exist_ok=True)

    for nome in os.listdir(pasta_sessao):
        origem_arquivo = os.path.join(pasta_sessao, nome)
        destino_arquivo = os.path.join(destino, nome)

        if os.path.isfile(origem_arquivo):
            shutil.copy2(origem_arquivo, destino_arquivo)

    log("SYNC_NUVEM", f"origem={pasta_sessao} destino={destino}")
    return destino
