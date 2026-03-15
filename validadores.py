# ===============================
# IKARUS INVENTORY - Validadores de Entrada
# ===============================

"""
Módulo de validação de dados - garante integridade e segurança
"""

import re
from typing import Tuple, Optional

class ValidadorInventario:
    """Validador centralizado para dados do inventário"""
    
    # Constantes
    TAMANHO_CODIGO_BARRAS = 13
    TAMANHO_CODIGO_INTERNO_MIN = 1
    TAMANHO_CODIGO_INTERNO_MAX = 50
    TAMANHO_NOME_MIN = 2
    TAMANHO_NOME_MAX = 200
    TAMANHO_USUARIO_MIN = 3
    TAMANHO_USUARIO_MAX = 50
    TAMANHO_SENHA_MIN = 4
    TAMANHO_SENHA_MAX = 100
    
    # Padrões regex
    REGEX_CODIGO_BARRAS = r'^\d{13}$'
    REGEX_CODIGO_INTERNO = r'^[A-Za-z0-9\-\_\.]+$'
    REGEX_NOME = r'^[a-zA-Z0-9\s\-\.\,áàâãéèêíïóôõöúçñ]+$'
    REGEX_USUARIO = r'^[a-zA-Z0-9\_\-\.]+$'
    REGEX_GRUPO = r'^[a-zA-Z0-9\s\-\.\,áàâãéèêíïóôõöúçñ]+$'
    
    @staticmethod
    def validar_codigo_barras(codigo: str) -> Tuple[bool, str]:
        """
        Valida código de barras (EAN-13)
        
        Retorna: (válido, mensagem_erro)
        """
        if not codigo:
            return False, "Código de barras não pode estar vazio"
        
        codigo = codigo.strip()
        
        if len(codigo) != ValidadorInventario.TAMANHO_CODIGO_BARRAS:
            return False, f"Código deve ter {ValidadorInventario.TAMANHO_CODIGO_BARRAS} dígitos"
        
        if not codigo.isdigit():
            return False, "Código deve conter apenas números"
        
        if not re.match(ValidadorInventario.REGEX_CODIGO_BARRAS, codigo):
            return False, "Formato de código inválido"
        
        # Validar dígito verificador (algoritmo EAN-13)
        if not ValidadorInventario._validar_ean13(codigo):
            return False, "Dígito verificador inválido (código pode estar corrompido)"
        
        return True, ""
    
    @staticmethod
    def validar_codigo_interno(codigo: str) -> Tuple[bool, str]:
        """Valida código interno do produto"""
        if not codigo:
            return False, "Código interno não pode estar vazio"
        
        codigo = codigo.strip()
        
        if len(codigo) < ValidadorInventario.TAMANHO_CODIGO_INTERNO_MIN:
            return False, f"Código muito curto (mínimo {ValidadorInventario.TAMANHO_CODIGO_INTERNO_MIN})"
        
        if len(codigo) > ValidadorInventario.TAMANHO_CODIGO_INTERNO_MAX:
            return False, f"Código muito longo (máximo {ValidadorInventario.TAMANHO_CODIGO_INTERNO_MAX})"
        
        if not re.match(ValidadorInventario.REGEX_CODIGO_INTERNO, codigo):
            return False, "Caracteres inválidos (use apenas letras, números, -, _, .)"
        
        return True, ""
    
    @staticmethod
    def validar_nome_produto(nome: str) -> Tuple[bool, str]:
        """Valida nome do produto"""
        if not nome:
            return False, "Nome não pode estar vazio"
        
        nome = nome.strip()
        
        if len(nome) < ValidadorInventario.TAMANHO_NOME_MIN:
            return False, f"Nome muito curto (mínimo {ValidadorInventario.TAMANHO_NOME_MIN} caracteres)"
        
        if len(nome) > ValidadorInventario.TAMANHO_NOME_MAX:
            return False, f"Nome muito longo (máximo {ValidadorInventario.TAMANHO_NOME_MAX})"
        
        if not re.match(ValidadorInventario.REGEX_NOME, nome):
            return False, "Caracteres inválidos no nome"
        
        return True, ""
    
    @staticmethod
    def validar_usuario(usuario: str) -> Tuple[bool, str]:
        """Valida nome de usuário"""
        if not usuario:
            return False, "Usuário não pode estar vazio"
        
        usuario = usuario.strip()
        
        if len(usuario) < ValidadorInventario.TAMANHO_USUARIO_MIN:
            return False, f"Usuário muito curto (mínimo {ValidadorInventario.TAMANHO_USUARIO_MIN})"
        
        if len(usuario) > ValidadorInventario.TAMANHO_USUARIO_MAX:
            return False, f"Usuário muito longo (máximo {ValidadorInventario.TAMANHO_USUARIO_MAX})"
        
        if not re.match(ValidadorInventario.REGEX_USUARIO, usuario):
            return False, "Caracteres inválidos (use letras, números, _, -)"
        
        return True, ""
    
    @staticmethod
    def validar_senha(senha: str) -> Tuple[bool, str]:
        """Valida força de senha"""
        if not senha:
            return False, "Senha não pode estar vazia"
        
        if len(senha) < ValidadorInventario.TAMANHO_SENHA_MIN:
            return False, f"Senha muito curta (mínimo {ValidadorInventario.TAMANHO_SENHA_MIN})"
        
        if len(senha) > ValidadorInventario.TAMANHO_SENHA_MAX:
            return False, f"Senha muito longa (máximo {ValidadorInventario.TAMANHO_SENHA_MAX})"
        
        # Validações adicionais de segurança
        has_lower = any(c.islower() for c in senha)
        has_upper = any(c.isupper() for c in senha)
        has_digit = any(c.isdigit() for c in senha)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in senha)
        
        # Recomendação de força
        força = sum([has_lower, has_upper, has_digit, has_special])
        
        if força == 0:
            return False, "Senha deve conter pelo menos 1 caractere"
        
        return True, f"Força: {'Fraca' if força < 2 else 'Média' if força < 3 else 'Forte'}"
    
    @staticmethod
    def validar_quantidade(qtd: int) -> Tuple[bool, str]:
        """Valida quantidade de itens"""
        try:
            qtd_int = int(qtd)
            if qtd_int < 0:
                return False, "Quantidade não pode ser negativa"
            if qtd_int > 999999:
                return False, "Quantidade muito grande"
            return True, ""
        except (ValueError, TypeError):
            return False, "Quantidade deve ser um número"
    
    @staticmethod
    def validar_grupo(grupo: str) -> Tuple[bool, str]:
        """Valida nome do grupo"""
        if not grupo or not grupo.strip():
            return True, ""  # Grupo é opcional
        
        grupo = grupo.strip()
        
        if len(grupo) > 100:
            return False, "Grupo muito longo"
        
        if not re.match(ValidadorInventario.REGEX_GRUPO, grupo):
            return False, "Caracteres inválidos no grupo"
        
        return True, ""
    
    @staticmethod
    def _validar_ean13(codigo: str) -> bool:
        """
        Valida dígito verificador EAN-13
        Retorna True se válido
        """
        if len(codigo) != 13:
            return False
        
        try:
            # Algoritmo EAN-13
            pares = sum(int(codigo[i]) for i in range(1, 13, 2))
            impares = sum(int(codigo[i]) for i in range(0, 12, 2))
            total = pares * 3 + impares
            digito = (10 - (total % 10)) % 10
            
            return int(codigo[12]) == digito
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def sanitizar_entrada(texto: str) -> str:
        """Remove caracteres perigosos de entrada"""
        if not isinstance(texto, str):
            return ""
        
        # Remover espaços extras
        texto = " ".join(texto.split())
        
        # Remover caracteres de controle
        texto = "".join(c for c in texto if ord(c) >= 32 or c in "\n\t")
        
        return texto.strip()
    
    @staticmethod
    def sanitizar_codigo_barras(codigo: str) -> str:
        """Sanitiza código de barras"""
        return "".join(c for c in codigo if c.isdigit())
    
    @staticmethod
    def gerar_relatorio_validacao(dados: dict) -> dict:
        """
        Valida um conjunto de dados de produto
        
        Retorna dict com resultado da validação
        """
        resultado = {
            "válido": True,
            "erros": [],
            "avisos": [],
            "dados": {}
        }
        
        # Validar código de barras
        if "codigo_barras" in dados:
            ok, msg = ValidadorInventario.validar_codigo_barras(dados["codigo_barras"])
            if not ok:
                resultado["válido"] = False
                resultado["erros"].append(f"Código de barras: {msg}")
            resultado["dados"]["codigo_barras"] = ValidadorInventario.sanitizar_codigo_barras(dados["codigo_barras"])
        
        # Validar código interno
        if "codigo_interno" in dados:
            ok, msg = ValidadorInventario.validar_codigo_interno(dados["codigo_interno"])
            if not ok:
                resultado["válido"] = False
                resultado["erros"].append(f"Código interno: {msg}")
            resultado["dados"]["codigo_interno"] = dados["codigo_interno"].strip()
        
        # Validar nome
        if "nome" in dados:
            ok, msg = ValidadorInventario.validar_nome_produto(dados["nome"])
            if not ok:
                resultado["válido"] = False
                resultado["erros"].append(f"Nome: {msg}")
            resultado["dados"]["nome"] = ValidadorInventario.sanitizar_entrada(dados["nome"])
        
        # Validar quantidade
        if "quantidade" in dados:
            ok, msg = ValidadorInventario.validar_quantidade(dados["quantidade"])
            if not ok:
                resultado["válido"] = False
                resultado["erros"].append(f"Quantidade: {msg}")
            else:
                resultado["dados"]["quantidade"] = int(dados["quantidade"])
        
        # Validar grupo
        if "grupo" in dados:
            ok, msg = ValidadorInventario.validar_grupo(dados["grupo"])
            if not ok:
                resultado["avisos"].append(f"Grupo: {msg}")
            resultado["dados"]["grupo"] = ValidadorInventario.sanitizar_entrada(dados["grupo"])
        
        return resultado


# Funções de conveniência
def validar_codigo_barras(codigo: str) -> bool:
    """Atalho para validar código de barras"""
    ok, _ = ValidadorInventario.validar_codigo_barras(codigo)
    return ok

def validar_usuario(usuario: str) -> bool:
    """Atalho para validar usuário"""
    ok, _ = ValidadorInventario.validar_usuario(usuario)
    return ok

def validar_senha(senha: str) -> bool:
    """Atalho para validar senha"""
    ok, _ = ValidadorInventario.validar_senha(senha)
    return ok

def sanitizar(texto: str) -> str:
    """Atalho para sanitizar entrada"""
    return ValidadorInventario.sanitizar_entrada(texto)
