# ===============================
# IKARUS INVENTORY - Manipulação de Planilhas
# ===============================

import os
import re
from typing import Optional, Tuple, Dict
import pandas as pd
import json

from config import SINONIMOS_COLUNAS, log

def normaliza_rotulo(s: str) -> str:
    """Normaliza rótulo de coluna para comparação"""
    return re.sub(r"[\W_]+", " ", str(s).strip().lower())

def encontrar_coluna(df: pd.DataFrame, alvo: str) -> Optional[str]:
    """Encontra coluna no DataFrame por sinônimos"""
    candidatos = [alvo.lower()] + SINONIMOS_COLUNAS.get(alvo, [])
    candidatos = [normaliza_rotulo(x) for x in candidatos]
    normal_por_original = {normaliza_rotulo(col): col for col in df.columns}
    for cand in candidatos:
        if cand in normal_por_original:
            return normal_por_original[cand]
    return None

def carregar_mapeamento(caminho_excel: str, aba: Optional[str] = None):
    """
    Carrega mapeamento de produtos do Excel.
    Retorna dicionário: {codigo_barra: (codigo_interno, nome, grupo)}
    """
    if not os.path.exists(caminho_excel):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_excel}")

    try:
        df = pd.read_excel(caminho_excel, sheet_name=aba, engine="openpyxl")
    except Exception as e:
        raise Exception(f"Erro ao ler Excel: {e}")

    if isinstance(df, dict):
        df = next(iter(df.values()))

    col_cb = encontrar_coluna(df, "CodigoBarra")
    col_ci = encontrar_coluna(df, "CodigoInterno")
    col_nm = encontrar_coluna(df, "Nome")
    col_grupo = encontrar_coluna(df, "Grupo")

    if not all([col_cb, col_ci, col_nm]):
        raise Exception("Colunas necessárias não encontradas (CodigoBarra, CodigoInterno, Nome)")

    df[col_cb] = df[col_cb].astype(str).str.strip()
    df[col_ci] = df[col_ci].astype(str).str.strip()
    df[col_nm] = df[col_nm].astype(str).str.strip()
    if col_grupo:
        df[col_grupo] = df[col_grupo].astype(str).str.strip()

    mapeamento = {}
    for _, row in df.iterrows():
        cb, ci, nm = row[col_cb], row[col_ci], row[col_nm]
        grupo = row[col_grupo] if col_grupo else ""
        if cb:
            mapeamento[cb] = (ci, nm, grupo)
    
    log("CARREGAR_MAPEAMENTO", f"arquivo={caminho_excel} itens={len(mapeamento)}")

    # Tentar carregar mapeamentos personalizados gerados pela UI (arquivo JSON)
    custom_file = "mapeamento_custom.json"
    try:
        if os.path.exists(custom_file):
            with open(custom_file, "r", encoding="utf-8") as fh:
                custom = json.load(fh)
            # custom expected format: { cb: [ci, nome, grupo], ... }
            for cb_k, v in custom.items():
                try:
                    ci_k, nm_k, grupo_k = v
                    # sobrescrever/atualizar entradas (permitir correções manuais)
                    mapeamento[str(cb_k)] = (str(ci_k), str(nm_k), str(grupo_k))
                except Exception:
                    continue
            log("CARREGAR_MAPEAMENTO_CUSTOM", f"arquivo={custom_file} itens={len(custom)}")
    except Exception:
        pass

    return mapeamento


def salvar_mapeamento_custom(custom_map: Dict[str, Tuple[str, str, str]], caminho: str = "mapeamento_custom.json") -> None:
    """Persiste o mapeamento custom em JSON para carregamento posterior.

    custom_map: dicionário no formato {cb: (ci, nome, grupo), ...}
    """
    try:
        # Converter tuples para listas para serialização JSON
        serial = {str(k): [v[0], v[1], v[2] if len(v) > 2 else ""] for k, v in custom_map.items()}
        with open(caminho, "w", encoding="utf-8") as fh:
            json.dump(serial, fh, ensure_ascii=False, indent=2)
        log("SALVAR_MAPEAMENTO_CUSTOM", f"arquivo={caminho} itens={len(serial)}")
    except Exception as e:
        log("SALVAR_MAPEAMENTO_CUSTOM_ERROR", str(e))

def construir_dataframes(contagem_por_cb, mapeamento: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Constrói DataFrames com produtos mapeados e não mapeados.
    Retorna (df_mapeados, df_nao_mapeados)
    """
    rows = []
    rows_nm = []
    
    for cb, qtd in contagem_por_cb.items():
        if qtd <= 0:
            continue
        if cb in mapeamento:
            ci, nm, *_ = mapeamento[cb]
            rows.append({
                "codigo_interno": ci,
                "codigo_barras": cb,
                "nome": nm,
                "quantidade": qtd,
            })
        else:
            rows_nm.append({
                "codigo_interno": "",
                "codigo_barras": cb,
                "nome": "(NÃO MAPEADO)",
                "quantidade": qtd,
            })
    
    df = pd.DataFrame(rows)
    df_nm = pd.DataFrame(rows_nm)
    return df, df_nm
