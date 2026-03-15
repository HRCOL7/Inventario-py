# ===============================
# IKARUS INVENTORY - Configurações Globais
# ===============================

import os
import logging

# === ARQUIVOS ===
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_EXCEL_PADRAO = "Produtos Box.xlsx"
ABA_EXCEL_PADRAO = None
ARQUIVO_TXT_SAIDA = "contagem.txt"
ARQUIVO_XLSX_SAIDA = "contagem.xlsx"
ARQUIVO_CSV_DETALHADO = "contagem_detalhada.csv"
ARQUIVO_CSV_NAO_MAPEADOS = "nao_mapeados.csv"
ARQUIVO_BACKUP = "contagem_backup.txt"
ARQUIVO_LOG = "contagem.log"
PASTA_NUVEM = os.getenv("IKARUS_NUVEM_DIR", "").strip()

# === CONFIGURAÇÕES ===
MOSTRAR_TOP_N_RESUMO = 10
SENHA_FINALIZAR = "733721"
INTERVALO_AUTOSAVE_MS = 120_000  # 2 minutos

# === SINÔNIMOS DE COLUNAS ===
SINONIMOS_COLUNAS = {
    "CodigoBarra": [
        "codigobarra", "codigo_barra", "cod_barra", "cod_barras", "codigo de barras",
        "codbarras", "código de barras", "barcode", "ean", "codigo_barras", "codigo barras",
        "codigo de barra"
    ],
    "CodigoInterno": [
        "codigointerno", "codigo_interno", "codinterno", "codigo", "sku", "código interno",
        "ref interna"
    ],
    "Nome": [
        "nome", "descricao", "descrição", "produto", "nome_produto", "nome produto"
    ],
}

# === LOGGING ===
def configurar_logger():
    logger = logging.getLogger("inventario")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(ARQUIVO_LOG, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger

LOGGER = configurar_logger()

def log(acao: str, detalhe: str = ""):
    try:
        LOGGER.info(f"{acao} | {detalhe}")
    except Exception:
        pass
