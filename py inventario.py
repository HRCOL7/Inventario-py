import sys
import re
import os
from collections import defaultdict, Counter

# Dependências: pandas, openpyxl
import pandas as pd

# ---------- Configurações ----------
ARQUIVO_EXCEL_PADRAO = "produtos.xlsx"     # nome padrão do Excel
ABA_EXCEL_PADRAO = None                    # None = primeira aba
ARQUIVO_TXT_SAIDA = "contagem.txt"         # exportação solicitada (interno|qtd)
ARQUIVO_CSV_DETALHADO = "contagem_detalhada.csv"  # apoio (interno, qtd, nome)
ARQUIVO_CSV_NAO_MAPEADOS = "nao_mapeados.csv"     # log de bipes sem mapeamento

MOSTRAR_TOP_N_RESUMO = 10

SINONIMOS_COLUNAS = {
    "CodigoBarra": [
        "codigobarra", "codigo_barra", "cod_barra", "cod_barras", "codigo de barras",
        "codbarras", "código de barras", "barcode", "ean", "codigo_barras", "codigo barras",
        "codigo de barra"  # <-- adicionado
    ],
    "CodigoInterno": [
        "codigointerno", "codigo_interno", "codinterno", "codigo", "sku", "código interno",
        "ref interna"  # <-- adicionado
    ],
    "Nome": [
        "nome", "descricao", "descrição", "produto", "nome_produto", "nome produto"
    ],
}

def normaliza_rotulo(s: str) -> str:
    return re.sub(r"[\W_]+", " ", str(s).strip().lower())

def encontrar_coluna(df: pd.DataFrame, alvo: str) -> str | None:
    # tenta achar a coluna alvo pelos sinônimos
    candidatos = [alvo.lower()] + SINONIMOS_COLUNAS.get(alvo, [])
    candidatos = [normaliza_rotulo(x) for x in candidatos]

    normal_por_original = {normaliza_rotulo(col): col for col in df.columns}
    for cand in candidatos:
        if cand in normal_por_original:
            return normal_por_original[cand]
    return None

def carregar_mapeamento(caminho_excel: str, aba: str | None = None):
    if not os.path.exists(caminho_excel):
        print(f"ERRO: Não encontrei o arquivo Excel '{caminho_excel}'.")
        sys.exit(1)

    print(f"Tentando ler: {caminho_excel}, aba: {aba}")  # <-- Adicione esta linha

    try:
        df = pd.read_excel(caminho_excel, sheet_name=aba, engine="openpyxl")
    except Exception as e:
        print(f"ERRO ao ler o Excel: {e}")
        sys.exit(1)

    # Se sheet_name=None, df será um dict de DataFrames
    if isinstance(df, dict):
        # Pega a primeira aba
        df = next(iter(df.values()))

    if not isinstance(df, pd.DataFrame):
        print("ERRO: O arquivo não pôde ser lido como uma tabela. Verifique se o arquivo está correto e se a aba existe.")
        sys.exit(1)

    col_cb = encontrar_coluna(df, "CodigoBarra")
    col_ci = encontrar_coluna(df, "CodigoInterno")
    col_nm = encontrar_coluna(df, "Nome")

    faltando = [lab for lab, col in [("CodigoBarra", col_cb), ("CodigoInterno", col_ci), ("Nome", col_nm)] if col is None]
    if faltando:
        print("ERRO: Não encontrei as seguintes colunas na planilha:", ", ".join(faltando))
        print("Dica: renomeie os cabeçalhos ou use sinônimos aceitos.")
        sys.exit(1)

    # Mantém como string para não perder zeros à esquerda
    df[col_cb] = df[col_cb].astype(str).str.strip()
    df[col_ci] = df[col_ci].astype(str).str.strip()
    df[col_nm] = df[col_nm].astype(str).str.strip()

    # Construir dicionário: barcode -> (interno, nome)
    mapeamento = {}
    duplicados = []

    for _, row in df.iterrows():
        cb = row[col_cb]
        ci = row[col_ci]
        nm = row[col_nm]

        if not cb or cb.lower() in ("nan", "none"):
            continue

        if cb in mapeamento:
            # se apontar para outro código interno, avisar
            if mapeamento[cb][0] != ci:
                duplicados.append((cb, mapeamento[cb][0], ci))
            # Mantém o primeiro mapeamento
        else:
            mapeamento[cb] = (ci, nm)

    if duplicados:
        print("⚠️ Aviso: Existem códigos de barras repetidos apontando para códigos internos diferentes:")
        for cb, ci_old, ci_new in duplicados[:10]:
            print(f"   - {cb}: {ci_old} (planilha anterior) vs {ci_new} (atual). Mantido o primeiro.")
        if len(duplicados) > 10:
            print(f"   (+ {len(duplicados)-10} ocorrências a mais…)")

    return mapeamento

def beep_ok():
    try:
        import winsound
        winsound.Beep(880, 70)  # tom curto
    except Exception:
        pass

def beep_erro():
    try:
        import winsound
        winsound.Beep(220, 120)
    except Exception:
        pass

def imprimir_ajuda():
    print("""
Comandos disponíveis:
  resumo                      -> mostra os TOP contados (por código interno)
  total                       -> mostra o total geral de unidades
  del <codigo_de_barras>      -> remove 1 unidade daquele código de barras
  set <codigo_de_barras> <q>  -> define a quantidade daquele código de barras
  help                        -> mostra esta ajuda
  fim                         -> finaliza e exporta os arquivos

Dica: apenas bipe um produto para somar (+1) automaticamente.
""".strip())

def main():
    # Permitir passar caminho do Excel e nome da aba por argumentos:
    caminho_excel = ARQUIVO_EXCEL_PADRAO
    aba = ABA_EXCEL_PADRAO

    # Uso: python inventario.py [arquivo.xlsx] [nome_da_aba]
    if len(sys.argv) >= 2:
        caminho_excel = sys.argv[1]
    if len(sys.argv) >= 3:
        aba = sys.argv[2]

    print("Carregando planilha de produtos…")
    mapeamento = carregar_mapeamento(caminho_excel, aba)
    print(f"✔ Mapeamento carregado ({len(mapeamento)} códigos de barras).")

    print("\n=== MODO LEITURA ===")
    print("Bipe os produtos. Digite 'help' para ver comandos. Digite 'fim' para exportar.\n")

    # Guardar contagens por código de barras (para permitir del/set por CB)
    contagem_por_cb = Counter()
    nao_mapeados = Counter()

    while True:
        try:
            entrada = input("Bipe/Comando: ").strip()
        except (EOFError, KeyboardInterrupt):
            entrada = "fim"

        if not entrada:
            continue

        # Comandos
        if entrada.lower() == "help":
            imprimir_ajuda()
            continue

        if entrada.lower() == "resumo":
            # agregação por código interno
            por_interno = defaultdict(int)
            for cb, qtd in contagem_por_cb.items():
                if cb in mapeamento:
                    ci, _ = mapeamento[cb]
                    por_interno[ci] += qtd
            # ordenar
            top = sorted(por_interno.items(), key=lambda x: x[1], reverse=True)[:MOSTRAR_TOP_N_RESUMO]
            print("TOP itens (por Código Interno):")
            if not top:
                print("  (vazio)")
            for ci, qtd in top:
                # pegar um nome representativo (primeiro que aparecer)
                nomes = [mapeamento[cb][1] for cb, q in contagem_por_cb.items()
                         if cb in mapeamento and mapeamento[cb][0] == ci and q > 0]
                nome = nomes[0] if nomes else ""
                print(f"  {ci:>15}  | {qtd:>6}  {(' - ' + nome) if nome else ''}")
            continue

        if entrada.lower() == "total":
            total_geral = sum(contagem_por_cb.values())
            print(f"Total de unidades contadas: {total_geral}")
            continue

        if entrada.lower().startswith("del "):
            cb = entrada[4:].strip()
            if cb in contagem_por_cb and contagem_por_cb[cb] > 0:
                contagem_por_cb[cb] -= 1
                print(f"−1 em {cb}. Agora: {contagem_por_cb[cb]}")
                beep_ok()
            else:
                print(f"Nada para remover em {cb}.")
                beep_erro()
            continue

        if entrada.lower().startswith("set "):
            partes = entrada.split()
            if len(partes) != 3:
                print("Uso: set <codigo_de_barras> <quantidade>")
                continue
            cb, qtd_txt = partes[1], partes[2]
            try:
                qtd = int(qtd_txt)
                if qtd < 0:
                    raise ValueError()
            except ValueError:
                print("Quantidade inválida. Use um inteiro >= 0.")
                continue
            contagem_por_cb[cb] = qtd
            if cb not in mapeamento:
                nao_mapeados[cb] += 0  # só para registrar que apareceu
                print(f"(Atenção) {cb} não está mapeado na planilha.")
                beep_erro()
            else:
                ci, nm = mapeamento[cb]
                print(f"Definido: {nm} ({ci}) = {qtd}")
                beep_ok()
            continue

        if entrada.lower() == "fim":
            break

        # Caso contrário, tratamos como CÓDIGO DE BARRAS escaneado
        codigo_barras = entrada
        if codigo_barras in mapeamento:
            contagem_por_cb[codigo_barras] += 1
            ci, nm = mapeamento[codigo_barras]
            print(f"+1  {nm}  ({ci})  -> total desse CB: {contagem_por_cb[codigo_barras]}")
            beep_ok()
        else:
            nao_mapeados[codigo_barras] += 1
            print(f"⚠️ Não mapeado: {codigo_barras} (adicione na planilha).")
            beep_erro()

    # ---------- Exportação ----------
    print("\nExportando…")
    # Agregar por CÓDIGO INTERNO
    agreg_interno = defaultdict(int)
    nome_por_interno = {}

    for cb, qtd in contagem_por_cb.items():
        if cb in mapeamento and qtd > 0:
            ci, nm = mapeamento[cb]
            agreg_interno[ci] += qtd
            # guardar um nome representativo
            if ci not in nome_por_interno:
                nome_por_interno[ci] = nm

    # Gerar TXT: CODIGO_INTERNO|QUANTIDADE
    linhas_txt = []
    for ci in sorted(agreg_interno.keys()):
        linhas_txt.append(f"{ci}|{agreg_interno[ci]}")
    with open(ARQUIVO_TXT_SAIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_txt) + ("\n" if linhas_txt else ""))

    # CSV detalhado para conferência
    df_detalhe = pd.DataFrame(
        [{"CodigoInterno": ci, "Quantidade": qtd, "Nome": nome_por_interno.get(ci, "")}
         for ci, qtd in sorted(agreg_interno.items())]
    )
    df_detalhe.to_csv(ARQUIVO_CSV_DETALHADO, index=False, encoding="utf-8")

    # Não mapeados (se houver)
    if nao_mapeados:
        df_nao = pd.DataFrame(
            [{"CodigoBarra": cb, "Quantidade": qtd} for cb, qtd in sorted(nao_mapeados.items())]
        )
        df_nao.to_csv(ARQUIVO_CSV_NAO_MAPEADOS, index=False, encoding="utf-8")

    print(f"✔ Gerado: {ARQUIVO_TXT_SAIDA}")
    print(f"✔ Gerado: {ARQUIVO_CSV_DETALHADO}")
    if nao_mapeados:
        print(f"✔ Gerado: {ARQUIVO_CSV_NAO_MAPEADOS} (corrija sua planilha e recontabilize se necessário)")
    print("Concluído.")
    

if __name__ == "__main__":
    main()

