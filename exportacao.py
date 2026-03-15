# ===============================
# IKARUS INVENTORY - Exportação de Relatórios
# ===============================

import os
from collections import defaultdict
from typing import Optional, Tuple
import pandas as pd
from config import (
    ARQUIVO_TXT_SAIDA, ARQUIVO_XLSX_SAIDA,
    ARQUIVO_CSV_DETALHADO, ARQUIVO_CSV_NAO_MAPEADOS, log
)
from planilha import construir_dataframes


def _resolver_caminhos_saida(output_dir: Optional[str] = None) -> Tuple[str, str, str]:
    """Resolve caminhos de saida, com suporte a pasta de sessao."""
    if not output_dir:
        return ARQUIVO_XLSX_SAIDA, ARQUIVO_CSV_DETALHADO, ARQUIVO_CSV_NAO_MAPEADOS

    os.makedirs(output_dir, exist_ok=True)
    return (
        os.path.join(output_dir, os.path.basename(ARQUIVO_XLSX_SAIDA)),
        os.path.join(output_dir, os.path.basename(ARQUIVO_CSV_DETALHADO)),
        os.path.join(output_dir, os.path.basename(ARQUIVO_CSV_NAO_MAPEADOS)),
    )

# PDF opcional
try:
    from fpdf import FPDF
    PDF_OK = True
except ImportError:
    PDF_OK = False

def exportar_txt_formatado(contagem_por_cb, mapeamento: dict, arquivo: str):
    """Exporta relatório em formato TXT agregado por código interno"""
    agreg_interno = defaultdict(int)
    for cb, qtd in contagem_por_cb.items():
        if cb in mapeamento and qtd > 0:
            ci, _ = mapeamento[cb][:2]
            agreg_interno[ci] += qtd
    
    linhas = [f"{ci} | {agreg_interno[ci]}" for ci in sorted(agreg_interno.keys())]
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + ("\n" if linhas else ""))
    
    log("EXPORTAR_TXT", f"arquivo={arquivo} linhas={len(linhas)}")

def exportar_detalhado(contagem_por_cb, mapeamento: dict, output_dir: Optional[str] = None):
    """Exporta relatórios detalhados em CSV e XLSX"""
    arquivo_xlsx, arquivo_csv_detalhado, arquivo_csv_nao_mapeados = _resolver_caminhos_saida(output_dir)
    df, df_nm = construir_dataframes(contagem_por_cb, mapeamento)
    
    df.to_csv(arquivo_csv_detalhado, index=False, encoding="utf-8")
    df_nm.to_csv(arquivo_csv_nao_mapeados, index=False, encoding="utf-8")
    
    with pd.ExcelWriter(arquivo_xlsx, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Mapeados")
        df_nm.to_excel(writer, index=False, sheet_name="NaoMapeados")
    
    log("EXPORTAR_DETALHADO", f"csv={arquivo_csv_detalhado} xlsx={arquivo_xlsx}")

def exportar_pdf(contagem_por_cb, mapeamento: dict, arquivo: str = "relatorio_inventario.pdf", output_dir: Optional[str] = None):
    """Exporta relatório em formato PDF"""
    if not PDF_OK:
        raise ImportError("Biblioteca FPDF não instalada")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        arquivo = os.path.join(output_dir, os.path.basename(arquivo))
    
    df, df_nm = construir_dataframes(contagem_por_cb, mapeamento)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Inventário", ln=True, align="C")
    pdf.ln(10)
    
    for idx, row in df.iterrows():
        pdf.cell(0, 10, txt=f"{row['codigo_interno']} | {row['codigo_barras']} | {row['nome']} | {row['quantidade']}", ln=True)
    
    if not df_nm.empty:
        pdf.add_page()
        pdf.cell(200, 10, txt="Não Mapeados", ln=True, align="C")
        pdf.ln(10)
        for idx, row in df_nm.iterrows():
            pdf.cell(0, 10, txt=f"{row['codigo_barras']} | {row['quantidade']}", ln=True)
    
    pdf.output(arquivo)
    log("EXPORTAR_PDF", f"arquivo={arquivo}")
    return arquivo
