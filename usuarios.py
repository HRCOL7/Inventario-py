# ===============================
# IKARUS INVENTORY - Gerenciamento de Usuários
# ===============================

import os
import json
import hashlib
from typing import Optional
from config import ARQUIVO_USUARIOS, log

def carregar_usuarios():
    """Carrega lista de usuários do JSON"""
    if not os.path.exists(ARQUIVO_USUARIOS):
        return []
    with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    """Salva lista de usuários no JSON"""
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def hash_senha(senha: str) -> str:
    """Gera hash SHA256 da senha"""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def cadastrar_usuario(usuario, senha):
    """Cadastra novo usuário. Retorna True se sucesso, False se já existe"""
    usuarios = carregar_usuarios()
    if any(u["usuario"] == usuario for u in usuarios):
        return False
    usuarios.append({"usuario": usuario, "senha": hash_senha(senha), "senha_original": senha})
    salvar_usuarios(usuarios)
    log("CADASTRO_OK", f"usuario={usuario}")
    return True

def autenticar(usuario, senha):
    """Autentica usuário. Retorna True se credenciais válidas"""
    usuarios = carregar_usuarios()
    senha_hash = hash_senha(senha)
    for u in usuarios:
        if u["usuario"] == usuario and u["senha"] == senha_hash:
            return True
    return False

def alterar_senha(usuario, senha_atual, nova_senha):
    """Altera senha do usuário. Retorna True se sucesso"""
    if not autenticar(usuario, senha_atual):
        return False
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u["usuario"] == usuario:
            u["senha"] = hash_senha(nova_senha)
            u["senha_original"] = nova_senha
    salvar_usuarios(usuarios)
    log("ALTERAR_SENHA", f"usuario={usuario}")
    return True

def excluir_usuario(usuario):
    """Exclui usuário do cadastro"""
    if usuario == "admin":
        return False
    usuarios = carregar_usuarios()
    novos = [u for u in usuarios if u["usuario"] != usuario]
    salvar_usuarios(novos)
    log("EXCLUIR_USUARIO", f"usuario={usuario}")
    return True

def obter_usuarios():
    """Retorna lista de nomes de usuários"""
    return [u["usuario"] for u in carregar_usuarios()]

def obter_senhas():
    """Retorna dicionário com usuários e senhas"""
    usuarios = carregar_usuarios()
    return {u["usuario"]: u.get("senha_original", "(não disponível)") for u in usuarios}
