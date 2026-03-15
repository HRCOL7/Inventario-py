# ===============================
# IKARUS INVENTORY - Tratamento de Erros
# ===============================

"""
Módulo centralizado de tratamento de erros e exceções
"""

import sys
import traceback
from typing import Optional, Callable, Any
from functools import wraps
from datetime import datetime

from config import log

class ErroInventario(Exception):
    """Classe base para exceções do inventário"""
    pass

class ErroValidacao(ErroInventario):
    """Erro de validação de dados"""
    pass

class ErroAutenticacao(ErroInventario):
    """Erro de autenticação"""
    pass

class ErroArquivo(ErroInventario):
    """Erro ao manipular arquivos"""
    pass

class ErroBancoDados(ErroInventario):
    """Erro ao acessar dados"""
    pass

class ErroExportacao(ErroInventario):
    """Erro ao exportar dados"""
    pass

class TratadorErros:
    """Gerenciador centralizado de erros"""
    
    # Registro de erros
    ERROS_REGISTRADOS = []
    MAX_ERROS_REGISTRO = 100
    
    @staticmethod
    def registrar_erro(tipo: str, mensagem: str, traceback_str: str = "", severidade: str = "erro"):
        """Registra erro para auditoria"""
        erro_info = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "mensagem": mensagem,
            "traceback": traceback_str[:500],  # Limitar tamanho
            "severidade": severidade
        }
        
        TratadorErros.ERROS_REGISTRADOS.append(erro_info)
        
        # Limitar tamanho do registro
        if len(TratadorErros.ERROS_REGISTRADOS) > TratadorErros.MAX_ERROS_REGISTRO:
            TratadorErros.ERROS_REGISTRADOS.pop(0)
        
        # Log do sistema
        log(f"ERRO_{tipo.upper()}", mensagem)
    
    @staticmethod
    def recuperar_erros(ultimos: int = 10) -> list:
        """Retorna últimos erros registrados"""
        return TratadorErros.ERROS_REGISTRADOS[-ultimos:]
    
    @staticmethod
    def limpar_erros():
        """Limpa registro de erros"""
        TratadorErros.ERROS_REGISTRADOS.clear()
    
    @staticmethod
    def formatar_erro_usuario(tipo: str, mensagem: str) -> str:
        """Formata mensagem de erro para exibir ao usuário"""
        mensagens_usuario = {
            "validacao": "❌ Dados inválidos",
            "autenticacao": "🔐 Falha na autenticação",
            "arquivo": "📁 Problema ao ler arquivo",
            "banco_dados": "💾 Erro ao acessar dados",
            "exportacao": "📤 Falha na exportação",
            "desconhecido": "⚠️ Erro inesperado"
        }
        
        titulo = mensagens_usuario.get(tipo, mensagens_usuario["desconhecido"])
        return f"{titulo}\n\n{mensagem}"

def tratar_erro(tipo_erro: str = "desconhecido", msg_padrao: str = ""):
    """
    Decorator para tratamento automático de erros
    
    Uso:
    @tratar_erro("validacao")
    def minha_funcao():
        pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except ErroInventario as e:
                tb = traceback.format_exc()
                TratadorErros.registrar_erro(tipo_erro, str(e), tb, "erro")
                raise
            except Exception as e:
                tb = traceback.format_exc()
                TratadorErros.registrar_erro(tipo_erro, str(e), tb, "crítico")
                raise ErroInventario(f"{msg_padrao or 'Erro desconhecido'}: {str(e)}") from e
        return wrapper
    return decorator

def validar_entrada(*validacoes):
    """
    Decorator para validação de argumentos
    
    Uso:
    @validar_entrada({"arg": "tipo"})
    def minha_funcao(arg):
        pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Validações básicas
            if not args and not kwargs:
                raise ErroValidacao("Argumentos obrigatórios não fornecidos")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def capturar_excecao(funcao: Callable, *args, **kwargs) -> tuple:
    """
    Executa função com captura de exceção
    
    Retorna: (sucesso: bool, resultado: Any, erro: Optional[str])
    """
    try:
        resultado = funcao(*args, **kwargs)
        return True, resultado, None
    except ErroInventario as e:
        TratadorErros.registrar_erro("validacao", str(e), traceback.format_exc())
        return False, None, str(e)
    except Exception as e:
        TratadorErros.registrar_erro("desconhecido", str(e), traceback.format_exc(), "crítico")
        return False, None, f"Erro inesperado: {str(e)}"

def garantir_tipo(argumento: Any, tipo_esperado: type, nome: str = "argumento") -> bool:
    """Verifica se argumento é do tipo esperado"""
    if not isinstance(argumento, tipo_esperado):
        raise ErroValidacao(
            f"{nome} deve ser {tipo_esperado.__name__}, recebido {type(argumento).__name__}"
        )
    return True

def garantir_nao_vazio(texto: str, nome: str = "campo") -> bool:
    """Verifica se texto não está vazio"""
    if not texto or not str(texto).strip():
        raise ErroValidacao(f"{nome} não pode estar vazio")
    return True

def garantir_tamanho(texto: str, minimo: int = 0, maximo: int = 999999, nome: str = "texto") -> bool:
    """Verifica tamanho de texto"""
    tamanho = len(str(texto).strip())
    if tamanho < minimo:
        raise ErroValidacao(f"{nome} muito curto (mínimo {minimo})")
    if tamanho > maximo:
        raise ErroValidacao(f"{nome} muito longo (máximo {maximo})")
    return True

class ContextoSeguro:
    """Context manager para operações com tratamento de erro"""
    
    def __init__(self, nome_operacao: str = "operação"):
        self.nome_operacao = nome_operacao
        self.sucesso = False
        self.erro = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.erro = str(exc_val)
            TratadorErros.registrar_erro(
                "contexto",
                f"{self.nome_operacao}: {exc_val}",
                traceback.format_exc(),
                "erro"
            )
            return False  # Propagar exceção
        else:
            self.sucesso = True
        return True

# Exemplo de uso em try/except seguro
def executar_com_seguranca(funcao: Callable, *args, on_erro: Optional[Callable] = None, **kwargs):
    """
    Executa função com tratamento de erro padronizado
    
    Uso:
    executar_com_seguranca(
        minha_funcao,
        arg1, arg2,
        on_erro=lambda e: print(f"Erro: {e}"),
        kwarg1="valor"
    )
    """
    try:
        return funcao(*args, **kwargs)
    except Exception as e:
        erro_msg = TratadorErros.formatar_erro_usuario("desconhecido", str(e))
        TratadorErros.registrar_erro("execucao", str(e), traceback.format_exc())
        
        if on_erro:
            on_erro(erro_msg)
        else:
            raise

# Utilitários de debug
class DebugInfo:
    """Informações de debug para troubleshooting"""
    
    @staticmethod
    def info_sistema() -> dict:
        """Retorna info do sistema"""
        import platform
        return {
            "python": platform.python_version(),
            "sistema": platform.system(),
            "arquitetura": platform.architecture()[0],
        }
    
    @staticmethod
    def info_ambiente() -> dict:
        """Info do ambiente de execução"""
        return {
            "arquivos_abertos": len(TratadorErros.ERROS_REGISTRADOS),
            "erros_registrados": len(TratadorErros.ERROS_REGISTRADOS),
            "timestamp": datetime.now().isoformat(),
        }
    
    @staticmethod
    def relatorio_diagnostico() -> str:
        """Gera relatório de diagnóstico"""
        info_sys = DebugInfo.info_sistema()
        info_env = DebugInfo.info_ambiente()
        
        relatorio = f"""
🔍 RELATÓRIO DE DIAGNÓSTICO
{'='*50}

📱 SISTEMA:
  Python: {info_sys['python']}
  OS: {info_sys['sistema']}
  Arquitetura: {info_sys['arquitetura']}

⚙️ AMBIENTE:
  Erros registrados: {info_env['erros_registrados']}
  Timestamp: {info_env['timestamp']}

📋 ÚLTIMOS ERROS:
"""
        for erro in TratadorErros.recuperar_erros(5):
            relatorio += f"\n  [{erro['timestamp']}] {erro['tipo']}: {erro['mensagem']}"
        
        return relatorio
